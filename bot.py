import os
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

# Основной дашборд (для кнопки "Дашборд")
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


async def send_html_as_rich(message: types.Message, disk_path: str):
    """Скачивает HTML и отправляет как Rich Message."""
    download_url = get_download_link(YANDEX_TOKEN, disk_path)
    file_response = requests.get(download_url, timeout=30)
    file_response.raise_for_status()
    
    # Принудительно UTF-8, чтобы русские буквы не превращались в кракозябры
    file_response.encoding = "utf-8"
    html_content = file_response.text
    
    await message.answer_rich(
        rich_message=InputRichMessage(html=html_content),
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


# Кнопка "Дашборд" — общий дашборд
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