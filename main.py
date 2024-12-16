import asyncio
import sys
import time
from src.core.client import DiscordBot
from src.core.config import config
from src.utils.logging import get_logger
from src.services import get_services

logger = get_logger()


async def main():
    """Main entry point for the Discord bot."""
    start_time = time.time()

    try:
        # Create bot and initialize services once
        bot = DiscordBot()
        await bot.setup_hook()

        logger.info(f"Startup completed in {time.time() - start_time:.2f}s")

        async with bot:
            await bot.start(config.DISCORD_TOKEN)

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        config.ensure_directories()
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Unhandled exception: {str(e)}")
        sys.exit(1)
