from aiogram import F, Router
from aiogram.enums import ChatAction, ParseMode
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from database.models import save_dialog, save_feedback
from services.llm_service import process_query

from .keyboards import get_disabled_feedback_keyboard, get_feedback_keyboard

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
        dialog_id = await save_dialog(
            user_id, query, answer, input_tokens, output_tokens
        )

        # Send the final answer with the feedback keyboard
        await message.answer(
            answer,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_feedback_keyboard(dialog_id),
        )

    except Exception as e:
        # Log the error (you might want to use a proper logging system)
        print(f"Error processing query: {str(e)}")

        # Inform the user about the error
        error_message = "I'm sorry, but an error occurred while processing your query. Please try again later."
        await message.answer(error_message, parse_mode=ParseMode.MARKDOWN)


@router.callback_query(F.data.startswith("feedback:"))
async def handle_feedback(callback_query: CallbackQuery):
    _, dialog_id, feedback = callback_query.data.split(":")
    is_positive = feedback == "positive"

    try:
        await save_feedback(int(dialog_id), is_positive)
        response = (
            "👍 Thank you for your positive feedback!"
            if is_positive
            else "👎 Thank you for your feedback. We'll try to improve!"
        )

        # Update the message with disabled keyboard
        await callback_query.message.edit_reply_markup(
            reply_markup=get_disabled_feedback_keyboard(feedback)
        )

        await callback_query.answer(response)
    except Exception as e:
        print(f"Error saving feedback: {str(e)}")
        await callback_query.answer(
            "Sorry, there was an error processing your feedback."
        )


@router.callback_query(F.data == "disabled")
async def handle_disabled_feedback(callback_query: CallbackQuery):
    await callback_query.answer("You've already provided feedback for this response.")
