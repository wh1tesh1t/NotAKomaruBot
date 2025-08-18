import logging
import time

import hydrogram
from hydrogram import Client
from hydrogram.enums import ParseMode
from hydrogram.errors import BadRequest
from hydrogram.raw.all import layer

from komarubot.config import BotConfig

from komarubot.utils.git import Git
from komarubot.utils.colors import TextColor

logger = logging.getLogger(__name__)

class KomaruBot(Client):
    def __init__(self):
        self.config = BotConfig()

        super().__init__(
            name=self.__class__.__name__,
            app_version=f"NotAKomaruBot r{Git.version()} ({Git.commit()})",
            api_id=self.config.API_ID,
            api_hash=self.config.API_HASH,
            bot_token=self.config.TOKEN,
            parse_mode=ParseMode.HTML,
            plugins={"root": "komarubot.plugins"},
            sleep_threshold=180,
        )

    async def start(self):
        await super().start()
        self.start_time = time.time()

        logger.info(TextColor.cyan(
            f"Hydrogram v{hydrogram.__version__} (Layer {layer}) — started on user @{self.me.username}."
        ))

        message = (
            "<b>NotAKomaruBot is now online!</b>\n"
            f"<b>Version:</b> <code>r{Git.version()} ({Git.commit()})</code>\n"
            f"<b>Hydrogram:</b> <code>v{hydrogram.__version__}</code>"
        )

        try:
            await self.send_message(chat_id=self.config.LOG_CHANNEL_ID, text=message)
        except BadRequest:
            logger.warning(TextColor.yellow("Failed to send startup message to LOG_CHANNEL_ID!"))

    async def stop(self):
        await super().stop()
