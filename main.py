# main.py

import asyncio
import sys
from telegram.ext import ApplicationBuilder
from loggers import setup_user_not_friendly_logger, log_user_friendly
from db import init_db
from handlers import register_handlers
from WEEEK import initialize_weeek_data


def read_token():
    with open("token.txt", "r", encoding="utf-8") as f:
        return f.read().strip()


async def main():
    log_user_friendly("🚀 Запуск бота...")
    init_db()
    setup_user_not_friendly_logger()

    try:
        await initialize_weeek_data()
        log_user_friendly("✅ WEEEK данные успешно инициализированы")
    except Exception as e:
        log_user_friendly(f"⚠️ Ошибка инициализации WEEEK: {e}")

    token = read_token()
    application = ApplicationBuilder().token(token).build()
    register_handlers(application)

    log_user_friendly("🤖 Бот запущен и готов к работе.")

    try:
        await application.initialize()
        await application.start()
        await application.updater.start_polling()

        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        log_user_friendly("🛑 Получен сигнал остановки...")
    finally:
        log_user_friendly("⏳ Останавливаем бота...")
        try:
            if application.updater.running:
                await application.updater.stop()
            await application.stop()
            await application.shutdown()
        except Exception as e:
            log_user_friendly(f"⚠️ Ошибка при остановке: {e}")
        log_user_friendly("🛑 Бот успешно остановлен")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
        log_user_friendly("🔌 Event loop закрыт")
