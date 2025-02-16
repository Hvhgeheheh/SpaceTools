#### Основные импорты ####

import asyncio
import json
import os

from aiogram import Bot, Dispatcher
from app.handlers import router
from datetime import datetime

from config import token

# 📂 Путь к файлу с пользователями
USERS_FILE = "users.json"

# Функции загрузки и сохранения JSON с ID чатов
def load_users_pend():
    """Загружает пользователей и ID чатов, предотвращая ошибки с пустым или поврежденным файлом."""
    if not os.path.exists(USERS_FILE) or os.stat(USERS_FILE).st_size == 0:
        return {
            "allowed_users": [],
            "pending_users": {},
            "admin_chat_id": -1002364159616,  # Значение по умолчанию
            "output_chat_id": -4648248130     # Значение по умолчанию
        }
    
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

            # Если admin_chat_id или output_chat_id отсутствуют, добавляем их со значениями по умолчанию
            data.setdefault("admin_chat_id", -1002364159616)
            data.setdefault("output_chat_id", -4648248130)

            return data
    except json.JSONDecodeError:
        return {
            "allowed_users": [],
            "pending_users": {},
            "admin_chat_id": -1002364159616,
            "output_chat_id": -4648248130
        }

def save_users_pend(users):
    """Сохраняет пользователей и ID чатов в файл."""
    with open(USERS_FILE, "w", encoding="utf-8") as file:
        json.dump(users, file, indent=4, ensure_ascii=False)


# Загружаем настройки
settings = load_users_pend()

# Теперь ID чатов берутся из файла, а не устанавливаются жестко
ADMIN_CHAT_ID = settings["admin_chat_id"]
OUTPUT_CHAT_ID = settings["output_chat_id"]

#### Основной функционал ####

bot = Bot(token=token)
dp = Dispatcher()

# Функции оповещения запуска и выключения бота
async def send_start_message():
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"🟢 Бот запущен!\n⏳ Время: <code>{start_time}</code>"
    await bot.send_message(OUTPUT_CHAT_ID, message, parse_mode="HTML")

async def send_stop_message():
    stop_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"🔴 Бот выключен!\n⏳ Время: <code>{stop_time}</code>"
    await bot.send_message(OUTPUT_CHAT_ID, message, parse_mode="HTML")

async def main():
    dp.include_router(router)
    print('Bot has been started ✅')
    await send_start_message()
    
    try:
        await dp.start_polling(bot)
    finally:
        await send_stop_message()
        await bot.session.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('⛔ Exited')
