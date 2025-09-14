# SPDX-License-Identifier: MIT
# Copyright (c) 2018-2024 Amano LLC

import re
from urllib.parse import quote_plus

from hydrogram import Client, filters
from hydrogram.types import (
    Message,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

from config import PREFIXES
from komaru.utils import commands, http, inline_commands
from komaru.utils.localization import Strings, use_chat_lang
from komaru.utils.builder_keyboard import setup_keyboard

@Client.on_message(filters.command("github", PREFIXES))
@Client.on_inline_query(filters.regex(r"^(github) .+", re.IGNORECASE))
@use_chat_lang
@setup_keyboard()
async def git(c: Client, m: InlineQuery | Message, s: Strings):
    if isinstance(m, Message):
        input_text = m.text
        reply_target_id = m.id
    else:
        input_text = m.query
        reply_target_id = None

    parts = input_text.split(maxsplit=1)

    if len(parts) == 1:
        error_message = s("git_no_username")
        if isinstance(m, Message):
            await m.reply_text(error_message, reply_to_message_id=reply_target_id)
        else:
            await m.answer([
                InlineQueryResultArticle(
                    id="git_no_username_error",
                    title=s("git_no_username"),
                    input_message_content=InputTextMessageContent(message_text=error_message),
                    description=s("git_no_username")
                )
            ], cache_time=0)
        return

    username = parts[1]
    res = {}
    try:
        req_response = await http.get(f"https://api.github.com/users/{username}")
        res = req_response.json()
    except Exception as e:
        api_error_message = s("git_api_error").format(error=str(e)) if hasattr(s, "git_api_error") else f"Произошла ошибка API: {e}"
        if isinstance(m, Message):
            await m.reply_text(api_error_message, reply_to_message_id=reply_target_id)
        else:
            await m.answer([
                InlineQueryResultArticle(
                    id="git_api_error",
                    title=s("git_api_error").format(error=str(e)),
                    input_message_content=InputTextMessageContent(message_text=api_error_message),
                    description=s("git_api_error").format(error=str(e))
                )
            ], cache_time=0)
        return

    if not res.get("login"):
        error_message = s("git_user_not_found")
        if isinstance(m, Message):
            await m.reply_text(error_message, reply_to_message_id=reply_target_id)
        else:
            await m.answer([
                InlineQueryResultArticle(
                    id="git_user_not_found_error",
                    title=s("git_user_not_found"),
                    input_message_content=InputTextMessageContent(message_text=error_message),
                    description=s("git_user_not_found")
                )
            ], cache_time=0)
        return

    avatar = res["avatar_url"]
    anticache = ""

    if isinstance(m, Message):
        try:
            head_response = await http.head(avatar)
            anticache = quote_plus(head_response.headers["Last-Modified"])
        except Exception:
            pass

    caption_text = s("git_user_info")
    formatted_caption = caption_text.format(
        name=res.get("name") or "None",
        username=res["login"],
        uid=res["id"],
        location=res.get("location") or "None",
        type=res["type"],
        typeview=res.get("user_view_type") or "None",
        bio=res.get("bio") or "None",
        repos=res.get("public_repos") or "Private",
        gists=res.get("public_gists") or "Private",
        followers=res.get("followers") or "Private",
        following=res.get("following") or "Private",
        createdat=res["created_at"],
        updatedat=res["updated_at"],
    )

    if isinstance(m, Message):
        await m.reply_photo(
            avatar + ("?" + anticache if anticache else ""),
            caption=formatted_caption,
            reply_to_message_id=reply_target_id,
        )
    else:
        await m.answer([
            InlineQueryResultArticle(
                id=f"github_user_{username}",
                title=f"{res['login']} - {res['id']}, ({res.get('name', 'N/A')})",
                description=f"{res['type']} - {res.get('location', 'N/A')}",
                input_message_content=InputTextMessageContent(
                    message_text=formatted_caption
                ),
                thumb_url=avatar
            )
        ], cache_time=0)

commands.add_command("github", "info")
inline_commands.add_command("github <username>")
