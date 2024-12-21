from typing import Optional, Dict, Any, List
import discord
from discord.ext import commands
from discord import Guild, Member, Role, TextChannel, User
from .registry import ToolRegistry, ToolParameter, ParameterType

# Create registry instance for Discord API tools
discord_tools = ToolRegistry()


def setup_discord_tools(bot: commands.Bot) -> ToolRegistry:
    """Initialize Discord API tools with bot context"""

    @discord_tools.register_function(
        name="get_user_info",
        description="Get information about a Discord user by ID or username",
        parameters=[
            ToolParameter(
                name="identifier",
                type=ParameterType.STRING,
                description="User ID or username to look up",
            )
        ],
    )
    async def get_user_info(identifier: str) -> Dict[str, Any]:
        """Fetch user information by ID or username"""
        try:
            # Try to fetch by ID first
            user = None
            try:
                user_id = int(identifier)
                user = await bot.fetch_user(user_id)
            except ValueError:
                # If not an ID, search by username
                for guild in bot.guilds:
                    user = discord.utils.get(guild.members, name=identifier)
                    if user:
                        break

            if not user:
                return {"error": "User not found"}

            return {
                "id": str(user.id),
                "username": user.name,
                "display_name": user.display_name,
                "bot": user.bot,
                "created_at": str(user.created_at),
                "avatar_url": str(user.avatar.url) if user.avatar else None,
            }
        except Exception as e:
            return {"error": f"Error fetching user info: {str(e)}"}

    @discord_tools.register_function(
        name="get_server_info",
        description="Get information about a Discord server by name",
        parameters=[
            ToolParameter(
                name="server_name",
                type=ParameterType.STRING,
                description="Name of the server to look up",
            )
        ],
    )
    async def get_server_info(server_name: str) -> Dict[str, Any]:
        """Fetch server information by name"""
        try:
            guild = discord.utils.get(bot.guilds, name=server_name)
            if not guild:
                return {"error": "Server not found"}

            return {
                "id": str(guild.id),
                "name": guild.name,
                "member_count": guild.member_count,
                "owner": str(guild.owner),
                "created_at": str(guild.created_at),
                "description": guild.description,
                "roles_count": len(guild.roles),
                "channels_count": len(guild.channels),
            }
        except Exception as e:
            return {"error": f"Error fetching server info: {str(e)}"}

    @discord_tools.register_function(
        name="get_role_info",
        description="Get information about roles in a server",
        parameters=[
            ToolParameter(
                name="server_name",
                type=ParameterType.STRING,
                description="Name of the server",
            ),
            ToolParameter(
                name="role_name",
                type=ParameterType.STRING,
                description="Name of the role to look up (optional)",
                required=False,
            ),
        ],
    )
    async def get_role_info(
        server_name: str, role_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetch role information for a server"""
        try:
            guild = discord.utils.get(bot.guilds, name=server_name)
            if not guild:
                return {"error": "Server not found"}

            if role_name:
                # Get specific role
                role = discord.utils.get(guild.roles, name=role_name)
                if not role:
                    return {"error": "Role not found"}
                return {
                    "id": str(role.id),
                    "name": role.name,
                    "color": str(role.color),
                    "position": role.position,
                    "permissions": str(role.permissions),
                    "member_count": len(role.members),
                }
            else:
                # Get all roles
                return {
                    "roles": [
                        {
                            "name": role.name,
                            "member_count": len(role.members),
                            "color": str(role.color),
                        }
                        for role in guild.roles
                        if not role.is_default()
                    ]
                }
        except Exception as e:
            return {"error": f"Error fetching role info: {str(e)}"}

    @discord_tools.register_function(
        name="get_channel_info",
        description="Get information about channels in a server",
        parameters=[
            ToolParameter(
                name="server_name",
                type=ParameterType.STRING,
                description="Name of the server",
            ),
            ToolParameter(
                name="channel_name",
                type=ParameterType.STRING,
                description="Name of the channel to look up (optional)",
                required=False,
            ),
        ],
    )
    async def get_channel_info(
        server_name: str, channel_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetch channel information for a server"""
        try:
            guild = discord.utils.get(bot.guilds, name=server_name)
            if not guild:
                return {"error": "Server not found"}

            if channel_name:
                # Get specific channel
                channel = discord.utils.get(guild.channels, name=channel_name)
                if not channel:
                    return {"error": "Channel not found"}
                return {
                    "id": str(channel.id),
                    "name": channel.name,
                    "type": str(channel.type),
                    "position": channel.position,
                    "created_at": str(channel.created_at),
                    "category": str(channel.category) if channel.category else None,
                }
            else:
                # Get all channels
                return {
                    "text_channels": [
                        {"name": ch.name, "type": "text"} for ch in guild.text_channels
                    ],
                    "voice_channels": [
                        {"name": ch.name, "type": "voice"}
                        for ch in guild.voice_channels
                    ],
                    "categories": [
                        {"name": cat.name, "type": "category"}
                        for cat in guild.categories
                    ],
                }
        except Exception as e:
            return {"error": f"Error fetching channel info: {str(e)}"}

    return discord_tools
