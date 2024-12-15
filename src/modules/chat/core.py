# src/modules/chat/core.py
from typing import Optional
from discord.ext import commands
import discord
from src.services.redis import RedisInterface
from src.services.llm import LLMService
from .events import ChatEvents
from .memory.short_term import ShortTermMemory


class ChatModule:
    """Handles chat interactions and responses"""

    def __init__(self, bot: commands.Bot, redis: RedisInterface, llm: LLMService):
        self.bot = bot
        self.redis = redis
        self.llm = llm
        self.memory = ShortTermMemory(max_messages=50, ttl=6300)  # 1h45m in seconds
        self.events = ChatEvents(bot, self)

    async def process_message(self, message: discord.Message) -> Optional[str]:
        """Process incoming message and generate response if needed"""
        if not self.events.should_respond(message):
            return None

        # Get conversation context
        context = self.memory.get_context(message.channel.id)

        # Prepare prompt with context
        prompt = self._build_prompt(message, context)

        try:
            # Generate response using LLM
            response = await self.llm.get_provider().generate_text(prompt)

            # Update conversation memory
            self.memory.add_message(
                channel_id=message.channel.id,
                user_id=message.author.id,
                content=message.content,
                is_bot=False,
            )
            self.memory.add_message(
                channel_id=message.channel.id,
                user_id=self.bot.user.id,
                content=response,
                is_bot=True,
            )

            return response
        except Exception as e:
            return f"I apologize, but I encountered an error: {str(e)}"

    def _build_prompt(self, message: discord.Message, context: list[dict]) -> str:
        """Build prompt with conversation context"""
        prompt_parts = [
            "You are a helpful and friendly Discord bot. ",
            "Previous conversation:\n",
        ]

        # Add context messages
        for msg in context:
            speaker = "Bot" if msg["is_bot"] else "User"
            prompt_parts.append(f"{speaker}: {msg['content']}\n")

        # Add current message
        prompt_parts.append(f"User: {message.content}\n")
        prompt_parts.append("Bot: ")

        return "".join(prompt_parts)
