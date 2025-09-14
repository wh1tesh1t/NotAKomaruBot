# SPDX-License-Identifier: MIT
# Copyright (c) 2018-2024 Amano LLC

import asyncio
import logging
import platform
import sys

from hydrogram import idle

from .bot import NotAKomaru
from .database import database
from .utils import http

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s.%(funcName)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# To avoid some annoying log
logging.getLogger("hydrogram.syncer").setLevel(logging.WARNING)
logging.getLogger("hydrogram.client").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

try:
    import uvloop

    uvloop.install()
except ImportError:
    if platform.system() != "Windows":
        logger.warning("uvloop is not installed and therefore will be disabled.")


async def main():
    komaru = NotAKomaru()

    try:
        # start the bot
        await database.connect()
        await komaru.start()

        if "test" not in sys.argv:
            await idle()
    except KeyboardInterrupt:
        # exit gracefully
        logger.warning("Forced stop… Bye!")
    finally:
        # close https connections and the DB if open
        await komaru.stop()
        await http.aclose()
        if database.is_connected:
            await database.close()


if __name__ == "__main__":
    # open new asyncio event loop
    event_policy = asyncio.get_event_loop_policy()
    event_loop = event_policy.new_event_loop()
    asyncio.set_event_loop(event_loop)

    # start the bot
    event_loop.run_until_complete(main())

    # close asyncio event loop
    event_loop.close()
