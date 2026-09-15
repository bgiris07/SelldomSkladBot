import os
import logging
import datetime
from pathlib import Path
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
import asyncio

# ==== НАСТРОЙКИ ====
import os
BOT_TOKEN = os.getenv("BOT_TOKEN")
HTML_FILE_PATH = Path(r"C:\dashboard\dashboard.html")
# ===================

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я отдаю HTML-дашборд с сервера 1С.\n\n"
        "Команды:\n"
        "/get — получить файл\n"
        "/status — информация о файле"
    )


@dp.message(Command("get"))
async def cmd_get(message: types.Message):
    if not HTML_FILE_PATH.exists():
        await message.answer(
            f"Файл не найден:\n{HTML_FILE_PATH}\n\n"
            "Проверь, что 1С выгрузила дашборд."
        )
        return

    try:
        stat = HTML_FILE_PATH.stat()
        mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M")

        document = FSInputFile(HTML_FILE_PATH, filename="dashboard.html")
        await message.answer_document(
            document,
            caption=f"Дашборд от {mtime}"
        )
    except Exception as e:
        logging.exception("Ошибка отправки")
        await message.answer(f"Ошибка: {e}")


@dp.message(Command("status"))
async def cmd_status(message: types.Message):
    if not HTML_FILE_PATH.exists():
        await message.answer("Файл ещё не создан.")
        return

    stat = HTML_FILE_PATH.stat()
    mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M:%S")
    size_kb = stat.st_size / 1024

    await message.answer(
        f"Файл: dashboard.html\n"
        f"Размер: {size_kb:.1f} КБ\n"
        f"Обновлён: {mtime}"
    )


async def main():
    print("Бот запущен.")
    print(f"Путь к файлу: {HTML_FILE_PATH}")
    print(f"Файл существует: {HTML_FILE_PATH.exists()}")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())