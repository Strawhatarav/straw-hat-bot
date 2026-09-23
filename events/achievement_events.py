import discord

from discord.ext import commands

from services.achievement_service import (
    process_message_achievements,
    get_achievement_by_key,
    unlock_achievement
)


class AchievementEvents(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    # ========================================================
    # MEMBER JOIN
    # ========================================================

    @commands.Cog.listener()
    async def on_member_join(
        self,
        member: discord.Member
    ):

        achievement = get_achievement_by_key(
            member.guild.id,
            "straw_hat_member"
        )

        if achievement is None:
            return

        newly_unlocked = unlock_achievement(
            member.guild.id,
            member.id,
            achievement[0]
        )

        if newly_unlocked:
            await self.send_achievement_notification(
                member,
                achievement
            )


    # ========================================================
    # MESSAGE
    # ========================================================

    @commands.Cog.listener()
    async def on_message(
        self,
        message: discord.Message
    ):

        # Ignore bots.
        if message.author.bot:
            return

        # Ignore DMs.
        if message.guild is None:
            return

        unlocked = process_message_achievements(
            message.guild.id,
            message.author.id
        )

        for achievement in unlocked:

            await self.send_achievement_notification(
                message.author,
                achievement
            )


    # ========================================================
    # ACHIEVEMENT NOTIFICATION
    # ========================================================

    async def send_achievement_notification(
        self,
        member: discord.Member,
        achievement
    ):

        # SQLite rows are indexed from zero.
        achievement_name = achievement[2]
        description = achievement[3]
        rarity = achievement[5]
        reward = achievement[10]

        embed = discord.Embed(
            title="🏆 ACHIEVEMENT UNLOCKED!",
            description=(
                f"**{achievement_name}**\n\n"
                f"{description}"
            ),
            color=discord.Color.from_rgb(
                220,
                38,
                38
            )
        )

        embed.add_field(
            name="Rarity",
            value=f"✨ {rarity}",
            inline=True
        )

        embed.add_field(
            name="🪙 Reward",
            value=f"{reward:,} Berries",
            inline=True
        )

        embed.set_footer(
            text="Straw Hat • Achievements"
        )

        # For now this is private.
        try:
            await member.send(embed=embed)

        except discord.Forbidden:
            # User has DMs disabled.
            pass


async def setup(bot):
    await bot.add_cog(
        AchievementEvents(bot)
    )