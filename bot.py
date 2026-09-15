import os
import re
import logging
import requests
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    InputRichMessage,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
import asyncio

# ==== НАСТРОЙКИ ====
BOT_TOKEN = os.getenv("BOT_TOKEN")
YANDEX_TOKEN = os.getenv("YANDEX_DISK_TOKEN")

MAIN_DASHBOARD_PATH = os.getenv("FILE_PATH_ON_DISK", "/dashboard.html")
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


def clean_html(html: str) -> str:
    """
    Убирает служебные теги, оставляя только содержимое <body>.
    Telegram понимает не всё — поэтому чистим.
    """
    # 1. Убираем DOCTYPE
    html = re.sub(r"<!DOCTYPE[^>]*>", "", html, flags=re.IGNORECASE)
    
    # 2. Убираем блок <head>...</head> целиком
    html = re.sub(r"<head[^>]*>.*?</head>", "", html, flags=re.IGNORECASE | re.DOTALL)
    
    # 3. Убираем теги <html>, </html>, <body>, </body>
    html = re.sub(r"</?html[^>]*>", "", html, flags=re.IGNORECASE)
    html = re.sub(r"</?body[^>]*>", "", html, flags=re.IGNORECASE)
    
    # 4. Убираем <style>...</style> и <script>...</script> (Telegram их всё равно не понимает)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.IGNORECASE | re.DOTALL)
    
    # 5. Убираем лишние пустые строки
    html = re.sub(r"\n\s*\n", "\n", html)
    
    return html.strip()


async def send_html_as_rich(message: types.Message, disk_path: str):
    """Скачивает HTML, чистит и отправляет как Rich Message."""
    download_url = get_download_link(YANDEX_TOKEN, disk_path)
    file_response = requests.get(download_url, timeout=30)
    file_response.raise_for_status()
    
    file_response.encoding = "utf-8"
    html_content = file_response.text
    
    # Чистим HTML от служебных тегов
    cleaned = clean_html(html_content)
    
    await message.answer_rich(
        rich_message=InputRichMessage(html=cleaned),
    )


def get_main_keyboard():
    """Главное меню: одна кнопка Дашборд."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Дашборд")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Нажмите кнопку..."
    )
    return keyboard


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Нажмите кнопку ниже, чтобы получить дашборд:",
        reply_markup=get_main_keyboard()
    )


@dp.message(F.text == "📊 Дашборд")
async def btn_dashboard(message: types.Message):
    await message.answer("Загружаю дашборд...")
    try:
        await send_html_as_rich(message, MAIN_DASHBOARD_PATH)
    except Exception as e:
        logging.exception("Ошибка")
        await message.answer(f"Ошибка: {e}")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())