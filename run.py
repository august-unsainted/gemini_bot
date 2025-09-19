import asyncio
from aiogram import Bot, Dispatcher

from config import TOKEN
from ai import router

bot = Bot(token=TOKEN)
dp = Dispatcher()


async def main():
    dp.include_routers(router)
    await dp.start_polling(bot, skip_updates=True)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот выключен')
