import asyncio
import sys
from src.core.client import DiscordBot
from src.core.config import config
from src.utils.logging import get_logger

logger = get_logger()


async def main():
    """Main entry point for the Discord bot."""
    try:
        # Create and start the bot
        bot = DiscordBot()
        async with bot:
            await bot.start(config.DISCORD_TOKEN)

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        # Ensure required directories exist
        config.ensure_directories()

        # Run the bot
        asyncio.run(main())

    except KeyboardInterrupt:
        logger.info("Bot shutdown by user")
        sys.exit(0)

    except Exception as e:
        logger.critical(f"Unhandled exception: {str(e)}")
        sys.exit(1)
