# ============================================================
# STRAW HAT BOUNTY MESSAGE EVENTS
# ============================================================

import random
import time

import discord
from discord.ext import commands
from config.banners import BOUNTY_POSTER_BANNER

from config.xp_config import (
    get_level_title,
)
from services.xp_service import (
    add_xp,
    get_xp_settings,
    is_channel_ignored,
    apply_inactivity_decay,
    get_level_reward,
)


class XPEvents(commands.Cog):
    """
    Handles XP-related Discord events.
    """

    def __init__(self, bot):
        self.bot = bot

        # ----------------------------------------------------
        # Temporary in-memory cooldown storage.
        #
        # Format:
        #
        # (guild_id, user_id) → timestamp
        # ----------------------------------------------------

        self.cooldowns = {}


# Backward-compatible alias for older references.
BountyEvents = XPEvents


    # ========================================================
    # MESSAGE EVENT
    # ========================================================

    @commands.Cog.listener()
    async def on_message(
        self,
        message: discord.Message
    ):
        """
        Award XP when a user sends an eligible message.
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
        # Get XP settings
        # ----------------------------------------------------

        settings = get_xp_settings(
            guild_id
        )

        (
            enabled,
            min_xp,
            max_xp,
            cooldown,
            levelup_channel_id
        ) = settings


        # ----------------------------------------------------
        # Check whether XP is enabled
        # ----------------------------------------------------

        if not enabled:
            return


        # ----------------------------------------------------
        # Check ignored channels
        # ----------------------------------------------------

        if is_channel_ignored(
            guild_id,
            channel_id
        ):
            return


        # ----------------------------------------------------
        # Check cooldown
        # ----------------------------------------------------

        current_time = time.time()

        cooldown_key = (
            guild_id,
            user_id
        )

        last_xp_time = self.cooldowns.get(
            cooldown_key,
            0
        )


        if (
            current_time - last_xp_time
            < cooldown
        ):
            return


        # ----------------------------------------------------
        # Start a new XP cooldown
        # ----------------------------------------------------

        self.cooldowns[cooldown_key] = current_time


        # ----------------------------------------------------
        # Generate random XP
        # ----------------------------------------------------

        amount = random.randint(
            min_xp,
            max_xp
        )


        # ----------------------------------------------------
        # Add XP to database
        # ----------------------------------------------------

        (
            old_xp,
            new_xp,
            old_level,
            new_level
        ) = add_xp(
            guild_id,
            user_id,
            amount
        )


        # ----------------------------------------------------
        # Check for level-up
        # ----------------------------------------------------

        if new_level > old_level:

            await self.handle_level_up(
                message,
                old_level,
                new_level,
                levelup_channel_id
            )


    # ============================================================
    # LEVEL-UP / BOUNTY POSTER
    # ============================================================
    
    async def handle_level_up(
        self,
        message,
        old_level,
        new_level,
        bounty_channel_id
    ):
    
        guild = message.guild
        member = message.author
    
        # --------------------------------------------------------
        # NO BOUNTY CHANNEL = NO PUBLIC ANNOUNCEMENT
        # --------------------------------------------------------
    
        if bounty_channel_id is None:
            return
    
        # --------------------------------------------------------
        # Find the configured Bounty Channel.
        # --------------------------------------------------------
    
        channel = guild.get_channel(
            bounty_channel_id
        )
    
        if channel is None:
            return
    
        # --------------------------------------------------------
        # Check whether the channel can receive messages.
        # --------------------------------------------------------
    
        if not isinstance(
            channel,
            discord.TextChannel
        ):
            return
    
        # --------------------------------------------------------
        # Handle level rewards.
        # --------------------------------------------------------
    
        rewards = []
    
        for level in range(
            old_level + 1,
            new_level + 1
        ):
    
            role_id = get_level_reward(
                guild.id,
                level
            )
    
            if role_id is None:
                continue
    
            role = guild.get_role(
                role_id
            )
    
            if role is None:
                continue
    
            bot_member = guild.me
    
            # ----------------------------------------------------
            # Make sure the bot is allowed to assign the role.
            # ----------------------------------------------------
    
            if bot_member is None:
                continue
    
            if role >= bot_member.top_role:
                continue
    
            if role in member.roles:
                continue
    
            try:
    
                await member.add_roles(
                    role,
                    reason=(
                        f"Bounty Level {level} reward"
                    )
                )
    
                rewards.append(
                    f"🎖️ {role.mention}"
                )
    
            except (
                discord.Forbidden,
                discord.HTTPException
            ):
                pass
    
        # --------------------------------------------------------
        # ONE PUBLIC BOUNTY POSTER
        # --------------------------------------------------------
        #
        # If someone jumps from Level 4 → Level 7,
        # we don't send three posters.
        #
        # We send ONE poster for the new highest level.
        # --------------------------------------------------------
    
        title = get_level_title(
            new_level
        )
    
        # --------------------------------------------------------
        # Main Bounty Poster Embed
        # --------------------------------------------------------
    
        embed = discord.Embed(
            title="🏴‍☠️ NEW BOUNTY",
            description=(
                f"## {member.display_name}\n\n"
                f"**WANTED**\n"
                f"*DEAD OR ALIVE*\n\n"
                f"⚔️ **Level {new_level}**\n"
                f"**{title}**"
            ),
            color=discord.Color.from_rgb(
                220,
                38,
                38
            )
        )
    
        # --------------------------------------------------------
        # Bounty poster image
        # --------------------------------------------------------
    
        embed.set_image(
            url=BOUNTY_POSTER_BANNER
        )
    
        # --------------------------------------------------------
        # Reward field
        # --------------------------------------------------------
    
        if rewards:
    
            embed.add_field(
                name="🎁 Bounty Reward",
                value="\n".join(rewards),
                inline=False
            )
    
        # --------------------------------------------------------
        # Footer
        # --------------------------------------------------------
    
        embed.set_footer(
            text="Straw Hat • Bounty Board"
        )
    
        # --------------------------------------------------------
        # PUBLIC MESSAGE
        #
        # NO BUTTONS
        # NO DROPDOWNS
        # NO VIEW
        # --------------------------------------------------------
    
        await channel.send(
            embed=embed
        )
    
# ============================================================
# EXTENSION SETUP
# ============================================================

async def setup(bot):
    """
    Load the XP event Cog into the bot.
    """

    await bot.add_cog(
        XPEvents(bot)
    )