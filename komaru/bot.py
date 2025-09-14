# SPDX-License-Identifier: MIT
# Copyright (c) 2018-2024 Amano LLC

import logging
import time
from functools import partial

import hydrogram
from hydrogram import Client
from hydrogram.enums import ParseMode
from hydrogram.errors import BadRequest
from hydrogram.raw.all import layer

from config import API_HASH, API_ID, DISABLED_PLUGINS, LOG_CHAT, TOKEN, WORKERS

from . import __commit__, __version_number__

logger = logging.getLogger(__name__)


class NotAKomaru(Client):
    def __init__(self):
        name = self.__class__.__name__.lower()

        super().__init__(
            name=name,
            app_version=f"NotAKomaru r{__version_number__} ({__commit__})",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=TOKEN,
            parse_mode=ParseMode.HTML,
            workers=WORKERS,
            plugins={"root": "komaru.plugins", "exclude": DISABLED_PLUGINS},
            sleep_threshold=180,
        )

    async def start(self):
        await super().start()

        self.start_time = time.time()

        logger.info(
            "NotAKomaru running with Hydrogram v%s (Layer %s) started on @%s. Hi!",
            hydrogram.__version__,
            layer,
            self.me.username,
        )

        from .database.restarted import del_restarted, get_restarted  # noqa: PLC0415
        from komaru.utils.localization import get_locale_string, get_lang

        wr = await get_restarted()
        await del_restarted()

        start_message = (
            "<b>NotAKomaru started!</b>\n\n"
            f"<b>Version number:</b> <code>r{__version_number__} ({__commit__})</code>\n"
            f"<b>Hydrogram:</b> <code>v{hydrogram.__version__}</code>"
        )

        try:
            await self.send_message(chat_id=LOG_CHAT, text=start_message)
            if wr:
                lang = await get_lang(message=wr[0], client=self)
                strings = partial(get_locale_string, lang)
                await self.edit_message_text(wr[0], wr[1], text=strings("sudos_restarted"))
        except BadRequest:
            logger.warning("Unable to send message to LOG_CHAT.")

    async def stop(self):
        await super().stop()
        logger.warning("NotAKomaru stopped. Bye!")
