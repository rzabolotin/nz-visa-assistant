from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_feedback_keyboard(dialog_id: int):
    keyboard = [
        [
            InlineKeyboardButton(
                text="👍", callback_data=f"feedback:{dialog_id}:positive"
            ),
            InlineKeyboardButton(
                text="👎", callback_data=f"feedback:{dialog_id}:negative"
            ),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_disabled_feedback_keyboard(selected_feedback: str):
    positive_text = "👍✅" if selected_feedback == "positive" else "👍"
    negative_text = "👎✅" if selected_feedback == "negative" else "👎"
    keyboard = [
        [
            InlineKeyboardButton(text=positive_text, callback_data="disabled"),
            InlineKeyboardButton(text=negative_text, callback_data="disabled"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
