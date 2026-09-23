# ============================================================
# STRAW HAT BOUNTY MESSAGE EVENTS
# ============================================================

import random
import time

import discord
from discord.ext import commands

from config.banners import BOUNTY_POSTER_BANNER
from config.xp_config import get_level_title
from services.xp_service import (
    add_xp,
    get_xp_settings,
    is_channel_ignored,

    get_level_reward,
)


class XPEvents(commands.Cog):
    """
    Handles Bounty-related Discord events.
    """

    def __init__(self, bot):
        self.bot = bot


        # Temporary in-memory cooldown storage.
        #
        # Format:
        # (guild_id, user_id) -> timestamp
        self.cooldowns = {}
        
    # ========================================================
    # MESSAGE EVENT
    # ========================================================

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Award Berries when a user sends an eligible message.
        """

        # ----------------------------------------------------
        # Ignore bots
        # ----------------------------------------------------

        if message.author.bot:
            return
        
        # ----------------------------------------------------
        # Ignore direct messages
        # ----------------------------------------------------

        if message.guild is None:
            return


        guild_id = message.guild.id

        user_id = message.author.id

        channel_id = message.channel.id


        # ----------------------------------------------------
        # Get Bounty settings
        # ----------------------------------------------------

        settings = get_xp_settings(guild_id)

        (
            enabled,
            min_xp,
            max_xp,
            cooldown,
            bounty_channel_id,
        ) = settings


        # ----------------------------------------------------
        # Check whether Bounty is enabled
        # ----------------------------------------------------

        if not enabled:
            return


        # ----------------------------------------------------
        # Check ignored channels
        # ----------------------------------------------------

        if is_channel_ignored(guild_id, channel_id):
            return


        # ----------------------------------------------------
        # Check cooldown
        # ----------------------------------------------------

        current_time = time.time()

        cooldown_key = (guild_id, user_id)

        last_xp_time = self.cooldowns.get(
            cooldown_key,
            0,
        )


        if current_time - last_xp_time < cooldown:
            return


        # ----------------------------------------------------
        # Start a new Bounty cooldown
        # ----------------------------------------------------

        self.cooldowns[cooldown_key] = current_time


        # ----------------------------------------------------
        # Generate random Berries
        # ----------------------------------------------------

        amount = random.randint(
            min_xp,
            max_xp,
        )


        # ----------------------------------------------------
        # Add Berries to database
        # ----------------------------------------------------

        (
            old_xp,
            new_xp,
            old_level,
            new_level,
        ) = add_xp(
            guild_id,
            user_id,
            amount,
        )


        # ----------------------------------------------------
        # Check for level-up
        # ----------------------------------------------------

        if new_level > old_level:

            await self.handle_level_up(
                message=message,
                old_level=old_level,
                new_level=new_level,
                new_bounty=new_xp,
                bounty_channel_id=bounty_channel_id,
            )


    # ========================================================
    # LEVEL-UP / BOUNTY POSTER
    # ========================================================

    async def handle_level_up(
        self,
        message: discord.Message,
        old_level: int,
        new_level: int,
        new_bounty: int,
        bounty_channel_id,
    ):
        """
        Handle level rewards and the public Bounty poster.
        """

        guild = message.guild
        member = message.author

        # ----------------------------------------------------
        # Handle level rewards first.
        #
        # Rewards should work even when no Bounty Channel
        # has been configured.
        # ----------------------------------------------------

        rewards = []

        for level in range(
            old_level + 1,
            new_level + 1,
        ):

            role_id = get_level_reward(
                guild.id,
                level,
            )

            if role_id is None:
                continue

            role = guild.get_role(role_id)

            if role is None:
                continue

            bot_member = guild.me

            # Bot member could not be resolved.
            if bot_member is None:
                continue

            # Bot cannot manage this role.
            if role >= bot_member.top_role:
                continue

            # User already has this role.
            if role in member.roles:
                continue

            try:

                await member.add_roles(
                    role,
                    reason=f"Bounty Level {level} reward",
                )

                rewards.append(
                    f"🎖️ {role.mention}"
                )

            except (
                discord.Forbidden,
                discord.HTTPException,
            ):
                continue

        # ----------------------------------------------------
        # No Bounty Channel = no public announcement.
        # ----------------------------------------------------

        if bounty_channel_id is None:
            return

        # ----------------------------------------------------
        # Find the configured Bounty Channel.
        # ----------------------------------------------------

        channel = guild.get_channel(
            bounty_channel_id
        )

        if channel is None:
            return

        # ----------------------------------------------------
        # Make sure this is a text channel.
        # ----------------------------------------------------

        if not isinstance(
            channel,
            discord.TextChannel,
        ):
            return

        # ----------------------------------------------------
        # Get the title for the new level.
        # ----------------------------------------------------

        title = get_level_title(new_level)

        # ----------------------------------------------------
        # Main Bounty Poster Embed
        # ----------------------------------------------------

        embed = discord.Embed(
            title="🏴‍☠️ NEW BOUNTY",
            description=(
                f"## {member.display_name}\n\n"
                "**WANTED**\n"
                "*DEAD OR ALIVE*\n\n"
                f"☠️ **Bounty**\n"
                f"**{new_bounty:,} Berries**\n\n"
                f"⚔️ **Level**\n"
                f"Level {new_level}\n\n"
                f"🔥 **Title**\n"
                f"**{title}**"
            ),
            color=discord.Color.from_rgb(
                220,
                38,
                38,
            ),
        )

        # ----------------------------------------------------
        # Bounty poster image
        # ----------------------------------------------------

        embed.set_image(
            url=BOUNTY_POSTER_BANNER
        )

        # ----------------------------------------------------
        # Level reward field
        # ----------------------------------------------------

        if rewards:

            embed.add_field(
                name="🎁 Bounty Reward",
                value="\n".join(rewards),
                inline=False,
            )

        # ----------------------------------------------------
        # Footer
        # ----------------------------------------------------

        embed.set_footer(
            text="Straw Hat • Bounty Board"
        )

        # ----------------------------------------------------
        # Public message
        #
        # No buttons.
        # No dropdowns.
        # No interactive view.
        # ----------------------------------------------------

        await channel.send(
            embed=embed
        )


# ============================================================
# EXTENSION SETUP
# ============================================================

async def setup(bot):
    """
    Load the Bounty event Cog into the bot.
    """

    await bot.add_cog(
        XPEvents(bot)
    )
