from aiogram import F, Router
from aiogram.enums import ChatAction, ParseMode
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

    try:
        await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)

        answer, input_tokens, output_tokens = await process_query(query)
        await save_dialog(user_id, query, answer, input_tokens, output_tokens)

        # Send the final answer
        await message.answer(answer, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        # Log the error (you might want to use a proper logging system)
        print(f"Error processing query: {str(e)}")

        # Inform the user about the error
        error_message = "I'm sorry, but an error occurred while processing your query. Please try again later."
        await message.answer(error_message, parse_mode=ParseMode.MARKDOWN)
