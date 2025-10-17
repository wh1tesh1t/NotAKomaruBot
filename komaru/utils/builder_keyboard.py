from __future__ import annotations

import functools
import re
from typing import Callable, Any

from hydrogram import Client, filters
from hydrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import PREFIXES
from komaru.utils.localization import Strings, get_lang, get_locale_string
from functools import partial

_menu_load_file = "custom/menus.py"
_parsed_mdata = {}
_callback_tcm = {}

def build_kbc(file_path=_menu_load_file) -> dict[str, list[list[dict[str, str]]]]:
    mdata = {}
    current_cmd = None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                match = re.match(r'^\{([^{}]+)\}:$', line)
                if match:
                    current_cmd = match.group(1).strip()
                    if current_cmd.startswith("(BOT_PREFIX)"):
                        current_cmd = current_cmd.replace("(BOT_PREFIX)", PREFIXES[0])
                    mdata[current_cmd] = []
                    continue
                if current_cmd:
                    row_buttons = []
                    for raw_btn in line.split('|'):
                        raw_btn = raw_btn.strip()
                        if not raw_btn:
                            continue
                        parts = [p.strip() for p in raw_btn.split(' - ', 2)]
                        if len(parts) == 3:
                            text, btype, value = parts
                            row_buttons.append({
                                "text": text,
                                "type": btype.lower(),
                                "value": value
                            })
                    if row_buttons:
                        mdata[current_cmd].append(row_buttons)
    except FileNotFoundError:
        pass
    return mdata


def setup_keyboard() -> Callable[[Callable], Callable]:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(c: Client, m: Message | CallbackQuery, *args: Any, **kwargs: Any) -> Any:
            if args and callable(args[-1]):
                s = args[-1]
                args = args[:-1]
            else:
                lang = await get_lang(m, c)
                s = partial(get_locale_string, lang)
            cmd_fmenu = None
            func_name = func.__name__
            if isinstance(m, Message) and m.command:
                cmd_fmenu = f"/{m.command[0]}"
            elif isinstance(m, CallbackQuery) and m.data:
                cmd_fmenu = _callback_tcm.get(m.data)
            def build_menu(menu_name: str) -> InlineKeyboardMarkup | None:
                if not menu_name or menu_name not in _parsed_mdata:
                    return None
                rows = _parsed_mdata[menu_name]
                inline_keyboard = []
                for row_items in rows:
                    row = []
                    for item in row_items:
                        text = s(item["text"]) if callable(s) else item["text"]
                        if item["type"] == "url":
                            row.append(InlineKeyboardButton(text=text, url=item["value"]))
                        elif item["type"] == "callback":
                            row.append(InlineKeyboardButton(text=text, callback_data=item["value"]))
                    if row:
                        inline_keyboard.append(row)
                return InlineKeyboardMarkup(inline_keyboard=inline_keyboard) if inline_keyboard else None
            menu_by_cmd = build_menu(cmd_fmenu)
            menu_by_func = build_menu(func_name)
            target = m.message if isinstance(m, CallbackQuery) else m
            send_name = 'edit_text' if isinstance(m, CallbackQuery) else 'reply_text'
            orig_send = getattr(target, send_name)
            async def patched_send(text: str, reply_markup=None, *a, **kw):
                combined_rows = []
                if reply_markup and reply_markup.inline_keyboard:
                    combined_rows.extend(reply_markup.inline_keyboard)
                if menu_by_cmd:
                    combined_rows.extend(menu_by_cmd.inline_keyboard)
                if menu_by_func:
                    combined_rows.extend(menu_by_func.inline_keyboard)
                if combined_rows:
                    reply_markup = InlineKeyboardMarkup(inline_keyboard=combined_rows)
                return await orig_send(text, reply_markup=reply_markup, *a, **kw)
            setattr(target, send_name, patched_send)
            try:
                return await func(c, m, s, *args, **kwargs)
            finally:
                setattr(target, send_name, orig_send)
        return wrapper
    return decorator


def _load_menus() -> None:
    global _parsed_mdata
    _parsed_mdata = build_kbc(_menu_load_file)

_load_menus()