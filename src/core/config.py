from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn, validator


class ServiceConfig(BaseSettings):
    """Base configuration for services"""

    enabled: bool = True
    options: Dict[str, Any] = Field(default_factory=dict)


class DatabaseServiceConfig(ServiceConfig):
    """Database service specific configuration"""

    pool_size: int = Field(ge=1, le=100, default=10)
    pool_timeout: int = Field(ge=1, le=300, default=30)
    max_retries: int = Field(ge=0, le=10, default=3)
    retry_delay: float = Field(ge=0.1, le=60.0, default=1.0)


class CacheServiceConfig(ServiceConfig):
    """Cache service specific configuration"""

    ttl: int = Field(ge=1, default=3600)
    max_size: int = Field(ge=1, default=1000)
    enable_compression: bool = False


class Settings(BaseSettings):
    # Discord Configuration
    discord_token: str
    discord_secret: str
    discord_owner_id: int
    discord_command_prefix: str = "n!"

    # AI Provider Configurations
    xai_api_key: str
    openai_api_key: str
    groq_api_key: str
    cohere_api_key: str
    fal_api_key: str
    google_api_key: str

    # Database Configuration
    database_session_url: PostgresDsn
    database_transaction_url: PostgresDsn
    database_direct_url: PostgresDsn
    use_connection_pooling: bool = True
    database_pool_size: int = Field(ge=1, le=100)
    database_pool_timeout: int = Field(ge=1, le=300)

    # Redis Configuration
    redis_host: str
    redis_port: int = Field(ge=1, le=65535)
    redis_password: Optional[str] = None
    redis_conversation_ttl: int = Field(ge=1)

    # Logging Configuration
    log_level: str = Field(..., pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    log_dir: str = "logs"

    # Service Configurations
    services: Dict[str, Dict[str, Any]] = Field(
        default_factory=lambda: {
            "database": {
                "enabled": True,
                "options": {
                    "pool_size": 10,
                    "pool_timeout": 30,
                    "max_retries": 3,
                    "retry_delay": 1.0,
                },
            },
            "cache": {
                "enabled": True,
                "options": {"ttl": 3600, "max_size": 1000, "enable_compression": False},
            },
        }
    )

    @validator("log_level")
    def uppercase_log_level(cls, v):
        return v.upper()

    @validator("services")
    def validate_services(cls, v):
        """Validate service configurations"""
        required_services = {"database", "cache"}
        if not all(service in v for service in required_services):
            missing = required_services - set(v.keys())
            raise ValueError(f"Missing required service configurations: {missing}")
        return v

    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """Get configuration for a specific service"""
        if service_name not in self.services:
            raise ValueError(f"No configuration found for service: {service_name}")
        return self.services[service_name]

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )


# Create a global settings instance
settings = Settings()

# Usage example:
# from src.core.config import settings
# db_config = settings.get_service_config("database")
