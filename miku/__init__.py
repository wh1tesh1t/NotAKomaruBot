import logging
import time

import hydrogram
from hydrogram import Client
from hydrogram.enums import ParseMode
from hydrogram.errors import BadRequest
from hydrogram.raw.all import layer

from miku.config import MikuConfig

from miku.utils.git import Git
from miku.utils.colors import TextColor

logger = logging.getLogger(__name__)

class MikuBot(Client):
    def __init__(self):
        self.config = MikuConfig()

        super().__init__(
            name=self.__class__.__name__,
            app_version=f"MikuBot r{Git.version()} ({Git.commit()})",
            api_id=self.config.API_ID,
            api_hash=self.config.API_HASH,
            bot_token=self.config.TOKEN,
            parse_mode=ParseMode.HTML,
            workers=self.config.WORKERS,
            #plugins={"root": "miku.plugins"},
            sleep_threshold=180,
        )

    async def start(self):
        await super().start()
        self.start_time = time.time()

        logger.info(TextColor.green(
            f"Hydrogram v{hydrogram.__version__} (Layer {layer}) — MikuBot started on user @{self.me.username}."
        ))

        message = (
            "<b>MikuBot is now online!</b>\n"
            f"<b>Version:</b> <code>r{Git.version()} ({Git.commit()})</code>\n"
            f"<b>Hydrogram:</b> <code>v{hydrogram.__version__}</code>"
        )

        try:
            await self.send_message(chat_id=self.config.LOG_CHANNEL_ID, text=message)
        except BadRequest:
            logger.warning(TextColor.yellow("Failed to send startup message to LOG_CHANNEL_ID!"))

    async def stop(self):
        await super().stop()
        logger.info(TextColor.red("MikuBot has been stopped."))
