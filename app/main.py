import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from bot.handlers import router
from config import BOT_TOKEN
from database.models import init_db
from services.elastic_service import es_client, find_or_create_index
from utils.logger import logger


async def main():
    logger.info("Starting the bot")
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    await init_db()
    await find_or_create_index()

    for _ in range(30):  # Пробуем в течение 30 секунд
        try:
            await es_client.info()
            print("Elasticsearch is ready")
            break
        except Exception:
            await asyncio.sleep(1)
    else:
        print("Elasticsearch is not available")
        return

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
