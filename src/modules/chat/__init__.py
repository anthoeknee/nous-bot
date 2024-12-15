# src/modules/chat/__init__.py
from discord.ext import commands
from src.services.redis import RedisInterface
from src.services.llm import LLMService
from .core import ChatModule


async def setup(bot: commands.Bot, redis: RedisInterface, llm: LLMService) -> None:
    """Set up the chat module"""
    chat_module = ChatModule(bot, redis, llm)

    @bot.event
    async def on_message(message):
        # Process commands first
        await bot.process_commands(message)

        # Then handle chat responses
        response = await chat_module.process_message(message)
        if response:
            await message.channel.send(response)
