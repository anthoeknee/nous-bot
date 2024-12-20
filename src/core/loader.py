import os
import importlib
from typing import List
from discord.ext import commands

from src.utils import ColorLogger
from src.core.config import settings

logger = ColorLogger("CogLoader", settings.log_level)


class CogLoader:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cogs_path = os.path.join("src", "cogs")
        self.loaded_cogs: List[str] = []

    async def _load_cog(self, module_path: str) -> bool:
        """
        Load a single cog module.
        Returns True if successful, False otherwise.
        """
        try:
            module = importlib.import_module(module_path)
            if hasattr(module, "setup"):
                await self.bot.load_extension(module_path)
                self.loaded_cogs.append(module_path)
                logger.info(f"Loaded cog: {module_path}")
                return True
            else:
                logger.warning(f"Skipped {module_path}: no setup function found")
                return False
        except Exception as e:
            logger.error(f"Failed to load cog {module_path}: {str(e)}")
            return False

    async def _unload_cog(self, module_path: str) -> bool:
        """
        Unload a single cog module.
        Returns True if successful, False otherwise.
        """
        try:
            await self.bot.unload_extension(module_path)
            self.loaded_cogs.remove(module_path)
            logger.info(f"Unloaded cog: {module_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to unload cog {module_path}: {str(e)}")
            return False

    async def reload_cog(self, module_path: str) -> bool:
        """
        Reload a specific cog module.
        Returns True if successful, False otherwise.
        """
        if module_path in self.loaded_cogs:
            await self._unload_cog(module_path)
        return await self._load_cog(module_path)

    def _get_cog_modules(self) -> List[str]:
        """
        Discover all potential cog modules in the cogs directory.
        """
        cog_modules = []

        for root, _, files in os.walk(self.cogs_path):
            for file in files:
                if file.endswith(".py") and not file.startswith("_"):
                    # Convert file path to module path
                    file_path = os.path.join(root, file)
                    module_path = os.path.splitext(file_path)[0].replace(os.sep, ".")
                    cog_modules.append(module_path)

        return cog_modules

    async def load_all_cogs(self) -> None:
        """
        Discover and load all cogs in the cogs directory.
        """
        cog_modules = self._get_cog_modules()

        for module_path in cog_modules:
            await self._load_cog(module_path)

        logger.info(f"Loaded {len(self.loaded_cogs)} cogs")

    async def reload_all_cogs(self) -> None:
        """
        Reload all currently loaded cogs.
        """
        currently_loaded = self.loaded_cogs.copy()
        for module_path in currently_loaded:
            await self.reload_cog(module_path)

    def get_loaded_cogs(self) -> List[str]:
        """
        Return a list of currently loaded cog modules.
        """
        return self.loaded_cogs.copy()
