import discord

from discord import app_commands
from discord.ext import commands

from services.achievement_service import (
    get_user_achievements
)


class Achievements(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @app_commands.command(
        name="achievements",
        description="View your Straw Hat achievements."
    )
    async def achievements(
        self,
        interaction: discord.Interaction
    ):

        rows = get_user_achievements(
            interaction.guild.id,
            interaction.user.id
        )

        unlocked = []
        locked = []

        for row in rows:

            name = row[2]
            description = row[3]
            category = row[4]
            rarity = row[5]
            hidden = row[6]
            unlocked_at = row[11]

            if unlocked_at:
                unlocked.append(
                    f"✅ {name} — {rarity}"
                )

            else:

                if hidden:
                    locked.append(
                        "🔒 ???? — Hidden Achievement"
                    )
                else:
                    locked.append(
                        f"🔒 {name}"
                    )

        embed = discord.Embed(
            title="🏆 STRAW HAT ACHIEVEMENTS",
            description=(
                f"**Unlocked:** {len(unlocked)} / "
                f"{len(rows)}"
            ),
            color=discord.Color.from_rgb(
                220,
                38,
                38
            )
        )

        if unlocked:
            embed.add_field(
                name="🏆 Unlocked",
                value="\n".join(unlocked[:10]),
                inline=False
            )

        if locked:
            embed.add_field(
                name="🔒 Locked",
                value="\n".join(locked[:10]),
                inline=False
            )

        embed.set_footer(
            text="Straw Hat • Achievements"
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(
        Achievements(bot)
    )