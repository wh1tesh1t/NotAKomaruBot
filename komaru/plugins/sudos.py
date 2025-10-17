# SPDX-License-Identifier: MIT
# Copyright (c) 2018-2024 Amano LLC

from __future__ import annotations

import asyncio
import html
import io
import os
import re
import sys
import time
import traceback
from contextlib import redirect_stdout, suppress
from sqlite3 import IntegrityError, OperationalError
from typing import TYPE_CHECKING

import humanfriendly
# import speedtest
from hydrogram import Client, filters
from hydrogram.enums import ChatType
from hydrogram.errors import RPCError, MessageNotModified, MessageIdInvalid
from hydrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from meval import meval

from config import DATABASE_PATH
from komaru.database import database
from komaru.database.restarted import set_restarted
from komaru.utils import sudofilter
from komaru.utils.localization import Strings, use_chat_lang
from komaru.utils.utils import shell_exec
from komaru.utils.builder_keyboard import setup_keyboard

if TYPE_CHECKING:
    from hydrogram.types import Message

prefix: list | str = "!"

conn = database.get_conn()

@Client.on_message(filters.command("sudos", prefix) & sudofilter)
@use_chat_lang
@setup_keyboard()
async def sudos(c: Client, m: Message, s: Strings):
    await m.reply_text(s("SOsu!"))

@Client.on_message(filters.command("cmd", prefix) & sudofilter)
@use_chat_lang
async def run_cmd(c: Client, m: Message, s: Strings):
    cmd = m.text.split(maxsplit=1)[1]
    if re.match(r"(?i)poweroff|halt|shutdown|reboot|screenfetch|uptime|fastfetch|neofetch|grep|ls -a", cmd):
        await m.reply_text(s("sudos_forbidden_command"))
        return
    stdout, stderr = await shell_exec(cmd)
    await m.reply_text(
        (f"<b>Output:</b>\n<code>{html.escape(stdout)}</code>" if stdout else "")
        + (f"\n<b>Errors:</b>\n<code>{stderr}</code>" if stderr else "")
    )

@Client.on_message(filters.command("eval", prefix) & sudofilter)
async def evals(c: Client, m: Message):
    text = m.text.split(maxsplit=1)[1]
    try:
        res = await meval(text, globals(), **locals())
    except BaseException:
        ev = traceback.format_exc()
        await m.reply_text(f"<code>{html.escape(ev)}</code>")
    else:
        try:
            await m.reply_text(f"<code>{html.escape(str(res))}</code>")
        except BaseException as e:
            await m.reply_text(str(e))

@Client.on_message(filters.command("exec", prefix) & sudofilter)
async def execs(c: Client, m: Message):
    strio = io.StringIO()
    code = m.text.split(maxsplit=1)[1]
    exec(
        "async def __ex(c, m): " + " ".join("\n " + line for line in code.split("\n"))
    )
    with redirect_stdout(strio):
        try:
            await locals()["__ex"](c, m)
        except BaseException:
            await m.reply_text(html.escape(traceback.format_exc()))
            return
    if strio.getvalue().strip():
        out = f"<code>{html.escape(strio.getvalue())}</code>"
    else:
        out = "Command executed."
    await m.reply_text(out)

@Client.on_message(filters.command("sql", prefix) & sudofilter)
async def execsql(c: Client, m: Message):
    command = m.text.split(maxsplit=1)[1]
    try:
        ex = await conn.execute(command)
    except (IntegrityError, OperationalError) as e:
        await m.reply_text(f"SQL executed with an error: {e.__class__.__name__}: {e}")
        return
    ret = await ex.fetchall()
    await conn.commit()
    if not ret:
        await m.reply_text("SQL executed successfully and without any return.")
        return
    res = "|".join([name[0] for name in ex.description]) + "\n"
    res += "\n".join(["|".join(str(s) for s in items) for items in ret])
    if len(res) < 3500:
        await m.reply_text(f"<code>{res}</code>")
        return
    bio = io.BytesIO()
    bio.name = "output.txt"
    bio.write(res.encode())
    await m.reply_document(bio)

@Client.on_message(filters.command("restart", prefix) & sudofilter)
@use_chat_lang
async def restart(c: Client, m: Message, s: Strings):
    sent = await m.reply_text(s("sudos_restarting"))
    await set_restarted(sent.chat.id, sent.id)
    await conn.commit()
    args = [sys.executable, "-m", "komaru"]
    os.execv(sys.executable, args)

@Client.on_message(filters.command("leave", prefix) & sudofilter)
async def leave_chat(c: Client, m: Message):
    if len(m.command) == 1:
        with suppress(RPCError):
            await m.chat.leave()
    else:
        chat_id = m.text.split(maxsplit=1)[1]
        with suppress(RPCError):
            await c.leave_chat(int(chat_id))

@Client.on_message(filters.command(["bot_stats", "stats"], prefix) & sudofilter)
async def getbotstats(c: Client, m: Message):
    users_count = await conn.execute("select count() from users")
    users_count = await users_count.fetchone()
    groups_count = await conn.execute("select count() from groups")
    groups_count = await groups_count.fetchone()
    filters_count = await conn.execute("select count() from filters")
    filters_count = await filters_count.fetchone()
    notes_count = await conn.execute("select count() from notes")
    notes_count = await notes_count.fetchone()
    bot_uptime = round(time.time() - c.start_time)
    bot_uptime = humanfriendly.format_timespan(bot_uptime)
    await m.reply_text(
        "<b>Bot statistics:</b>\n\n"
        f"<b>Users:</b> {users_count[0]}\n"
        f"<b>Groups:</b> {groups_count[0]}\n"
        f"<b>Filters:</b> {filters_count[0]}\n"
        f"<b>Notes:</b> {notes_count[0]}\n\n"
        f"<b>Uptime:</b> {bot_uptime}"
    )

@Client.on_message(filters.command("del", prefix) & sudofilter)
async def del_message(c: Client, m: Message):
    err = ""
    try:
        await c.delete_messages(m.chat.id, m.reply_to_message.id)
    except RPCError as e:
        err += str(e)
    try:
        await c.delete_messages(m.chat.id, m.id)
    except RPCError as e:
        err += str(e)
    await m.reply_text(err)

@Client.on_message(
    filters.command("backup", prefix)
    & sudofilter
    & ~filters.forwarded
    & ~filters.group
    & ~filters.via_bot
)
async def backupcmd(c: Client, m: Message):
    await m.reply_document(DATABASE_PATH)

@Client.on_message(filters.command("upload", prefix) & sudofilter)
async def uploadfile(c: Client, m: Message):
    if not m.reply_to_message:
        await m.reply_text("You must reply to a file to upload.")
    sent = await m.reply_to_message.reply_text("Uploading file…")
    file_path = await m.reply_to_message.download(m.command[1] if len(m.command) > 1 else "")
    await sent.edit_text(f"File successfully saved.")

@Client.on_message(filters.command("doc", prefix) & sudofilter)
async def downloadfile(c: Client, m: Message):
    if len(m.text.split()) > 1:
        await m.reply_document(m.command[1])
    else:
        await m.reply_text("You must specify the document path.")

@Client.on_message(filters.command("chat", prefix) & sudofilter)
async def getchatcmd(c: Client, m: Message):
    if len(m.text.split()) == 1:
        await m.reply_text("You must specify the Chat.")
        return
    targetchat = await c.get_chat(m.command[1])
    if targetchat.type == ChatType.PRIVATE:
        await m.reply_text("This is a private Chat.")
        return
    await m.reply_text(
        f"<b>Title:</b> {targetchat.title}\n<b>Username:</b> {targetchat.username}\n<b>Members:</b> {targetchat.members_count}"
    )

@Client.on_message(filters.command("send", prefix) & sudofilter)
@use_chat_lang
async def send_msg(c: Client, m: Message, s: Strings):
    args = m.text.split()
    if "-h" in args:
        await m.reply_text(s("send_help"), disable_web_page_preview=True)
        return
    chat_id = m.chat.id
    text = None
    file = None
    forward = False
    edit_id = None
    delete_id = None
    reply_to = None
    topic_id = None
    buttons = []
    rows = []
    try:
        if "-id" in args:
            chat_id = int(args[args.index("-id") + 1])
        if "-tid" in args:
            topic_id = int(args[args.index("-tid") + 1])
        if "-edit" in args:
            edit_id = int(args[args.index("-edit") + 1])
        if "-del" in args:
            delete_id = int(args[args.index("-del") + 1])
        if "-rply" in args:
            reply_to = int(args[args.index("-rply") + 1])
        if "-t" in args:
            raw = m.text
            t_index = raw.find("-t")
            if t_index != -1:
                sub = raw[t_index + 2:].strip()
                next_flags = [" -url", " -cb", " -id", " -edit", " -del", " -rply", " -fwd", " -tid"]
                cut_pos = len(sub)
                for flag in next_flags:
                    i = sub.find(flag)
                    if i != -1 and i < cut_pos:
                        cut_pos = i
                text = sub[:cut_pos].strip().replace("\\n", "\n")
        parts = re.split(r"\s*\|\s*", m.text)
        for part in parts:
            row_buttons = []
            pattern = re.compile(r"-(url|cb)(\d*)\b")
            matches = list(pattern.finditer(part))
            for idx, match in enumerate(matches):
                start = match.end()
                end = matches[idx + 1].start() if idx + 1 < len(matches) else len(part)
                region = part[start:end].strip()
                if not region:
                    continue
                region_parts = region.split()
                value = region_parts[0]
                label = region[len(value):].strip()
                btn_text = label or (s("send_button_url_no_text") if match.group(1) == "url" else s("send_button_callback_no_text"))
                if match.group(1) == "url":
                    row_buttons.append(InlineKeyboardButton(btn_text, url=value))
                else:
                    row_buttons.append(InlineKeyboardButton(btn_text, callback_data=value))
            if row_buttons:
                rows.append(row_buttons)
        keyboard = InlineKeyboardMarkup(rows) if rows else None
        if "-fwd" in args:
            forward = True
        if delete_id:
            try:
                await c.delete_messages(chat_id, delete_id)
                await m.reply_text(s("send_deleted").format(id=delete_id, user_id=m.from_user.id))
            except MessageIdInvalid:
                await m.reply_text(s("send_invalid_id"))
            except RPCError as e:
                await m.reply_text(s("send_api_error").format(e=e))
            return
        r = m.reply_to_message
        if r:
            if forward:
                await r.forward(chat_id)
                await m.reply_text(s("send_forwarded").format(user_id=m.from_user.id))
                return
            if r.photo:
                file = r.photo.file_id
            elif r.video:
                file = r.video.file_id
            elif r.document:
                file = r.document.file_id
            elif r.audio:
                file = r.audio.file_id
            elif r.sticker:
                file = r.sticker.file_id
            if not text and (r.caption or r.text):
                text = r.caption or r.text
        if not text and not file and not forward:
            await m.reply_text(s("send_no_content"))
            return
        if edit_id:
            try:
                await c.edit_message_text(chat_id=chat_id, message_id=edit_id, text=text or "", reply_markup=keyboard)
                await m.reply_text(s("send_edited").format(id=edit_id, user_id=m.from_user.id))
                return
            except MessageNotModified:
                await m.reply_text(s("send_not_modified"))
                return
            except RPCError:
                try:
                    await c.edit_message_caption(chat_id=chat_id, message_id=edit_id, caption=text or "", reply_markup=keyboard)
                    await m.reply_text(s("send_edited").format(id=edit_id, user_id=m.from_user.id))
                    return
                except RPCError as e:
                    await m.reply_text(s("send_api_error").format(e=e))
                    return
        send_args = dict(chat_id=chat_id, reply_markup=keyboard)
        if reply_to:
            send_args["reply_to_message_id"] = reply_to
        if topic_id:
            send_args["message_thread_id"] = topic_id
        if file:
            if r and r.photo:
                await c.send_photo(**send_args, photo=file, caption=text or "")
            elif r and r.video:
                await c.send_video(**send_args, video=file, caption=text or "")
            elif r and r.audio:
                await c.send_audio(**send_args, audio=file, caption=text or "")
            else:
                await c.send_document(**send_args, document=file, caption=text or "")
        else:
            await c.send_message(**send_args, text=text or "")
        await m.reply_text(s("send_success").format(user_id=m.from_user.id))
    except RPCError as e:
        await m.reply_text(s("send_api_error").format(e=e))
    except Exception as e:
        await m.reply_text(s("send_exception_error").format(e=e))
