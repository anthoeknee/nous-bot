from discord.ext import commands
from src.core import settings
from src.core import ProcessManager
from src.core import CogLoader


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=settings.discord_command_prefix)
        self.process_manager = ProcessManager.initialize()
        self.cog_loader = CogLoader(self)

    async def setup_hook(self):
        await self.cog_loader.load_all_cogs()

    async def close(self):
        self.process_manager.stop()
        await super().close()
