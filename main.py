import asyncio
from src.core.client import Bot
import logging

# Set up basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    bot = None
    try:
        bot = Bot()
        await bot.start(bot.settings.discord_token)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}", exc_info=True)
    finally:
        if bot is not None:
            await bot.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}", exc_info=True)
        raise
