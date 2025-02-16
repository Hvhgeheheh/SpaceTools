from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
# 💠 Главное меню
# 💠 Главное меню
main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Запустить бомбер 💣', callback_data='startbomb')],
    [InlineKeyboardButton(text='Контакты ☎', callback_data='get_contacts')],
])

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

# 🚀 Выбор типа атаки
attack_type = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='📩 SMS', callback_data='SMS')],
    [InlineKeyboardButton(text='📞 CALL', callback_data='CALL')],
    [InlineKeyboardButton(text='💫 MIX', callback_data='MIX')],
    [InlineKeyboardButton(text='💬 Feedback (RU only)', callback_data='FEEDBACK')]
])

# 🌌 Кнопки для старта
start_stop_bomber = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🚀 Начать атаку', callback_data='start_attack')],
    [InlineKeyboardButton(text='❌ Отмена', callback_data='stop_attack')],
])

# 🌀 Кнопки остановки
stop_bomber = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🛑 Остановить атаку', callback_data='stop_attack')],
])

# 🔮 Кнопки для статуса бота
statusbut = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Бот работает корректно", callback_data="status_green")],
        [InlineKeyboardButton(text="🟡 Ведутся технические работы", callback_data="status_yellow")],
        [InlineKeyboardButton(text="🔴 Бот оффлайн", callback_data="status_red")],
    ])