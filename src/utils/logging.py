import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


class BotLogger:
    _instance: Optional["BotLogger"] = None

    def __init__(self):
        if BotLogger._instance is not None:
            raise RuntimeError("BotLogger is a singleton. Use BotLogger.get_logger()")

        self.logger = logging.getLogger("DiscordBot")
        self.setup_logger()

    @classmethod
    def get_logger(cls) -> logging.Logger:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance.logger

    def setup_logger(self):
        # Get configuration from environment
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        log_dir = os.getenv("LOG_DIR", "logs")

        # Create logs directory if it doesn't exist
        Path(log_dir).mkdir(parents=True, exist_ok=True)

        # Set logging level
        self.logger.setLevel(getattr(logging, log_level))

        # Create formatters
        console_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)

        # File handler with rotation
        file_handler = RotatingFileHandler(
            filename=os.path.join(log_dir, "discord_bot.log"),
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(file_formatter)

        # Add handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)


# Convenience functions
def get_logger() -> logging.Logger:
    return BotLogger.get_logger()


def debug(msg: str, *args, **kwargs):
    get_logger().debug(msg, *args, **kwargs)


def info(msg: str, *args, **kwargs):
    get_logger().info(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs):
    get_logger().warning(msg, *args, **kwargs)


def error(msg: str, *args, **kwargs):
    get_logger().error(msg, *args, **kwargs)


def critical(msg: str, *args, **kwargs):
    get_logger().critical(msg, *args, **kwargs)
