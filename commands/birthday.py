import calendar

import discord
from discord import app_commands
from discord.ext import commands

from database.database import (
    set_birthday,
    remove_birthday,
    get_birthday,
)

from services.birthday_service import (
    format_birthday,
    get_days_until_birthday,
)

from services.embed_service import (
    create_embed,
    RED,
    GREEN,
    YELLOW,
)


BIRTHDAY_COLOR = discord.Color.from_rgb(
    236,
    72,
    153
)


class Birthday(commands.Cog):

    birthday = app_commands.Group(
        name="birthday",
        description="Manage your birthday in this server."
    )


    def __init__(self, bot):

        self.bot = bot


    # ========================================================
    # /BIRTHDAY SET
    # ========================================================

    @birthday.command(
        name="set",
        description="Set your birthday in this server."
    )
    @app_commands.describe(
        month="Your birth month (1-12).",
        day="Your birth day."
    )
    async def birthday_set(
        self,
        interaction: discord.Interaction,
        month: int,
        day: int
    ):

        guild = interaction.guild

        if guild is None:

            await interaction.response.send_message(
                "This command can only be used inside a server.",
                ephemeral=True
            )

            return


        # Validate month

        if month < 1 or month > 12:

            await interaction.response.send_message(
                "❌ Month must be between **1 and 12**.",
                ephemeral=True
            )

            return


        # Validate day

        max_day = calendar.monthrange(
            2000,
            month
        )[1]

        if day < 1 or day > max_day:

            await interaction.response.send_message(
                f"❌ Day must be between **1 and {max_day}** for this month.",
                ephemeral=True
            )

            return


        # Save birthday

        set_birthday(
            guild.id,
            interaction.user.id,
            month,
            day
        )


        birthday_text = format_birthday(
            month,
            day
        )


        embed = create_embed(
            title="🎂 Birthday Set",
            description=(
                "Your birthday has been saved for this server.\n\n"
                f"📅 **{birthday_text}**\n\n"
                "🏴‍☠️ The Straw Hat crew will celebrate with you!"
            ),
            color=GREEN,
            footer_text="Straw Hat • Birthday System"
        )


        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


    # ========================================================
    # /BIRTHDAY REMOVE
    # ========================================================

    @birthday.command(
        name="remove",
        description="Remove your birthday from this server."
    )
    async def birthday_remove(
        self,
        interaction: discord.Interaction
    ):

        guild = interaction.guild

        if guild is None:

            await interaction.response.send_message(
                "This command can only be used inside a server.",
                ephemeral=True
            )

            return


        existing = get_birthday(
            guild.id,
            interaction.user.id
        )


        if existing is None:

            await interaction.response.send_message(
                "🎂 You don't have a birthday set in this server.",
                ephemeral=True
            )

            return


        remove_birthday(
            guild.id,
            interaction.user.id
        )


        embed = create_embed(
            title="🎂 Birthday Removed",
            description=(
                "Your birthday has been removed from this server.\n\n"
                "You can add it again anytime with "
                "**/birthday set**."
            ),
            color=RED,
            footer_text="Straw Hat • Birthday System"
        )


        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


    # ========================================================
    # /BIRTHDAY
    # ========================================================

    @birthday.command(
        name="view",
        description="View your birthday in this server."
    )
    async def birthday_view(
        self,
        interaction: discord.Interaction
    ):

        guild = interaction.guild

        if guild is None:

            await interaction.response.send_message(
                "This command can only be used inside a server.",
                ephemeral=True
            )

            return


        result = get_birthday(
            guild.id,
            interaction.user.id
        )


        if result is None:

            embed = create_embed(
                title="🎂 Your Birthday",
                description=(
                    "You haven't set your birthday in this server yet.\n\n"
                    "Use **/birthday set** to add it."
                ),
                color=YELLOW,
                footer_text="Straw Hat • Birthday System"
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

            return


        month, day = result

        birthday_text = format_birthday(
            month,
            day
        )

        days = get_days_until_birthday(
            month,
            day
        )


        if days == 0:

            countdown = "🎉 **Today!**"

        elif days == 1:

            countdown = "⏳ **Tomorrow!**"

        else:

            countdown = f"⏳ **{days} days remaining**"


        embed = create_embed(
            title="🎂 Your Birthday",
            description=(
                f"📅 **{birthday_text}**\n\n"
                f"{countdown}\n\n"
                "🏴‍☠️ Birthday celebrations are handled by "
                "the Straw Hat crew."
            ),
            color=BIRTHDAY_COLOR,
            footer_text="Straw Hat • Birthday System"
        )


        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


async def setup(bot):

    await bot.add_cog(
        Birthday(bot)
    )