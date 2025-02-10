#### Основные импорты ####

import asyncio

from aiogram import Bot, Dispatcher
from app.handlers import router

from config import token

#### Основной функционал ####

bot = Bot(token=token)
dp = Dispatcher()



async def main():
    dp.include_router(router)
    print('Bot has been started')
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exited')
