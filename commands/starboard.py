import discord

from discord import app_commands
from discord.ext import commands

from services.starboard_service import (
    create_default_settings,
    get_settings,
    update_setting
)


class Starboard(commands.GroupCog, group_name="starboard"):

    def __init__(self, bot):
        self.bot = bot


    # ========================================================
    # /starboard channel
    # ========================================================

    @app_commands.command(
        name="channel",
        description="Set the Starboard channel."
    )
    @app_commands.default_permissions(
        manage_guild=True
    )
    async def channel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):

        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(
                "❌ You need Manage Server permission.",
                ephemeral=True
            )
            return


        create_default_settings(
            interaction.guild.id
        )

        update_setting(
            interaction.guild.id,
            "channel_id",
            channel.id
        )

        update_setting(
            interaction.guild.id,
            "enabled",
            1
        )


        embed = discord.Embed(
            title="⭐ STARBOARD CHANNEL UPDATED",
            description=(
                f"Starboard messages will now be "
                f"posted in {channel.mention}."
            ),
            color=discord.Color.from_rgb(
                34,
                197,
                94
            )
        )

        embed.set_footer(
            text="Straw Hat • Starboard"
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


    # ========================================================
    # /starboard threshold
    # ========================================================

    @app_commands.command(
        name="threshold",
        description="Set the number of ⭐ reactions required."
    )
    @app_commands.default_permissions(
        manage_guild=True
    )
    async def threshold(
        self,
        interaction: discord.Interaction,
        amount: app_commands.Range[int, 1, 100]
    ):

        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(
                "❌ You need Manage Server permission.",
                ephemeral=True
            )
            return


        create_default_settings(
            interaction.guild.id
        )

        update_setting(
            interaction.guild.id,
            "threshold",
            amount
        )


        embed = discord.Embed(
            title="⭐ STARBOARD THRESHOLD UPDATED",
            description=(
                f"Messages now require **{amount} ⭐** "
                f"to enter the Starboard."
            ),
            color=discord.Color.from_rgb(
                34,
                197,
                94
            )
        )

        embed.set_footer(
            text="Straw Hat • Starboard"
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


    # ========================================================
    # /starboard settings
    # ========================================================

    @app_commands.command(
        name="settings",
        description="View Starboard configuration."
    )
    @app_commands.default_permissions(
        manage_guild=True
    )
    async def settings(
        self,
        interaction: discord.Interaction
    ):

        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(
                "❌ You need Manage Server permission.",
                ephemeral=True
            )
            return


        create_default_settings(
            interaction.guild.id
        )

        settings = get_settings(
            interaction.guild.id
        )

        channel_id = settings[1]
        threshold = settings[2]
        enabled = settings[3]


        channel_display = (
            f"<#{channel_id}>"
            if channel_id
            else "Not configured"
        )


        embed = discord.Embed(
            title="⭐ STARBOARD SETTINGS",
            color=discord.Color.from_rgb(
                37,
                99,
                235
            )
        )

        embed.add_field(
            name="Status",
            value=(
                "🟢 Enabled"
                if enabled
                else "🔴 Disabled"
            ),
            inline=True
        )

        embed.add_field(
            name="Channel",
            value=channel_display,
            inline=True
        )

        embed.add_field(
            name="Threshold",
            value=f"⭐ {threshold}",
            inline=True
        )

        embed.set_footer(
            text="Straw Hat • Starboard"
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


    # ========================================================
    # /starboard disable
    # ========================================================

    @app_commands.command(
        name="disable",
        description="Disable the Starboard."
    )
    @app_commands.default_permissions(
        manage_guild=True
    )
    async def disable(
        self,
        interaction: discord.Interaction
    ):

        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(
                "❌ You need Manage Server permission.",
                ephemeral=True
            )
            return


        create_default_settings(
            interaction.guild.id
        )

        update_setting(
            interaction.guild.id,
            "enabled",
            0
        )


        embed = discord.Embed(
            title="⭐ STARBOARD DISABLED",
            description=(
                "New messages will no longer be "
                "added to the Starboard."
            ),
            color=discord.Color.from_rgb(
                234,
                179,
                8
            )
        )

        embed.set_footer(
            text="Straw Hat • Starboard"
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(
        Starboard(bot)
    )