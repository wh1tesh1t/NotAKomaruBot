from __future__ import annotations

import functools
import re
from typing import Callable, Any

from hydrogram import Client, filters
from hydrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)


_menu_load_file = "custom/menus.py"
_parsed_mdata = {}
_callback_tcm = {}

def build_kbc(file_path=_menu_load_file) -> dict[str, list[list[dict[str, str]]]]:
    mdata = {}
    cr_cmd = None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                match = re.match(r'^\{([^{}]+)\}:$', line)
                if match:
                    cr_cmd = match.group(1).strip()
                    mdata[cr_cmd] = []
                elif cr_cmd:
                    raw_button_defs = line.split('|')
                    cr_rb = []
                    for raw_button_def in raw_button_defs:
                        raw_button_def = raw_button_def.strip()
                        if not raw_button_def:
                            continue

                        parts = raw_button_def.split(' - ', 2)
                        if len(parts) == 3:
                            button_text = parts[0].strip()
                            button_type = parts[1].strip().lower()
                            button_value = parts[2].strip()

                            cr_rb.append({
                                "text": button_text,
                                "type": button_type,
                                "value": button_value
                            })
                    if cr_rb:
                        mdata[cr_cmd].append(cr_rb)
    except FileNotFoundError:
        pass
    return mdata

def setup_keyboard() -> Callable[[Callable], Callable]:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(c: Client, m: Message | CallbackQuery, s: Strings, *args: Any, **kwargs: Any) -> Any:
            cmd_fmenu = None
            function_name_for_menu = func.__name__

            if isinstance(m, Message) and m.command:
                cmd_fmenu = f"/{m.command[0]}"
            elif isinstance(m, CallbackQuery) and m.data:
                cmd_fmenu = _callback_tcm.get(m.data)
            kbc_gcmd: InlineKeyboardMarkup | None = None
            if cmd_fmenu and cmd_fmenu in _parsed_mdata:
                menu_rows = _parsed_mdata[cmd_fmenu]
                inline_keyboard_markup_rows = []
                for row_items in menu_rows:
                    kbc = []
                    for item in row_items:
                        text = item["text"]
                        button_type = item["type"]
                        value = item["value"]
                        if button_type == "url":
                            kbc.append(InlineKeyboardButton(text=text, url=value))
                        elif button_type == "callback":
                            kbc.append(InlineKeyboardButton(text=text, callback_data=value))
                    if kbc:
                        inline_keyboard_markup_rows.append(kbc)
                if inline_keyboard_markup_rows:
                    kbc_gcmd = InlineKeyboardMarkup(inline_keyboard=inline_keyboard_markup_rows)

            kbc_gfunc: InlineKeyboardMarkup | None = None
            if function_name_for_menu and function_name_for_menu in _parsed_mdata:
                menu_rows = _parsed_mdata[function_name_for_menu]
                inline_keyboard_markup_rows = []
                for row_items in menu_rows:
                    kbc = []
                    for item in row_items:
                        text = item["text"]
                        button_type = item["type"]
                        value = item["value"]
                        if button_type == "url":
                            kbc.append(InlineKeyboardButton(text=text, url=value))
                        elif button_type == "callback":
                            kbc.append(InlineKeyboardButton(text=text, callback_data=value))
                    if kbc:
                        inline_keyboard_markup_rows.append(kbc)
                if inline_keyboard_markup_rows:
                    kbc_gfunc = InlineKeyboardMarkup(inline_keyboard=inline_keyboard_markup_rows)

            send_method = None
            target_object: Message | Any = None
            method_name = None

            if isinstance(m, Message):
                target_object = m
                method_name = 'reply_text'
            elif isinstance(m, CallbackQuery):
                target_object = m.message
                method_name = 'edit_text'

            if target_object and hasattr(target_object, method_name):
                send_method = getattr(target_object, method_name)

                _OMITTED_ARG = object()

                async def psend_method(
                    text: str,
                    reply_markup: InlineKeyboardMarkup | None = _OMITTED_ARG,
                    *send_args: Any,
                    **send_kwargs: Any
                ) -> Any:

                    cikr: list[list[InlineKeyboardButton]] = []

                    if reply_markup is _OMITTED_ARG:
                        if method_name == 'edit_text' and target_object.reply_markup:
                            cikr.extend(target_object.reply_markup.inline_keyboard)
                    elif reply_markup is not None:
                        cikr.extend(reply_markup.inline_keyboard)

                    if kbc_gcmd:
                        cikr.extend(kbc_gcmd.inline_keyboard)

                    if kbc_gfunc:
                        cikr.extend(kbc_gfunc.inline_keyboard)

                    frmt_send: InlineKeyboardMarkup | None = None
                    if cikr:
                        frmt_send = InlineKeyboardMarkup(inline_keyboard=cikr)

                    return await send_method(text, reply_markup=frmt_send, *send_args, **send_kwargs)

                setattr(target_object, method_name, psend_method)

            try:
                result = await func(c, m, s, *args, **kwargs)
            finally:
                if target_object and send_method:
                    setattr(target_object, method_name, send_method)

            return result

        return wrapper
    return decorator

def _load_menus() -> None:
    global _parsed_mdata
    _parsed_mdata = build_kbc(_menu_load_file)

_load_menus()
