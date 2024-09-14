from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from services.llm_service import process_query
from database.models import save_dialog

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Hello! I'm a bot that can help answer questions about New Zealand visas. What would you like to know?"
    )


@router.message(F.text)
async def handle_message(message: Message):
    user_id = message.from_user.id
    query = message.text

    # answer = await process_query(query)
    # await save_dialog(user_id, query, answer)

    answer = "This is a temporary answer. Bot is under development."

    await message.answer(answer)
