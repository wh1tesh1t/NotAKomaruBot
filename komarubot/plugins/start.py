from hydrogram import Client, filters
from hydrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from hydrogram.enums import ParseMode

@Client.on_message(filters.command("start"))
@Client.on_callback_query(filters.regex(f"^start_cmd$"))
async def start(Client, m: Message | CallbackQuery):
    msg = m
    edit = msg.edit_text
    reply = msg.reply_text
    button = InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                button("test", url=f"https://google.com"),
            ],
        ]
    )
    await reply("Hello World!", reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
