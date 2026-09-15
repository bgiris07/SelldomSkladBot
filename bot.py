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

KLADOVSHCHIKI_PATH = os.getenv("KLADOVSHCHIKI_PATH", "/kladovshchiki.html")
SBORSHCHIKI_PATH = os.getenv("SBORSHCHIKI_PATH", "/sborshchiki.html")
# ===================

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def get_download_link(token, disk_path):
    url = "https://cloud-api.yandex.net/v1/disk/resources/download"
    headers = {"Authorization": f"OAuth {token}"}
    params = {"path": disk_path}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get("href")
    else:
        raise Exception(f"API Диска вернул {response.status_code}: {response.text}")


def clean_html(html: str) -> str:
    html = re.sub(r"<!DOCTYPE[^>]*>", "", html, flags=re.IGNORECASE)
    html = re.sub(r"<head[^>]*>.*?</head>", "", html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r"</?html[^>]*>", "", html, flags=re.IGNORECASE)
    html = re.sub(r"</?body[^>]*>", "", html, flags=re.IGNORECASE)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r"\n\s*\n", "\n", html)
    return html.strip()


async def send_html_as_rich(message: types.Message, disk_path: str):
    download_url = get_download_link(YANDEX_TOKEN, disk_path)
    file_response = requests.get(download_url, timeout=30)
    file_response.raise_for_status()
    file_response.encoding = "utf-8"
    html_content = file_response.text
    cleaned = clean_html(html_content)
    await message.answer_rich(
        rich_message=InputRichMessage(html=cleaned),
    )


def get_main_keyboard():
    """Главное меню: Кладовщики, Сборщики, Обновить."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 Кладовщики"), KeyboardButton(text="🛒 Сборщики")],
            [KeyboardButton(text="🔄 Обновить")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите раздел..."
    )
    return keyboard


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Выберите раздел:",
        reply_markup=get_main_keyboard()
    )


@dp.message(F.text == "📦 Кладовщики")
async def btn_kladovshchiki(message: types.Message):
    await message.answer("Загружаю статистику кладовщиков...")
    try:
        await send_html_as_rich(message, KLADOVSHCHIKI_PATH)
    except Exception as e:
        logging.exception("Ошибка")
        await message.answer(f"Ошибка: {e}")


@dp.message(F.text == "🛒 Сборщики")
async def btn_sborshchiki(message: types.Message):
    await message.answer("Загружаю статистику сборщиков...")
    try:
        await send_html_as_rich(message, SBORSHCHIKI_PATH)
    except Exception as e:
        logging.exception("Ошибка")
        await message.answer(f"Ошибка: {e}")


@dp.message(F.text == "🔄 Обновить")
async def btn_refresh(message: types.Message):
    """Принудительно перерисовывает клавиатуру у пользователя."""
    await message.answer(
        "Клавиатура обновлена ✅",
        reply_markup=get_main_keyboard()
    )


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())