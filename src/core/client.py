import discord
from discord.ext import commands
from src.core.config import config
from src.core.loader import ModuleLoader
from src.services import get_services
from src.utils.logging import get_logger

logger = get_logger()


class DiscordBot(commands.Bot):
    """Custom Discord bot client with enhanced functionality."""

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix=config.DISCORD_COMMAND_PREFIX,
            intents=intents,
            help_command=None,  # Disable default help command
        )

        self.module_loader = ModuleLoader()
        self.owner_id = config.DISCORD_OWNER_ID

    async def setup_hook(self) -> None:
        """Initialize bot services and modules."""
        try:
            # Initialize services
            service_manager = get_services()
            await service_manager.initialize_services()

            # Load all modules
            await self.module_loader.load_all(self)

            logger.info("Bot setup completed successfully")

        except Exception as e:
            logger.error(f"Failed to setup bot: {str(e)}")
            raise

    async def on_ready(self):
        """Called when the bot is ready and connected."""
        logger.info(f"Logged in as {self.user.name} ({self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guilds")

        # Set custom status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{config.DISCORD_COMMAND_PREFIX}help",
            )
        )

    async def on_command_error(self, ctx: commands.Context, error: Exception):
        """Global error handler for commands."""
        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command.")
            return

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument: {error.param.name}")
            return

        # Log unexpected errors
        logger.error(f"Command error in {ctx.command}: {str(error)}")
        await ctx.send("An unexpected error occurred. Please try again later.")

    async def close(self):
        """Cleanup before shutdown."""
        try:
            # Stop all services
            service_manager = get_services()
            await service_manager.stop_all()

            logger.info("Bot shutdown completed")

        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")

        finally:
            await super().close()
