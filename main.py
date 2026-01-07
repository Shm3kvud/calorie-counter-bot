import asyncio
import logging
from aiogram import Bot, Dispatcher
from app.configs.config import BOT_TOKEN
from app.handlers import handlers
from app.database.sqlite_db import db
# from app.middlewares import TextCheckMiddleware


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


async def main():
    await db.init_db()
    # dp.message.middleware(TextCheckMiddleware())
    dp.include_router(router=handlers.router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.INFO)
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit Bot")
