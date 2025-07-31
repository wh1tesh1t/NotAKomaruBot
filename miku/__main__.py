import asyncio
import logging
import platform

from hydrogram import idle

from miku import MikuBot
from miku.utils.colors import TextColor

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s.%(funcName)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Reduce noisy logs from hydrogram modules
logging.getLogger("hydrogram.syncer").setLevel(logging.WARNING)
logging.getLogger("hydrogram.client").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

if platform.system() == "Windows":
    logger.info(TextColor.yellow("Windows detected: uvloop is not used!"))
else:
    import uvloop
    uvloop.install()
    logger.info(TextColor.green("uvloop has been set as the default event loop!"))


async def main():
    miku = MikuBot()

    try:
        await miku.start()
        await idle()
    except KeyboardInterrupt:
        logger.warning(TextColor.yellow("Forced stop… Bye!"))
    finally:
        await miku.stop()



if __name__ == "__main__":
    event_policy = asyncio.get_event_loop_policy()
    event_loop = event_policy.new_event_loop()
    asyncio.set_event_loop(event_loop)

    event_loop.run_until_complete(main())
    event_loop.close()
