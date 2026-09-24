import discord

from discord.ext import commands

from services.starboard_service import (
    get_settings,
    get_starboard_message,
    save_starboard_message,
    update_star_count,
    delete_starboard_message
)

from services.achievement_service import (
    increment_starboard_posts,
    get_starboard_posts,
    get_achievement_by_key,
    unlock_achievement
)

STAR_EMOJI = "⭐"


class StarboardEvents(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    # ========================================================
    # STAR ADDED
    # ========================================================

    @commands.Cog.listener()
    async def on_raw_reaction_add(
        self,
        payload: discord.RawReactionActionEvent
    ):

        await self.process_reaction(
            payload,
            reaction_added=True
        )


    # ========================================================
    # STAR REMOVED
    # ========================================================

    @commands.Cog.listener()
    async def on_raw_reaction_remove(
        self,
        payload: discord.RawReactionActionEvent
    ):

        await self.process_reaction(
            payload,
            reaction_added=False
        )


    # ========================================================
    # MAIN REACTION PROCESSOR
    # ========================================================

    async def process_reaction(
        self,
        payload,
        reaction_added: bool
    ):

        # ----------------------------------------------------
        # Only handle the ⭐ emoji.
        # ----------------------------------------------------

        if payload.emoji.name != STAR_EMOJI:
            return


        # ----------------------------------------------------
        # Ignore DMs.
        # ----------------------------------------------------

        if payload.guild_id is None:
            return


        # ----------------------------------------------------
        # Get Starboard configuration.
        # ----------------------------------------------------

        settings = get_settings(
            payload.guild_id
        )

        if settings is None:
            return


        guild_id = settings[0]
        channel_id = settings[1]
        threshold = settings[2]
        enabled = settings[3]


        # ----------------------------------------------------
        # Starboard disabled?
        # ----------------------------------------------------

        if not enabled:
            return


        # ----------------------------------------------------
        # No Starboard channel configured.
        # ----------------------------------------------------

        if channel_id is None:
            return


        # ----------------------------------------------------
        # Ignore reactions inside the Starboard channel itself.
        # ----------------------------------------------------

        if payload.channel_id == channel_id:
            return


        # ----------------------------------------------------
        # Fetch the original message.
        # ----------------------------------------------------

        channel = self.bot.get_channel(
            payload.channel_id
        )

        if channel is None:
            return

        try:
            message = await channel.fetch_message(
                payload.message_id
            )

        except (
            discord.NotFound,
            discord.Forbidden,
            discord.HTTPException
        ):
            return


        # ----------------------------------------------------
        # Don't starboard bot messages.
        # ----------------------------------------------------

        if message.author.bot:
            return


        # ----------------------------------------------------
        # Count current ⭐ reactions.
        #
        # We deliberately calculate the current count from
        # Discord rather than trusting the event itself.
        # ----------------------------------------------------

        star_count = 0

        for reaction in message.reactions:

            if str(reaction.emoji) == STAR_EMOJI:
                star_count = reaction.count
                break


        # ----------------------------------------------------
        # Find existing Starboard entry.
        # ----------------------------------------------------

        existing = get_starboard_message(
            guild_id,
            message.id
        )


        # ====================================================
        # CASE 1 — THRESHOLD REACHED
        # ====================================================

        if star_count >= threshold:

            # -----------------------------------------------
            # Already on Starboard?
            # -----------------------------------------------

            if existing:

                starboard_message_id = existing[0]

                await self.update_starboard_post(
                    guild_id,
                    message,
                    starboard_message_id,
                    star_count
                )

                update_star_count(
                    guild_id,
                    message.id,
                    star_count
                )

            # -----------------------------------------------
            # Achievement: Viral Post
            # -----------------------------------------------
            
            if star_count >= 10:
            
                achievement = get_achievement_by_key(
                    guild_id,
                    "viral_post"
                )
            
                if achievement:
            
                    newly_unlocked = unlock_achievement(
                        guild_id,
                        message.author.id,
                        achievement[0]
                    )
            
                    if newly_unlocked:
                        print(
                            f"{message.author} unlocked "
                            f"{achievement[2]}"
                        )

                return


            # -----------------------------------------------
            # First time reaching threshold.
            # -----------------------------------------------

            starboard_channel = self.bot.get_channel(
                channel_id
            )

            if not isinstance(
                starboard_channel,
                discord.TextChannel
            ):
                return


            embed = self.create_starboard_embed(
                message,
                star_count
            )

            try:

                starboard_message = (
                    await starboard_channel.send(
                        embed=embed
                    )
                )

            except (
                discord.Forbidden,
                discord.HTTPException
            ):
                return


            # -----------------------------------------------
            # Save mapping.
            # -----------------------------------------------
            
            save_starboard_message(
                guild_id,
                message.id,
                starboard_message.id,
                star_count
            )
            
            # -----------------------------------------------
            # Achievement: First Starboard
            # -----------------------------------------------
            
            increment_starboard_posts(
                guild_id,
                message.author.id
            )
            
            starboard_posts = get_starboard_posts(
                guild_id,
                message.author.id
            )
            
            # First Starboard post
            if starboard_posts >= 1:
            
                achievement = get_achievement_by_key(
                    guild_id,
                    "first_starboard"
                )
            
                if achievement:
            
                    newly_unlocked = unlock_achievement(
                        guild_id,
                        message.author.id,
                        achievement[0]
                    )
            
                    if newly_unlocked:
                        print(
                            f"{message.author} unlocked "
                            f"{achievement[2]}"
                        )
            
            
            # -----------------------------------------------
            # Achievement: 10 Starboard Posts
            # -----------------------------------------------
            
            if starboard_posts >= 10:
            
                achievement = get_achievement_by_key(
                    guild_id,
                    "star_10"
                )
            
                if achievement:
            
                    newly_unlocked = unlock_achievement(
                        guild_id,
                        message.author.id,
                        achievement[0]
                    )
            
                    if newly_unlocked:
                        print(
                            f"{message.author} unlocked "
                            f"{achievement[2]}"
                        )


        # ====================================================
        # CASE 2 — BELOW THRESHOLD
        # ====================================================

        elif existing:

            starboard_message_id = existing[0]

            starboard_channel = self.bot.get_channel(
                channel_id
            )

            if starboard_channel is None:
                return

            try:

                starboard_message = (
                    await starboard_channel.fetch_message(
                        starboard_message_id
                    )
                )

                await starboard_message.delete()

            except (
                discord.NotFound,
                discord.Forbidden,
                discord.HTTPException
            ):
                pass

            delete_starboard_message(
                guild_id,
                message.id
            )


    # ========================================================
    # CREATE STARBOARD EMBED
    # ========================================================

    def create_starboard_embed(
        self,
        message: discord.Message,
        star_count: int
    ):

        embed = discord.Embed(
            title="⭐ STRAW HAT STARBOARD",
            description=message.content or "*No text content*",
            color=discord.Color.from_rgb(
                220,
                38,
                38
            ),
            timestamp=message.created_at
        )

        embed.set_author(
            name=message.author.display_name,
            icon_url=message.author.display_avatar.url
        )

        embed.add_field(
            name="⭐ Stars",
            value=f"**{star_count}**",
            inline=True
        )

        embed.add_field(
            name="📍 Channel",
            value=message.channel.mention,
            inline=True
        )

        embed.add_field(
            name="🔗 Original",
            value=(
                f"[Jump to message]"
                f"({message.jump_url})"
            ),
            inline=False
        )

        # ----------------------------------------------------
        # If the message contains an image attachment,
        # display it in the Starboard.
        # ----------------------------------------------------

        for attachment in message.attachments:

            if attachment.content_type:

                if attachment.content_type.startswith(
                    "image/"
                ):
                    embed.set_image(
                        url=attachment.url
                    )

                    break


        embed.set_footer(
            text="Straw Hat • Starboard"
        )

        return embed


    # ========================================================
    # UPDATE EXISTING STARBOARD POST
    # ========================================================

    async def update_starboard_post(
        self,
        guild_id,
        original_message,
        starboard_message_id,
        star_count
    ):

        settings = get_settings(guild_id)

        if settings is None:
            return

        channel_id = settings[1]

        channel = self.bot.get_channel(
            channel_id
        )

        if channel is None:
            return

        try:

            starboard_message = (
                await channel.fetch_message(
                    starboard_message_id
                )
            )

        except (
            discord.NotFound,
            discord.Forbidden,
            discord.HTTPException
        ):
            return


        embed = self.create_starboard_embed(
            original_message,
            star_count
        )

        try:

            await starboard_message.edit(
                embed=embed
            )

        except (
            discord.NotFound,
            discord.Forbidden,
            discord.HTTPException
        ):
            pass


async def setup(bot):
    await bot.add_cog(
        StarboardEvents(bot)
    )