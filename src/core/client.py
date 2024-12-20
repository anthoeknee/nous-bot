from discord.ext import commands
import discord
from src.core.config import settings
from src.utils.logging import ColorLogger


# Example placeholders for these classes:
class ProcessManager:
    @staticmethod
    def initialize():
        return ProcessManager()

    def stop(self):
        pass


class CogLoader:
    def __init__(self, bot):
        self.bot = bot

    async def load_all_cogs(self):
        pass


class Bot(commands.Bot):
    def __init__(self):
        # Add settings as instance variable
        self.settings = settings

        # Use ColorLogger instead of basic logging
        self.logger = ColorLogger("discord")

        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix=settings.discord_command_prefix, intents=intents
        )

        self.process_manager = ProcessManager.initialize()
        self.cog_loader = CogLoader(self)

    async def setup_hook(self):
        self.logger.info("Bot is setting up...")
        try:
            await self.cog_loader.load_all_cogs()
            self.logger.info("Cogs loaded successfully.")
        except Exception as e:
            self.logger.error(f"Failed to load cogs: {e}")

    async def on_ready(self):
        self.logger.info(f"Logged in as {self.user.name} (ID: {self.user.id})")
        self.logger.info("------")

    async def close(self):
        self.logger.info("Bot is shutting down...")
        self.process_manager.stop()
        await super().close()
