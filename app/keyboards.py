from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Главное меню
main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Запустить бомбер 💣', callback_data='startbomb')]
])

get_id = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='💠 Получить chat id', callback_data='chat_id')]
])

# Выбор типа атаки
attack_type = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='📩 SMS', callback_data='SMS')],
    [InlineKeyboardButton(text='📞 CALL', callback_data='CALL')],
    [InlineKeyboardButton(text='💫 MIX', callback_data='MIX')],
    [InlineKeyboardButton(text='💬 Feedback', callback_data='FEEDBACK')]
])

# Кнопки для старта и остановки
start_stop_bomber = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🚀 Начать атаку', callback_data='start_attack')],
    [InlineKeyboardButton(text='❌ Отмена', callback_data='stop_attack')],
])

stop_bomber = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🛑 Остановить атаку', callback_data='stop_attack')],
])
