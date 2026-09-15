import os
import logging
import datetime
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InputRichMessage
import asyncio

# ==== НАСТРОЙКИ ====
BOT_TOKEN = os.getenv("BOT_TOKEN")
YANDEX_TOKEN = os.getenv("YANDEX_DISK_TOKEN")
FILE_PATH_ON_DISK = os.getenv("FILE_PATH_ON_DISK", "/dashboard.html")
# ===================

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def get_download_link(token, disk_path):
    """Запрашивает у API Яндекс.Диска временную прямую ссылку на файл."""
    url = "https://cloud-api.yandex.net/v1/disk/resources/download"
    headers = {"Authorization": f"OAuth {token}"}
    params = {"path": disk_path}
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get("href")
    else:
        raise Exception(f"API Диска вернул {response.status_code}: {response.text}")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! /get — показать дашборд.")

@dp.message(Command("get"))
async def cmd_get(message: types.Message):
    await message.answer("Загружаю дашборд...")
    try:
        # 1. Получаем прямую ссылку через API
        download_url = get_download_link(YANDEX_TOKEN, FILE_PATH_ON_DISK)
        
        # 2. Скачиваем HTML-код файла
        file_response = requests.get(download_url, timeout=30)
        file_response.raise_for_status()

        # 3. Явно указываем кодировку UTF-8 при декодировании
        file_response.encoding = "utf-8"
        html_content = file_response.text
        
        # 4. Отправляем как Rich Message (Telegram сам отрисует таблицу)
        await message.answer_rich(
            rich_message=InputRichMessage(html=html_content),
        )
        
    except Exception as e:
        logging.exception("Ошибка")
        await message.answer(f"Ошибка: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())