import asyncio
import logging
import platform

from hydrogram import idle

from komarubot import KomaruBot
from komarubot.utils.colors import TextColor

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s.%(funcName)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logging.getLogger("hydrogram.syncer").setLevel(logging.WARNING)
logging.getLogger("hydrogram.client").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def main():
    komaru = KomaruBot()

    try:
        await komaru.start()
        await idle()
    finally:
        await komaru.stop()



if __name__ == "__main__":
    event_policy = asyncio.get_event_loop_policy()
    event_loop = event_policy.new_event_loop()
    asyncio.set_event_loop(event_loop)

    event_loop.run_until_complete(main())
    event_loop.close()
