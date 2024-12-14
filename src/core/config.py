import os
from typing import Dict, Any
from dotenv import load_dotenv


class Config:
    """Singleton configuration class for the Discord bot."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """Load all configuration values."""
        # Load environment variables
        load_dotenv()

        # Discord Configuration
        self.DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
        self.DISCORD_SECRET = os.getenv("DISCORD_SECRET")
        self.DISCORD_OWNER_ID = int(os.getenv("DISCORD_OWNER_ID", 0))
        self.DISCORD_COMMAND_PREFIX = os.getenv("DISCORD_COMMAND_PREFIX", "n!")

        # AI Provider API Keys
        self.XAI_API_KEY = os.getenv("XAI_API_KEY")
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        self.COHERE_API_KEY = os.getenv("COHERE_API_KEY")
        self.FAL_API_KEY = os.getenv("FAL_API_KEY")
        self.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

        # Service Configurations
        self.SERVICES_CONFIG = {
            "cache": {
                "enabled": True,
                "class": "src.services.cache.RedisCache",
                "config": {
                    "host": os.getenv("REDIS_HOST", "localhost"),
                    "port": int(os.getenv("REDIS_PORT", 6379)),
                    "password": os.getenv("REDIS_PASSWORD", ""),
                    "prefix": "discord_bot",
                    "ttl": int(os.getenv("REDIS_CONVERSATION_TTL", 5400)),
                },
            },
            "database": {
                "enabled": True,
                "class": "src.services.database.DatabaseSession",
                "config": {
                    "url": os.getenv("DATABASE_SESSION_URL"),
                    "pool_size": int(os.getenv("DATABASE_POOL_SIZE", 20)),
                    "pool_timeout": int(os.getenv("DATABASE_POOL_TIMEOUT", 30)),
                    "use_connection_pooling": os.getenv(
                        "USE_CONNECTION_POOLING", "true"
                    ).lower()
                    == "true",
                },
            },
        }

        # Logging Configuration
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_DIR = os.getenv("LOG_DIR", "logs")
        self.LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        # Database URLs
        self.DATABASE_URLS = {
            "session": os.getenv("DATABASE_SESSION_URL"),
            "transaction": os.getenv("DATABASE_TRANSACTION_URL"),
            "direct": os.getenv("DATABASE_DIRECT_URL"),
        }


# Create a global instance
config = Config()

# Usage example:
# from src.core.config import config
# print(config.DISCORD_TOKEN)
# print(config.SERVICES_CONFIG['database'])
