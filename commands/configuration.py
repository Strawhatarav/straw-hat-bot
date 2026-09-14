import discord
from discord import app_commands
from discord.ext import commands

from database.database import (
    create_guild_config,
    update_welcome_channel,
    update_goodbye_channel,
    update_default_role,
    update_welcome_message,
    update_goodbye_message,
    get_guild_config,
)


class Configuration(
    commands.GroupCog,
    group_name="config",
    group_description="Configure Straw Hat for this server."
):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="welcome-channel",
        description="Set the channel for welcome messages."
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def welcome_channel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):

        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True
            )
            return

        create_guild_config(guild.id)

        update_welcome_channel(
            guild.id,
            channel.id
        )

        await interaction.response.send_message(
            f"✅ Welcome messages will now be sent in {channel.mention}.",
            ephemeral=True
        )

    @app_commands.command(
        name="goodbye-channel",
        description="Set the channel for goodbye messages."
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def goodbye_channel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):

        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True
            )
            return

        create_guild_config(guild.id)

        update_goodbye_channel(
            guild.id,
            channel.id
        )

        await interaction.response.send_message(
            f"✅ Goodbye messages will now be sent in {channel.mention}.",
            ephemeral=True
        )

    @app_commands.command(
        name="defaultrole",
        description="Set the role automatically given to new members."
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def defaultrole(
        self,
        interaction: discord.Interaction,
        role: discord.Role
    ):

        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True
            )
            return

        create_guild_config(guild.id)

        update_default_role(
            guild.id,
            role.id
        )

        await interaction.response.send_message(
            f"✅ New members will receive {role.mention}.",
            ephemeral=True
        )

    @app_commands.command(
        name="welcome-message",
        description="Set the custom welcome message."
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def welcome_message(
        self,
        interaction: discord.Interaction,
        message: str
    ):

        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True
            )
            return

        create_guild_config(guild.id)

        update_welcome_message(
            guild.id,
            message
        )

        await interaction.response.send_message(
            "✅ Welcome message updated.",
            ephemeral=True
        )

    @app_commands.command(
        name="goodbye-message",
        description="Set the custom goodbye message."
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def goodbye_message(
        self,
        interaction: discord.Interaction,
        message: str
    ):

        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True
            )
            return

        create_guild_config(guild.id)

        update_goodbye_message(
            guild.id,
            message
        )

        await interaction.response.send_message(
            "✅ Goodbye message updated.",
            ephemeral=True
        )

    @app_commands.command(
        name="view",
        description="View Straw Hat's current server configuration."
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def view(
        self,
        interaction: discord.Interaction
    ):

        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True
            )
            return

        create_guild_config(guild.id)

        config = get_guild_config(guild.id)

        (
            guild_id,
            welcome_channel_id,
            goodbye_channel_id,
            default_role_id,
            welcome_message,
            goodbye_message
        ) = config

        welcome_channel = (
            guild.get_channel(welcome_channel_id)
            if welcome_channel_id
            else None
        )

        goodbye_channel = (
            guild.get_channel(goodbye_channel_id)
            if goodbye_channel_id
            else None
        )

        default_role = (
            guild.get_role(default_role_id)
            if default_role_id
            else None
        )

        embed = discord.Embed(
            title="⚙️ Straw Hat Configuration",
            description=f"Configuration for **{guild.name}**"
        )

        embed.add_field(
            name="👋 Welcome Channel",
            value=(
                welcome_channel.mention
                if welcome_channel
                else "Not configured"
            ),
            inline=False
        )

        embed.add_field(
            name="👋 Goodbye Channel",
            value=(
                goodbye_channel.mention
                if goodbye_channel
                else "Not configured"
            ),
            inline=False
        )

        embed.add_field(
            name="🎭 Default Role",
            value=(
                default_role.mention
                if default_role
                else "Not configured"
            ),
            inline=False
        )

        embed.add_field(
            name="📝 Welcome Message",
            value=welcome_message or "Not configured",
            inline=False
        )

        embed.add_field(
            name="📝 Goodbye Message",
            value=goodbye_message or "Not configured",
            inline=False
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Configuration(bot))