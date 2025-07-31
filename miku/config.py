import os
import dotenv
import logging

logger = logging.getLogger(__name__)

dotenv.load_dotenv("config.env", override=True)

class MikuConfig:
    def __init__(self):
        def get_env_var(name, required=True, cast=str, default=None):
            val = os.getenv(name, default)
            if required and (val is None or val == ""):
                logger.error(f"Environment variable {name} is required but not set.")
                return None
            if val is not None:
                try:
                    return cast(val)
                except ValueError:
                    logger.error(f"Environment variable {name} must be of type {cast.__name__}. Got: {val}")
                    return None
            return val

        self.TOKEN = get_env_var("TOKEN")
        self.API_ID = get_env_var("API_ID", cast=int)
        self.API_HASH = get_env_var("API_HASH")
        self.WORKERS = get_env_var("WORKERS", required=False, cast=int, default="24")
        self.LOG_CHANNEL_ID = get_env_var("LOG_CHANNEL_ID", cast=int)

        # Проверка критических переменных
        if not all([self.TOKEN, self.API_ID, self.API_HASH]):
            logger.critical("Missing required configuration values. Exiting.")
            raise SystemExit(1)
