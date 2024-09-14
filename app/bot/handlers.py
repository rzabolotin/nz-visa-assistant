from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message
from database.models import save_dialog
from services.llm_service import process_query

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Hello! I'm a bot that can help answer questions about New Zealand visas. What would you like to know?",
        parse_mode=ParseMode.MARKDOWN,
    )


@router.message(F.text)
async def handle_message(message: Message):
    user_id = message.from_user.id
    query = message.text

    answer = await process_query(query)
    # await save_dialog(user_id, query, answer)

    await message.answer(answer, parse_mode=ParseMode.MARKDOWN)
