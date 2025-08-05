# utils.py

import os
from datetime import datetime
from pathconf import BASE_PATH

_d_id = 0

def get_d_id():
    global _d_id
    return _d_id

def increase_d_id():
    global _d_id
    _d_id += 1

def reset_d_id():
    global _d_id
    _d_id = 0

def save_text_file(task_id: int, text: str, base_path = BASE_PATH if 'BASE_PATH' in globals() else 'data'):
    folder = os.path.join(base_path, datetime.now().strftime("%Y-%m-%d"), str(task_id))
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"{task_id}_text.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path

def read_token():
    with open("token.txt", "r", encoding="utf-8") as f:
        return f.read().strip()

def save_rename_log(task_id: int, log_text: str, base_path = BASE_PATH if 'BASE_PATH' in globals() else 'data'):
    folder = os.path.join(base_path, datetime.now().strftime("%Y-%m-%d"), str(task_id))
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, "rename.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(log_text)
    return path

def delete_task_files(task_id: int, base_path = BASE_PATH if 'BASE_PATH' in globals() else 'data'):
    folder = os.path.join(base_path, datetime.now().strftime("%Y-%m-%d"), str(task_id))
    if os.path.exists(folder):
        for root, dirs, files in os.walk(folder, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for d in dirs:
                os.rmdir(os.path.join(root, d))
        os.rmdir(folder)


# utils.py

# utils.py

def build_task_card(task_id: int, user_name: str, created_at: str, full_text: str, files_list: list):
    # Формируем название задачи (без переносов строк)
    task_lines = []
    for line in full_text.split('\n'):
        if not line.startswith('data\\') and line.strip() and not any(f in line for f in files_list):
            task_lines.append(line.strip())
    cleaned_title_text = " ".join(task_lines)

    if not cleaned_title_text and files_list:
        cleaned_title_text = "Информация в файле"

    title = f"{task_id}. {cleaned_title_text}"[:50]

    # Формируем текст задачи с сохранением переносов и разделением файлов
    task_text_parts = []
    current_text = []

    for line in full_text.split('\n'):
        if line.startswith('data\\') or any(f in line for f in [f.split(' -> ')[0] for f in files_list]):
            if current_text:
                task_text_parts.append("\n".join(current_text))
                current_text = []
            task_text_parts.append(line)
        elif line.strip():
            current_text.append(line)

    if current_text:
        task_text_parts.append("\n".join(current_text))

    task_text = "\n\n".join(task_text_parts)

    # Формируем текст карточки
    text = (
            f"📝 Добавил: {user_name}\n"
            f"📅 Дата создания: {created_at}\n"
            f"📌 Название задачи: {title}\n\n"
            f"📃 Текст задачи:\n{task_text if task_text else 'Текст отсутствует'}\n\n"
            f"📎 Файлы:\n" + "\n".join(
                f"✅ {f.split(' -> ')[0]}" if ' -> ' in f else
                f"❌ {f.replace('[Файл не скачан из-за недопустимого расширения]', '')} (не скачан)"
                for f in files_list
            )
    )
    return text, title