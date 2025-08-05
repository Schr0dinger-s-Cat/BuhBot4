# handlers.py
import sys

from WEEEK import create_weeek_task
from telegram import (
    Update, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from telegram.ext import (
    CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from datetime import datetime
import os
import json
from pathconf import BASE_PATH
from db import create_task, update_task, get_task_column, mark_task_deleted
from loggers import log_user_friendly
from utils import (
    get_d_id, increase_d_id, reset_d_id,
    save_text_file, save_rename_log, delete_task_files,
    build_task_card
)

from pathlib import Path
import ast  # Для безопасного чтения Python-выражений




def load_allowed_extensions():
    try:
        with open("extensions.txt", "r", encoding="utf-8") as f:
            extensions = [line.strip().lower() for line in f if line.strip()]
            return extensions
    except FileNotFoundError:
        # Если файла нет - разрешаем все расширения (или можно вернуть пустой список для запрета всех)
        return None

ALLOWED_EXTENSIONS = load_allowed_extensions()

def register_handlers(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO | filters.Document.ALL, collect_data))
    application.add_handler(CallbackQueryHandler(button_handler))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    task_id = create_task()
    context.user_data['db_task_id'] = task_id
    context.user_data['messages'] = []
    context.user_data['files'] = []
    reset_d_id()

    keyboard = ReplyKeyboardMarkup([
        [KeyboardButton("Создать задачу"), KeyboardButton("Отмена")]
    ], resize_keyboard=True)

    await update.message.reply_text(
        "📌 Для создания задачи отправляйте текст, фото, файлы.\n"
        "Когда всё будет готово — нажмите 'Создать задачу'.\n\n"
        "Кнопка 'Отмена' сбрасывает ввод, удаляя файлы, но сохраняя факт задачи в системе.",
        reply_markup=keyboard
    )

    log_user_friendly(f"👤 Пользователь {user.full_name} начал создание задачи {task_id}")


# handlers.py

# Модифицируем функцию collect_data
async def collect_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    task_id = context.user_data.get('db_task_id')
    if not task_id:
        await update.message.reply_text("❗ Пожалуйста, начните с команды /start")
        return

    if update.message.text in ["Создать задачу", "Отмена"]:
        if update.message.text == "Создать задачу":
            await publish_task(update, context)
        else:
            await cancel_task(update, context)
        return

    rename_log = context.user_data.get('rename_log', "")
    file_entries = context.user_data.get('files', [])
    file_texts = []

    msg_text = update.message.text or update.message.caption or ""
    has_text = bool(msg_text.strip())
    has_file = False

    # Обработка документов
    if update.message.document:
        doc = update.message.document
        file_ext = os.path.splitext(doc.file_name)[1].lower()

        # Проверяем расширение, если список расширений задан
        if ALLOWED_EXTENSIONS is not None and file_ext not in ALLOWED_EXTENSIONS:
            file_texts.append(f"{doc.file_name} [Файл не скачан из-за недопустимого расширения]")
            log_user_friendly(f"⚠️ Файл {doc.file_name} отклонён из-за недопустимого расширения")
        else:
            file = await doc.get_file()
            did = get_d_id()
            filename = f"{task_id}_{did}{os.path.splitext(doc.file_name)[1]}"
            folder = os.path.join(BASE_PATH, datetime.now().strftime("%Y-%m-%d"), str(task_id))
            os.makedirs(folder, exist_ok=True)
            path = os.path.join(folder, filename)
            await file.download_to_drive(path)
            rename_log += f"{doc.file_name} -> {filename}\n"
            file_entries.append(f"{doc.file_name} -> {path}")
            file_texts.append(doc.file_name)
            has_file = True
            increase_d_id()

    # Обработка фото (оставляем без изменений, так как фото всегда допустимы)
    elif update.message.photo:
        photo = update.message.photo[-1]
        file = await photo.get_file()
        did = get_d_id()
        filename = f"{task_id}_{did}.jpg"
        folder = os.path.join(BASE_PATH, datetime.now().strftime("%Y-%m-%d"), str(task_id))
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, filename)
        await file.download_to_drive(path)
        rename_log += f"photo_{photo.file_unique_id}.jpg -> {filename}\n"
        file_entries.append(f"photo -> {path}")
        file_texts.append("photo.jpg")
        has_file = True
        increase_d_id()

    # Остальной код функции оставляем без изменений
    if has_text or has_file:
        entry = msg_text.strip()
        if file_texts:
            entry += "\n" + "\n".join(file_texts) if entry else "\n".join(file_texts)
        context.user_data.setdefault('messages', []).append(entry)

    context.user_data['rename_log'] = rename_log
    context.user_data['files'] = file_entries

    log_user_friendly(f"📨 Принято сообщение от {user.full_name}. Текст: {msg_text or '[нет текста]'}")

# handlers.py (изменяем функцию publish_task)

async def publish_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task_id = context.user_data.get('db_task_id')
    if not task_id:
        await update.message.reply_text("❗ Не удалось найти задачу.")
        return

    user = update.effective_user
    user_id = user.id
    user_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    full_text = "\n".join(context.user_data.get('messages', [])) or "[текст не указан]"
    files = context.user_data.get('files', [])
    rename_log = context.user_data.get('rename_log', "Файлы не прикреплялись")

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    files_json = json.dumps({
        "file_count": len(files),
        "doc_ids": [],
        "photo_ids": [],
        "rename_log": rename_log
    }, ensure_ascii=False, indent=2)

    # Сохраняем в базу
    update_task(task_id, "user_id", user_id)
    update_task(task_id, "user_name", user_name)
    update_task(task_id, "created_at", created_at)
    update_task(task_id, "full_text", full_text)
    update_task(task_id, "files_json", files_json)
    update_task(task_id, "sost", "sucsessefully_publeshed")

    # Сохраняем текст и лог
    text_file_path = save_text_file(task_id, full_text)
    save_rename_log(task_id, rename_log)

    # Формируем данные для карточки задачи
    task_card, task_title = build_task_card(
        task_id, f"<a href='tg://user?id={user_id}'>{user_name}</a>", created_at, full_text, files
    )

    # Формируем данные для WEEEK
    # Формируем описание задачи с сохранением структуры
    task_text_parts = []
    current_text = []

    for line in full_text.split('\n'):
        if line.startswith('data\\') or any(f in line for f in files):
            if current_text:
                task_text_parts.append("\n".join(current_text))
                current_text = []
            task_text_parts.append(line)
        elif line.strip():
            current_text.append(line)

    if current_text:
        task_text_parts.append("\n".join(current_text))

    weeek_description = "\n\n".join(task_text_parts)

    # Создаем задачу в WEEEK
    try:
        weeek_task_id = await create_weeek_task(
            title=task_title,
            description=weeek_description,
            files_info=rename_log
        )

        # Сохраняем ID задачи из WEEEK в нашу базу
        update_task(task_id, "weeek_task_id", str(weeek_task_id))
        log_user_friendly(f"✅ Задача {task_id} создана в WEEEK с ID {weeek_task_id}")
    except Exception as e:
        log_user_friendly(f"⚠️ Ошибка при создании задачи в WEEEK: {str(e)}")
        await update.message.reply_text(f"⚠️ Задача создана, но не отправлена в WEEEK: {str(e)}")

    # Отправляем пользователю
    await update.message.reply_text(f"✅ Задача создана:\n\n{task_card}", parse_mode="HTML")

    # Отправляем в админ-чат
    try:
        with open("Admin_chat.txt", "r", encoding="utf-8") as f:
            admin_chat_id = int(f.read().strip())
        await context.bot.send_message(admin_chat_id, f"📥 Новая задача:\n\n{task_card}", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Не удалось отправить задачу администратору: {e}")

    log_user_friendly(f"📦 Задача {task_id} опубликована.")

    # Сброс и переход к новой задаче
    await start(update, context)


async def cancel_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task_id = context.user_data.get('db_task_id')
    mark_task_deleted(task_id)
    delete_task_files(task_id)
    await update.message.reply_text("🚫 Задача отменена. Ввод сброшен.")
    log_user_friendly(f"🗑 Задача {task_id} отменена и очищены файлы.")

    # Сброс и переход к новой задаче
    await start(update, context)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()

