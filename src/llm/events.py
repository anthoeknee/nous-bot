"""
events.py implements a simple Discord.py Cog that listens for messages and
calls our LLMCore to handle the conversation.
"""

import discord
from discord.ext import commands

from src.llm.core import LLMCore
from src.services.registry import ServiceRegistry


class LLMEventsCog(commands.Cog):
    """
    Cog that integrates with Discord.py. On receiving a message, it delegates to the LLMCore.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cache = ServiceRegistry.get_instance("cache")
        self.active_sessions = {}
        self.logger = self.bot.logger.getChild("llm")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Basic checks for ignoring own messages or system messages
        if message.author == self.bot.user or message.author.bot:
            return

        # Check if the message is a command using discord.py's command processing
        ctx = await self.bot.get_context(message)
        if ctx.valid:  # This will be True for both slash and prefix commands
            return

        try:
            # Always process DM messages
            is_dm = isinstance(message.channel, discord.DMChannel)
            # Check if message mentions the bot or is a reply to the bot's message
            is_bot_mention = self.bot.user in message.mentions
            is_bot_reply = (
                message.reference
                and message.reference.resolved
                and message.reference.resolved.author == self.bot.user
            )

            # Only process if it's a DM or the bot was mentioned/replied to
            if not (is_dm or is_bot_mention or is_bot_reply):
                return

            session_id = f"discord_session_{message.channel.id}"
            if session_id not in self.active_sessions:
                self.active_sessions[session_id] = LLMCore(session_id, self.cache)

            llm_core = self.active_sessions[session_id]

            # Construct a conversation message dict
            # If there's an attachment that is an image, we treat it as an image_url message
            if message.attachments:
                for attachment in message.attachments:
                    if any(
                        attachment.filename.lower().endswith(ext)
                        for ext in [".png", ".jpg", ".jpeg", ".gif"]
                    ):
                        user_msg = {
                            "content": f"User sent an image: {attachment.url}",
                            "type": "image_url",
                            "url": attachment.url,
                        }
                        response_text = await llm_core.process_user_message(user_msg)
                        if response_text:
                            await message.channel.send(response_text)
                        return

            # Otherwise, treat as a normal text message
            user_msg = {"content": message.content, "type": "text"}
            response_text = await llm_core.process_user_message(user_msg)
            if response_text:
                await message.channel.send(response_text)

        except Exception as e:
            self.logger.error(f"Error processing message: {e}", exc_info=True)
            await message.channel.send(
                "Sorry, I encountered an error processing your message."
            )


async def setup(bot):
    """
    Required setup function for Discord.py to add this Cog.
    """
    await bot.add_cog(LLMEventsCog(bot))
