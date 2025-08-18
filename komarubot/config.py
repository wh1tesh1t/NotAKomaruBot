import os
import dotenv
import logging

logger = logging.getLogger(__name__)

dotenv.load_dotenv("config.env", override=True)

class BotConfig:
    def __init__(self):
        self.TOKEN = self._get_env_var("TOKEN")
        self.API_ID = self._get_env_var("API_ID", cast=int)
        self.API_HASH = self._get_env_var("API_HASH")
        self.LOG_CHANNEL_ID = self._get_env_var("LOG_CHANNEL_ID", cast=int)

    def _get_env_var(self, name, required=True, cast=str, default=None):
        val = os.getenv(name, default)
        if required and (val is None or val == ""):
            logger.error(f"Environment variable '{name}' is required but not set.")
            return None
        if val is not None:
            try:
                return cast(val)
            except (ValueError, TypeError):
                logger.error(f"Environment variable '{name}' must be of type {cast.__name__}. Got: {val}")
                return None
        return val
