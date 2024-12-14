from typing import Optional
import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class DatabaseConfig:
    session_url: str
    transaction_url: str
    direct_url: str
    use_pooling: bool
    pool_size: int
    pool_timeout: int


@dataclass
class RedisConfig:
    host: str
    port: int
    password: Optional[str]
    conversation_ttl: int


@dataclass
class DiscordConfig:
    token: str
    secret: str
    owner_id: int
    command_prefix: str


@dataclass
class AIConfig:
    xai_key: str
    openai_key: str
    groq_key: str
    cohere_key: str
    fal_key: str
    google_key: str


class Config:
    _instance: Optional["Config"] = None

    def __init__(self):
        if Config._instance is not None:
            raise RuntimeError("Config is a singleton. Use Config.get()")

        # Load environment variables
        load_dotenv()

        # Initialize configurations
        self.database = DatabaseConfig(
            session_url=os.getenv("DATABASE_SESSION_URL", ""),
            transaction_url=os.getenv("DATABASE_TRANSACTION_URL", ""),
            direct_url=os.getenv("DATABASE_DIRECT_URL", ""),
            use_pooling=os.getenv("USE_CONNECTION_POOLING", "true").lower() == "true",
            pool_size=int(os.getenv("DATABASE_POOL_SIZE", "20")),
            pool_timeout=int(os.getenv("DATABASE_POOL_TIMEOUT", "30")),
        )

        self.redis = RedisConfig(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD"),
            conversation_ttl=int(os.getenv("REDIS_CONVERSATION_TTL", "5400")),
        )

        self.discord = DiscordConfig(
            token=os.getenv("DISCORD_TOKEN", ""),
            secret=os.getenv("DISCORD_SECRET", ""),
            owner_id=int(os.getenv("DISCORD_OWNER_ID", "0")),
            command_prefix=os.getenv("DISCORD_COMMAND_PREFIX", "n!"),
        )

        self.ai = AIConfig(
            xai_key=os.getenv("XAI_API_KEY", ""),
            openai_key=os.getenv("OPENAI_API_KEY", ""),
            groq_key=os.getenv("GROQ_API_KEY", ""),
            cohere_key=os.getenv("COHERE_API_KEY", ""),
            fal_key=os.getenv("FAL_API_KEY", ""),
            google_key=os.getenv("GOOGLE_API_KEY", ""),
        )

    @classmethod
    def get(cls) -> "Config":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def validate(self) -> bool:
        """Validate that all required configuration values are present."""
        required_fields = [
            (self.discord.token, "Discord token is missing"),
            (self.discord.secret, "Discord secret is missing"),
            (self.discord.owner_id, "Discord owner ID is missing"),
            (self.database.session_url, "Database session URL is missing"),
        ]

        for value, error_message in required_fields:
            if not value:
                raise ValueError(error_message)

        return True
