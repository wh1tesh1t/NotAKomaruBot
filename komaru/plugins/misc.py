# SPDX-License-Identifier: MIT
# Copyright (c) 2018-2024 Amano LLC

import re
from html import escape
from urllib.parse import quote, unquote

from hydrogram import Client, filters
from hydrogram.enums import ChatMembersFilter, ParseMode
from hydrogram.errors import BadRequest
from hydrogram.types import InlineKeyboardMarkup, Message

from config import LOG_CHAT, PREFIXES
from komaru.utils import button_parser, commands, http
from komaru.utils.consts import ADMIN_STATUSES
from komaru.utils.localization import Strings, use_chat_lang


@Client.on_message(filters.command("mark", PREFIXES))
@use_chat_lang
async def mark(c: Client, m: Message, s: Strings):
    if len(m.command) == 1:
        await m.reply_text(s("mark_usage"))
        return

    txt = m.text.split(None, 1)[1]
    msgtxt, buttons = button_parser(txt)
    await m.reply_text(
        msgtxt,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=(InlineKeyboardMarkup(buttons) if len(buttons) != 0 else None),
    )


@Client.on_message(filters.command("html", PREFIXES))
@use_chat_lang
async def html(c: Client, m: Message, s: Strings):
    if len(m.command) == 1:
        await m.reply_text(s("html_usage"))
        return

    txt = m.text.split(None, 1)[1]
    msgtxt, buttons = button_parser(txt)
    await m.reply_text(
        msgtxt,
        parse_mode=ParseMode.HTML,
        reply_markup=(InlineKeyboardMarkup(buttons) if len(buttons) != 0 else None),
    )



@Client.on_message(filters.command("urlencode", PREFIXES))
async def urlencodecmd(c: Client, m: Message):
    await m.reply_text(quote(m.text.split(None, 1)[1]))


@Client.on_message(filters.command("urldecode", PREFIXES))
async def urldecodecmd(c: Client, m: Message):
    await m.reply_text(unquote(m.text.split(None, 1)[1]))


@Client.on_message(filters.command("parsebutton"))
@use_chat_lang
async def button_parse_helper(c: Client, m: Message, s: Strings):
    if len(m.text.split()) > 2:
        await m.reply_text(
            f"[{m.text.split(None, 2)[2]}](buttonurl:{m.command[1]})",
            parse_mode=ParseMode.DISABLED,
        )
    else:
        await m.reply_text(s("parsebtn_err"))


commands.add_command("mark", "general")
commands.add_command("html", "general")
commands.add_command("urlencode", "general")
commands.add_command("urldecode", "general")
commands.add_command("parsebutton", "general")
