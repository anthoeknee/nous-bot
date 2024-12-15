from discord.ext import commands
import discord


class ChatEvents:
    """Handles chat-related event logic"""

    def __init__(self, bot: commands.Bot, chat_module):
        self.bot = bot
        self.chat_module = chat_module

    def should_respond(self, message: discord.Message) -> bool:
        """
        Determine if the bot should generate a response based on message context.

        Args:
            message: The message to evaluate

        Returns:
            bool: Whether the bot should generate a response
        """
        # Early returns for common rejection cases
        if any(
            [
                message.author.bot,  # Ignore bots
                message.content.startswith("/"),  # Ignore slash commands
                message.content.startswith(
                    self.bot.command_prefix
                ),  # Ignore prefix commands
            ]
        ):
            return False

        # Handle DMs: respond to everything except commands
        if not message.guild:
            return True

        # In servers, only respond to mentions or replies
        is_mentioned = self.bot.user in message.mentions
        is_reply_to_bot = (
            message.reference
            and message.reference.resolved
            and message.reference.resolved.author.id == self.bot.user.id
        )

        return is_mentioned or is_reply_to_bot
