# ============================================================
# STRAW HAT LEVELING COMMANDS
# ============================================================

import discord

from discord import app_commands

from discord.ext import commands
from config.xp_config import get_level_title
from config.banners import BOUNTY_RANK_BANNER
from services.xp_service import (
    get_user_xp,
    get_user_rank,
    get_leaderboard,
    calculate_progress,

    get_xp_settings,
    update_xp_setting,

    add_ignored_channel,
    remove_ignored_channel,
    get_ignored_channels,

    add_level_reward,
    remove_level_reward,
    get_level_rewards,
)


def get_level_title(level: int) -> str:
    """Return a title based on the provided level."""

    level = max(0, int(level))

    if level < 5:
        return "Deckhand"
    if level < 10:
        return "Sailor"
    if level < 20:
        return "Crewmate"
    if level < 35:
        return "Veteran"
    if level < 60:
        return "Captain's Ace"
    if level < 100:
        return "Pirate King"
    return "Yonko"


# ============================================================
# PUBLIC LEVELING COMMANDS
# ============================================================

class Leveling(commands.Cog):
    """
    Public commands related to XP and levels.
    """

    def __init__(self, bot):
        self.bot = bot


    # ========================================================
    # /rank
    # ========================================================
    
    @app_commands.command(
        name="rank",
        description="View your Straw Hat Bounty rank."
    )
    @app_commands.describe(
        member="The member whose Bounty rank you want to view."
    )
    async def rank(
        self,
        interaction: discord.Interaction,
        member: discord.Member | None = None
    ):
    
        # ----------------------------------------------------
        # Server-only command
        # ----------------------------------------------------
    
        if interaction.guild is None:
    
            await interaction.response.send_message(
                "This command can only be used inside a server.",
                ephemeral=True
            )
    
            return
    
    
        # ----------------------------------------------------
        # Default to command user
        # ----------------------------------------------------
    
        member = member or interaction.user
    
    
        # ----------------------------------------------------
        # Get Bounty information
        # ----------------------------------------------------
    
        bounty, level = get_user_xp(
            interaction.guild.id,
            member.id
        )
    
    
        # ----------------------------------------------------
        # Get server rank
        # ----------------------------------------------------
    
        server_rank = get_user_rank(
            interaction.guild.id,
            member.id
        )
    
        if server_rank is None:
            server_rank = "Unranked"
    
    
        # ----------------------------------------------------
        # Calculate progress
        # ----------------------------------------------------
    
        (
            progress_bounty,
            required_bounty,
            percentage
        ) = calculate_progress(
            bounty,
            level
        )
    
    
        # ----------------------------------------------------
        # Build symbolic progress bar
        # ----------------------------------------------------
    
        total_symbols = 10
    
        filled_symbols = int(
            percentage / 100 * total_symbols
        )
    
        filled_symbols = max(
            0,
            min(
                total_symbols,
                filled_symbols
            )
        )
    
        empty_symbols = (
            total_symbols - filled_symbols
        )
    
        progress_bar = (
            "◆" * filled_symbols
            + "◇" * empty_symbols
        )
    
    
        # ----------------------------------------------------
        # Get Straw Hat title
        # ----------------------------------------------------
    
        title = get_level_title(level)
    
    
        # ----------------------------------------------------
        # Get member's highest role
        # ----------------------------------------------------
    
        role = member.top_role
    
        if role.is_default():
            role_display = "No special role"
        else:
            role_display = role.mention
    
    
        # ====================================================
        # BANNER EMBED
        # ====================================================
    
        banner_embed = discord.Embed(
            color=discord.Color.from_rgb(
                220,
                38,
                38
            )
        )
    
        banner_embed.set_image(
            url=BOUNTY_RANK_BANNER
        )
    
    
        # ----------------------------------------------------
        # Send banner first
        # ----------------------------------------------------
    
        await interaction.response.send_message(
            embed=banner_embed,
            ephemeral=True
        )
    
    
        # ====================================================
        # RANK EMBED
        # ====================================================
    
        embed = discord.Embed(
            title="☠️ STRAW HAT BOUNTY",
            color=discord.Color.from_rgb(
                220,
                38,
                38
            )
        )
    
        embed.description = (
            f"### {member.display_name}\n"
            f"**{title}**"
        )
    
    
        embed.add_field(
            name="☠️ Bounty",
            value=f"**{bounty:,} Berries**",
            inline=True
        )
    
        embed.add_field(
            name="🏆 Server Rank",
            value=f"**#{server_rank}**",
            inline=True
        )
    
        embed.add_field(
            name="⚔️ Level",
            value=f"**Level {level}**",
            inline=True
        )
    
    
        embed.add_field(
            name="Progress to Next Level",
            value=(
                f"{progress_bar}\n"
                f"`{progress_bounty:,} / "
                f"{required_bounty:,} Berries` "
                f"to Level {level + 1}"
            ),
            inline=False
        )
    
    
        embed.add_field(
            name="🎖️ Role",
            value=role_display,
            inline=False
        )
    
    
        embed.set_footer(
            text="Straw Hat • Discord Bot"
        )
    
    
        # ----------------------------------------------------
        # Send rank embed
        # ----------------------------------------------------
    
        await interaction.followup.send(
            embed=embed,
            ephemeral=True
        )
        
    # ========================================================
    # /leaderboard
    # ========================================================
    
    @app_commands.command(
        name="leaderboard",
        description="View the Straw Hat Bounty Board."
    )
    async def leaderboard(
        self,
        interaction: discord.Interaction
    ):
    
        if interaction.guild is None:
    
            await interaction.response.send_message(
                "This command can only be used inside a server.",
                ephemeral=True
            )
    
            return
    
    
        # ----------------------------------------------------
        # Get top 10 users
        # ----------------------------------------------------
    
        results = get_leaderboard(
            interaction.guild.id,
            limit=10
        )
    
    
        # ====================================================
        # BOUNTY BOARD EMBED
        # ====================================================
    
        embed = discord.Embed(
            title="🏆 STRAW HAT BOUNTY BOARD",
            description=(
                "The highest Bounties in the Straw Hat crew."
            ),
            color=discord.Color.from_rgb(
                220,
                38,
                38
            )
        )
    
    
        if not results:
    
            embed.description = (
                "No crew members have earned Berries yet."
            )
    
        else:
    
            medals = {
                1: "🥇",
                2: "🥈",
                3: "🥉"
            }
    
            lines = []
    
    
            for index, (
                user_id,
                bounty,
                level
            ) in enumerate(
                results,
                start=1
            ):
    
                member = (
                    interaction.guild.get_member(
                        user_id
                    )
                )
    
    
                if member:
    
                    name = member.display_name
    
                else:
    
                    name = f"User {user_id}"
    
    
                prefix = medals.get(
                    index,
                    f"**{index}.**"
                )
    
    
                title = get_level_title(
                    level
                )
    
    
                lines.append(
                    f"{prefix} **{name}**\n"
                    f"{title} • Level {level} • "
                    f"☠️ {bounty:,} Berries"
                )
    
    
            embed.description = "\n\n".join(
                lines
            )
    
    
        # ----------------------------------------------------
        # Find current user's position
        # ----------------------------------------------------
    
        user_rank = get_user_rank(
            interaction.guild.id,
            interaction.user.id
        )
    
    
        if user_rank is not None:
    
            user_bounty, user_level = get_user_xp(
                interaction.guild.id,
                interaction.user.id
            )
    
    
            embed.add_field(
                name="⚓ Your Position",
                value=(
                    f"**#{user_rank}**\n"
                    f"Level {user_level}\n"
                    f"☠️ {user_bounty:,} Berries"
                ),
                inline=False
            )
    
    
        embed.set_footer(
            text="Straw Hat • Discord Bot"
        )
    
    
        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

# ============================================================
# XP ADMINISTRATION GROUP
# ============================================================

class XPConfig(commands.GroupCog, group_name="xp"):
    """
    Administrator commands for configuring the XP system.
    """

    def __init__(self, bot):
        self.bot = bot


    # ========================================================
    # /xp settings
    # ========================================================

    @app_commands.command(
        name="settings",
        description="View XP settings."
    )
    @app_commands.default_permissions(
        manage_guild=True
    )
    async def settings(
        self,
        interaction: discord.Interaction
    ):

        (
            enabled,
            min_xp,
            max_xp,
            cooldown,
            levelup_channel_id
        ) = get_xp_settings(
            interaction.guild.id
        )


        status = (
            "🟢 Enabled"
            if enabled
            else "🔴 Disabled"
        )


        if levelup_channel_id:

            channel = (
                interaction.guild.get_channel(
                    levelup_channel_id
                )
            )

            bounty_channel = (
                channel.mention
                if channel
                else "Channel not found"
            )

        else:

            bounty_channel = "Not configured"


        ignored_channels = (
            get_ignored_channels(
                interaction.guild.id
            )
        )


        embed = discord.Embed(
            title="⚙️ STRAW HAT BOUNTY SETTINGS",
            color=discord.Color.from_rgb(
                220,
                38,
                38
            )
        )


        embed.add_field(
            name="Status",
            value=status,
            inline=True
        )

        embed.add_field(
            name="🪙 Bounty Range",
            value=f"{min_xp}–{max_xp} Berries",
            inline=True
        )

        embed.add_field(
            name="Cooldown",
            value=f"{cooldown} seconds",
            inline=True
        )

        embed.add_field(
            name="📢 Bounty Channel",
            value=bounty_channel,
            inline=False
        )

        embed.add_field(
            name="Ignored Channels",
            value=str(
                len(ignored_channels)
            ),
            inline=True
        )

        embed.set_footer(
            text="Straw Hat • Discord Bot"
        )


        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


    # ========================================================
    # /xp enable
    # ========================================================

    @app_commands.command(
        name="enable",
        description="Enable the XP system."
    )
    @app_commands.default_permissions(
        manage_guild=True
    )
    async def enable(
        self,
        interaction: discord.Interaction
    ):

        update_xp_setting(
            interaction.guild.id,
            "enabled",
            1
        )


        await interaction.response.send_message(
            "🟢 The Straw Hat XP system is now enabled.",
            ephemeral=True
        )


    # ========================================================
    # /xp disable
    # ========================================================

    @app_commands.command(
        name="disable",
        description="Disable the XP system."
    )
    @app_commands.default_permissions(
        manage_guild=True
    )
    async def disable(
        self,
        interaction: discord.Interaction
    ):

        update_xp_setting(
            interaction.guild.id,
            "enabled",
            0
        )


        await interaction.response.send_message(
            "🔴 The Straw Hat XP system is now disabled.",
            ephemeral=True
        )


    # ========================================================
    # /xp range
    # ========================================================

    @app_commands.command(
        name="range",
        description="Set XP earned per eligible message."
    )
    @app_commands.describe(
        minimum="Minimum XP.",
        maximum="Maximum XP."
    )
    @app_commands.default_permissions(
        manage_guild=True
    )
    async def range(
        self,
        interaction: discord.Interaction,
        minimum: app_commands.Range[int, 1, 1000],
        maximum: app_commands.Range[int, 1, 1000]
    ):

        if minimum > maximum:

            await interaction.response.send_message(
                "⚠️ Minimum XP cannot be greater than maximum XP.",
                ephemeral=True
            )

            return


        update_xp_setting(
            interaction.guild.id,
            "min_xp",
            minimum
        )

        update_xp_setting(
            interaction.guild.id,
            "max_xp",
            maximum
        )


        await interaction.response.send_message(
            f"🟢 XP range changed to "
            f"**{minimum}–{maximum} XP**.",
            ephemeral=True
        )


    # ========================================================
    # /xp cooldown
    # ========================================================

    @app_commands.command(
        name="cooldown",
        description="Set the XP cooldown."
    )
    @app_commands.describe(
        seconds="Cooldown in seconds."
    )
    @app_commands.default_permissions(
        manage_guild=True
    )
    async def cooldown(
        self,
        interaction: discord.Interaction,
        seconds: app_commands.Range[int, 1, 3600]
    ):

        update_xp_setting(
            interaction.guild.id,
            "cooldown",
            seconds
        )


        await interaction.response.send_message(
            f"🟢 XP cooldown set to "
            f"**{seconds} seconds**.",
            ephemeral=True
        )


    # ========================================================
    # /xp channel
    # ========================================================

    @app_commands.command(
        name="channel",
        description="Set the level-up announcement channel."
    )
    @app_commands.describe(
        channel="Channel where level-ups are announced."
    )
    @app_commands.default_permissions(
        manage_guild=True
    )
    async def channel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):

        update_xp_setting(
            interaction.guild.id,
            "levelup_channel_id",
            channel.id
        )


        await interaction.response.send_message(
            f"🟢 Level-up announcements will now "
            f"appear in {channel.mention}.",
            ephemeral=True
        )


    # ========================================================
    # /xp ignore
    # ========================================================

    @app_commands.command(
        name="ignore",
        description="Disable XP in a channel."
    )
    @app_commands.describe(
        channel="Channel to ignore."
    )
    @app_commands.default_permissions(
        manage_guild=True
    )
    async def ignore(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):

        add_ignored_channel(
            interaction.guild.id,
            channel.id
        )


        await interaction.response.send_message(
            f"🟢 XP will no longer be awarded "
            f"in {channel.mention}.",
            ephemeral=True
        )


    # ========================================================
    # /xp unignore
    # ========================================================

    @app_commands.command(
        name="unignore",
        description="Allow XP in a channel again."
    )
    @app_commands.default_permissions(
        manage_guild=True
    )
    async def unignore(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):

        remove_ignored_channel(
            interaction.guild.id,
            channel.id
        )


        await interaction.response.send_message(
            f"🟢 XP can now be earned in "
            f"{channel.mention}.",
            ephemeral=True
        )


    # ========================================================
    # /xp ignored
    # ========================================================

    @app_commands.command(
        name="ignored",
        description="View channels ignored by XP."
    )
    @app_commands.default_permissions(
        manage_guild=True
    )
    async def ignored(
        self,
        interaction: discord.Interaction
    ):

        channel_ids = get_ignored_channels(
            interaction.guild.id
        )


        if not channel_ids:

            description = (
                "No channels are currently ignored."
            )

        else:

            lines = []


            for channel_id in channel_ids:

                channel = (
                    interaction.guild.get_channel(
                        channel_id
                    )
                )


                if channel:

                    lines.append(
                        channel.mention
                    )


            description = (
                "\n".join(lines)
                if lines
                else "No valid channels found."
            )


        embed = discord.Embed(
            title="🚫 XP IGNORED CHANNELS",
            description=description,
            color=discord.Color.from_rgb(
                234,
                179,
                8
            )
        )

        embed.set_footer(
            text="Straw Hat • Discord Bot"
        )


        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


    # ========================================================
    # /xp reward
    # ========================================================

    @app_commands.command(
        name="reward",
        description="Set a role reward for a level."
    )
    @app_commands.describe(
        level="Level at which the role is awarded.",
        role="Discord role to award."
    )
    @app_commands.default_permissions(
        manage_guild=True
    )
    async def reward(
        self,
        interaction: discord.Interaction,
        level: app_commands.Range[int, 1, 1000],
        role: discord.Role
    ):

        bot_member = interaction.guild.me


        # ----------------------------------------------------
        # Check role hierarchy
        # ----------------------------------------------------

        if role >= bot_member.top_role:

            await interaction.response.send_message(
                "⚠️ I cannot assign that role because "
                "it is higher than or equal to my highest role.",
                ephemeral=True
            )

            return


        add_level_reward(
            interaction.guild.id,
            level,
            role.id
        )


        await interaction.response.send_message(
            f"🟢 {role.mention} will be awarded "
            f"at **Level {level}**.",
            ephemeral=True
        )


    # ========================================================
    # /xp remove-reward
    # ========================================================

    @app_commands.command(
        name="remove-reward",
        description="Remove a level role reward."
    )
    @app_commands.describe(
        level="Level whose reward should be removed."
    )
    @app_commands.default_permissions(
        manage_guild=True
    )
    async def remove_reward(
        self,
        interaction: discord.Interaction,
        level: app_commands.Range[int, 1, 1000]
    ):

        remove_level_reward(
            interaction.guild.id,
            level
        )


        await interaction.response.send_message(
            f"🟢 Reward for Level {level} removed.",
            ephemeral=True
        )


    # ========================================================
    # /xp rewards
    # ========================================================

    @app_commands.command(
        name="rewards",
        description="View configured level rewards."
    )
    @app_commands.default_permissions(
        manage_guild=True
    )
    async def rewards(
        self,
        interaction: discord.Interaction
    ):

        results = get_level_rewards(
            interaction.guild.id
        )


        embed = discord.Embed(
            title="🎁 STRAW HAT LEVEL REWARDS",
            color=discord.Color.from_rgb(
                220,
                38,
                38
            )
        )


        if not results:

            embed.description = (
                "No level rewards have been configured."
            )

        else:

            lines = []


            for level, role_id in results:

                role = interaction.guild.get_role(
                    role_id
                )


                if role:

                    lines.append(
                        f"**Level {level}** → "
                        f"{role.mention}"
                    )

                else:

                    lines.append(
                        f"**Level {level}** → "
                        "Role not found"
                    )


            embed.description = "\n".join(
                lines
            )


        embed.set_footer(
            text="Straw Hat • Discord Bot"
        )


        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


    @app_commands.command(
        name="bounty-channel",
        description="Set the channel for public bounty announcements."
    )
    @app_commands.describe(
        channel="The channel where bounty level-up posters will be sent."
    )
    @app_commands.default_permissions(
        manage_guild=True
    )
    async def bounty_channel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):
    
        # --------------------------------------------------------
        # Server-only command
        # --------------------------------------------------------
    
        if interaction.guild is None:
    
            await interaction.response.send_message(
                "This command can only be used inside a server.",
                ephemeral=True
            )
    
            return
    
        # --------------------------------------------------------
        # Extra permission check
        # --------------------------------------------------------
    
        if not interaction.user.guild_permissions.manage_guild:
    
            await interaction.response.send_message(
                "❌ You need the **Manage Server** permission "
                "to configure the Bounty Channel.",
                ephemeral=True
            )
    
            return
    
        # --------------------------------------------------------
        # Make sure the bot can send messages there.
        # --------------------------------------------------------
    
        bot_member = interaction.guild.me
    
        if bot_member is None:
    
            await interaction.response.send_message(
                "❌ I couldn't verify my permissions.",
                ephemeral=True
            )
    
            return
    
        permissions = channel.permissions_for(
            bot_member
        )
    
        if not permissions.view_channel:
    
            await interaction.response.send_message(
                f"❌ I cannot see {channel.mention}.",
                ephemeral=True
            )
    
            return
    
        if not permissions.send_messages:
    
            await interaction.response.send_message(
                f"❌ I cannot send messages in {channel.mention}.",
                ephemeral=True
            )
    
            return
    
        # --------------------------------------------------------
        # Save Bounty Channel.
        # --------------------------------------------------------
    
        update_xp_setting(
            interaction.guild.id,
            "levelup_channel_id",
            channel.id
        )
    
        # --------------------------------------------------------
        # Confirmation
        # --------------------------------------------------------
    
        embed = discord.Embed(
            title="☠️ BOUNTY CHANNEL UPDATED",
            description=(
                f"Public bounty announcements will now "
                f"be sent to {channel.mention}."
            ),
            color=discord.Color.from_rgb(
                34,
                197,
                94
            )
        )
    
        embed.set_footer(
            text="Straw Hat • Discord Bot"
        )
    
        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )
# ============================================================
# EXTENSION SETUP
# ============================================================

async def setup(bot):
    """
    Load both leveling Cogs.
    """

    await bot.add_cog(
        Leveling(bot)
    )

    await bot.add_cog(
        XPConfig(bot)
    )