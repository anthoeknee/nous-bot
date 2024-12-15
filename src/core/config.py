import os
from typing import Any, Dict
from dotenv import load_dotenv
from pathlib import Path


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""

    pass


class Config:
    """Singleton configuration class for the Discord bot with validation."""

    _instance = None
    _required_vars = {
        "DISCORD_TOKEN",
        "DISCORD_SECRET",
        "DISCORD_OWNER_ID",
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _validate_config(self) -> None:
        """Validate required environment variables are set."""
        missing_vars = [
            var for var in self._required_vars if not getattr(self, var, None)
        ]
        if missing_vars:
            raise ConfigValidationError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )

    def _load_config(self) -> None:
        """Load and validate all configuration values."""
        # Load environment variables from .env file
        env_path = Path(".env")
        load_dotenv(dotenv_path=env_path)

        # Discord Configuration
        self.DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
        self.DISCORD_SECRET = os.getenv("DISCORD_SECRET")
        try:
            self.DISCORD_OWNER_ID = int(os.getenv("DISCORD_OWNER_ID", "0"))
        except ValueError:
            raise ConfigValidationError("DISCORD_OWNER_ID must be a valid integer")
        self.DISCORD_COMMAND_PREFIX = os.getenv("DISCORD_COMMAND_PREFIX", "n!")

        # AI Provider API Keys with validation
        self.API_KEYS = {
            "xai": os.getenv("XAI_API_KEY"),
            "openai": os.getenv("OPENAI_API_KEY"),
            "groq": os.getenv("GROQ_API_KEY"),
            "cohere": os.getenv("COHERE_API_KEY"),
            "fal": os.getenv("FAL_API_KEY"),
            "google": os.getenv("GOOGLE_API_KEY"),
        }

        # Service Configurations with type hints
        self.SERVICES_CONFIG: Dict[str, Dict[str, Any]] = {
            "cache": {
                "enabled": True,
                "class": "src.services.redis.service.RedisService",
                "config": {
                    "host": os.getenv("REDIS_HOST", "localhost"),
                    "port": int(os.getenv("REDIS_PORT", "6379")),
                    "password": os.getenv("REDIS_PASSWORD", ""),
                    "prefix": "discord_bot",
                    "ttl": int(os.getenv("REDIS_CONVERSATION_TTL", "5400")),
                },
            },
            "database": {
                "enabled": True,
                "class": "src.services.database.DatabaseSession",
                "config": {
                    "session_url": os.getenv("DATABASE_SESSION_URL"),
                    "transaction_url": os.getenv("DATABASE_TRANSACTION_URL"),
                    "direct_url": os.getenv("DATABASE_DIRECT_URL"),
                    "pool_size": int(os.getenv("DATABASE_POOL_SIZE", "20")),
                    "pool_timeout": int(os.getenv("DATABASE_POOL_TIMEOUT", "30")),
                    "use_connection_pooling": os.getenv(
                        "USE_CONNECTION_POOLING", "true"
                    ).lower()
                    == "true",
                },
            },
            "llm": {
                "enabled": True,
                "class": "src.services.llm.LLMService",
                "config": {
                    "default_provider": "google",
                    "provider_configs": {
                        "google": {
                            "api_key": self.API_KEYS["google"],
                            "model": "gemini-2.0-flash-exp",
                        }
                    },
                },
            },
        }

        # Logging Configuration
        self.LOGGING_CONFIG = {
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "directory": Path(os.getenv("LOG_DIR", "logs")),
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        }

        # Database URLs with validation
        self.DATABASE_URLS = {
            "session": os.getenv("DATABASE_SESSION_URL"),
            "transaction": os.getenv("DATABASE_TRANSACTION_URL"),
            "direct": os.getenv("DATABASE_DIRECT_URL"),
        }

        # Validate configuration
        self._validate_config()

    def get_api_key(self, provider: str) -> str:
        """Safely get API key for a provider."""
        key = self.API_KEYS.get(provider)
        if not key:
            raise ConfigValidationError(f"No API key found for provider: {provider}")
        return key

    def ensure_directories(self) -> None:
        """Ensure required directories exist."""
        self.LOGGING_CONFIG["directory"].mkdir(parents=True, exist_ok=True)


# Create a global instance
config = Config()
config.ensure_directories()
