from aiogram import F, Router
from aiogram.enums import ChatAction, ParseMode
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from database.models import save_dialog, save_feedback
from services.llm_service import process_query
from utils.logger import logger

from .keyboards import get_disabled_feedback_keyboard, get_feedback_keyboard

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    logger.info(f"User {message.from_user.id} started the bot")
    await message.answer(
        "Hello! I'm a bot that can help answer questions about New Zealand visas. What would you like to know?",
        parse_mode=ParseMode.MARKDOWN,
    )


@router.message(F.text)
async def handle_message(message: Message):
    user_id = message.from_user.id
    query = message.text

    logger.info(f"Received message from user {user_id}: {query}")

    try:
        await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)

        answer, input_tokens, output_tokens = await process_query(query)
        dialog_id = await save_dialog(
            user_id, query, answer, input_tokens, output_tokens
        )

        logger.info(f"Processed query for user {user_id}. Dialog ID: {dialog_id}")

        # Send the final answer with the feedback keyboard
        await message.answer(
            answer,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_feedback_keyboard(dialog_id),
        )

    except Exception as e:
        logger.error(f"Error processing query for user {user_id}: {str(e)}")

        # Inform the user about the error
        error_message = "I'm sorry, but an error occurred while processing your query. Please try again later."
        await message.answer(error_message, parse_mode=ParseMode.MARKDOWN)


@router.callback_query(F.data.startswith("feedback:"))
async def handle_feedback(callback_query: CallbackQuery):
    _, dialog_id, feedback = callback_query.data.split(":")
    is_positive = feedback == "positive"
    user_id = callback_query.from_user.id

    logger.info(
        f"Received feedback from user {user_id} for dialog {dialog_id}: {feedback}"
    )

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
        logger.info(
            f"Feedback processed successfully for user {user_id}, dialog {dialog_id}"
        )
    except Exception as e:
        logger.error(
            f"Error saving feedback for user {user_id}, dialog {dialog_id}: {str(e)}"
        )
        await callback_query.answer(
            "Sorry, there was an error processing your feedback."
        )


@router.callback_query(F.data == "disabled")
async def handle_disabled_feedback(callback_query: CallbackQuery):
    await callback_query.answer("You've already provided feedback for this response.")
