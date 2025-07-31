import logging
import aiosqlite

from miku.config import MikuConfig
from miku.utils.colors import TextColor

logger = logging.getLogger(__name__)

class DatabaseCore:
    def __init__(self):
        self.config = MikuConfig()
        self.conn = None
        self.db_path = self.config.DATABASE_NAME

    async def connect(self):
        """Establishes the connection and initializes required tables."""
        self.conn = await aiosqlite.connect(self.db_path)
        await self.conn.executescript(self.init_script())
        await self.conn.execute("PRAGMA journal_mode=WAL")
        await self.conn.commit()
        self.conn.row_factory = aiosqlite.Row
        logger.info(TextColor.green("Database connection established and initialized."))

    async def close(self):
        """Closes the database connection."""
        if self.conn:
            await self.conn.close()
            self.conn = None
            logger.info(TextColor.red("Database connection closed."))

    def getconnection(self) -> aiosqlite.Connection:
        if not self.conn:
            raise RuntimeError("Database connection is not open.")
        return self.conn

    @staticmethod
    def init_script() -> str:
        """SQL script to create necessary tables if they don’t exist."""
        return """
        CREATE TABLE IF NOT EXISTS groups (
            chat_id INTEGER PRIMARY KEY,
            chat_lang TEXT
        );

        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            chat_lang TEXT
        );

        CREATE TABLE IF NOT EXISTS channels (
            chat_id INTEGER PRIMARY KEY,
            chat_lang TEXT
        );
        """
