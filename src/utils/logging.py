import logging
from typing import Optional
from colorama import init, Fore, Style
from src.core.config import settings

init(autoreset=True)


class ColorLogger:
    COLORS = {
        "DEBUG": Fore.BLUE,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.RED + Style.BRIGHT,
    }

    def __init__(self, name: str, level: Optional[str] = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level or settings.log_level)

        # Create console handler if none exists
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def _log(self, level: str, message: str, *args, **kwargs):
        color = self.COLORS.get(level, "")
        formatted_message = f"{color}{message}{Style.RESET_ALL}"
        getattr(self.logger, level.lower())(formatted_message, *args, **kwargs)

    def debug(self, message: str, *args, **kwargs):
        self._log("DEBUG", message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        self._log("INFO", message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        self._log("WARNING", message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        self._log("ERROR", message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs):
        self._log("CRITICAL", message, *args, **kwargs)

    def getChild(self, suffix: str) -> "ColorLogger":
        """
        Create a child logger with the given suffix.
        This mirrors the behavior of the standard Python logger's getChild method.
        """
        return ColorLogger(f"{self.logger.name}.{suffix}")
