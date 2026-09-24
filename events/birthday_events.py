from datetime import datetime
from zoneinfo import ZoneInfo

import discord

from discord.ext import commands, tasks

from database.database import (
    get_all_birthdays,
    get_birthday_settings,
    get_birthday_notification,
    create_birthday_notification,
    mark_birthday_sent,
    mark_reminder_7_sent,
    mark_reminder_1_sent,
)

from services.birthday_service import (
    is_birthday_today,
    is_birthday_tomorrow,
    is_birthday_in_seven_days,
)


BIRTHDAY_COLOR = discord.Color.from_rgb(
    236,
    72,
    153
)


class BirthdayEvents(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

        self.birthday_loop.start()


    def cog_unload(self):

        self.birthday_loop.cancel()


    # ========================================================
    # BIRTHDAY CHECK LOOP
    # ========================================================

    @tasks.loop(minutes=1)
    async def birthday_loop(self):

        birthdays = get_all_birthdays()


        for (
            guild_id,
            user_id,
            month,
            day
        ) in birthdays:

            settings = get_birthday_settings(
                guild_id
            )

            if settings is None:
                continue


            (
                _guild_id,
                enabled,
                channel_id,
                role_id,
                celebration_hour,
                timezone_name
            ) = settings


            if not enabled:
                continue


            try:

                timezone = ZoneInfo(
                    timezone_name
                )

            except Exception:

                timezone = ZoneInfo(
                    "Asia/Kolkata"
                )


            now = datetime.now(
                timezone
            )

            year = now.year

            notification = get_birthday_notification(
                guild_id,
                user_id,
                year
            )

            if notification is None:

                create_birthday_notification(
                    guild_id,
                    user_id,
                    year
                )

                notification = (
                    0,
                    0,
                    0
                )

            (
                birthday_sent,
                reminder_7_sent,
                reminder_1_sent
            ) = notification            


            # Only run birthday actions at the
            # configured hour.

            if now.hour != celebration_hour:
                continue


            # ------------------------------------------------
            # BIRTHDAY TODAY
            # ------------------------------------------------

            if (
                is_birthday_today(
                    month,
                    day
                )
                and not birthday_sent
            ):

                await self.process_birthday(
                    guild_id,
                    user_id,
                    channel_id,
                    role_id
                )

                mark_birthday_sent(
                    guild_id,
                    user_id,
                    year
                )

            # ------------------------------------------------
            # SEVEN DAY REMINDER
            # ------------------------------------------------

            elif (
                is_birthday_in_seven_days(
                    month,
                    day
                )
                and not reminder_7_sent
            ):

                await self.send_reminder(
                    guild_id,
                    user_id,
                    days=7
                )

                mark_reminder_7_sent(
                    guild_id,
                    user_id,
                    year
                )

            # ------------------------------------------------
            # ONE DAY REMINDER
            # ------------------------------------------------

            elif (
                is_birthday_tomorrow(
                    month,
                    day
                )
                and not reminder_1_sent
            ):

                await self.send_reminder(
                    guild_id,
                    user_id,
                    days=1
                )

                mark_reminder_1_sent(
                    guild_id,
                    user_id,
                    year
                )

    @birthday_loop.before_loop
    async def before_birthday_loop(self):

        await self.bot.wait_until_ready()


    # ========================================================
    # BIRTHDAY CELEBRATION
    # ========================================================

    async def process_birthday(
        self,
        guild_id,
        user_id,
        channel_id,
        role_id
    ):

        guild = self.bot.get_guild(
            guild_id
        )

        if guild is None:
            return


        member = guild.get_member(
            user_id
        )

        if member is None:
            return


        # ----------------------------------------------------
        # BIRTHDAY ROLE
        # ----------------------------------------------------

        if role_id:

            role = guild.get_role(
                role_id
            )

            if role is not None:

                try:

                    await member.add_roles(
                        role,
                        reason="Birthday celebration"
                    )

                except (
                    discord.Forbidden,
                    discord.HTTPException
                ):

                    pass


        # ----------------------------------------------------
        # PUBLIC BIRTHDAY MESSAGE
        # ----------------------------------------------------

        if channel_id is None:
            return


        channel = guild.get_channel(
            channel_id
        )

        if not isinstance(
            channel,
            discord.TextChannel
        ):

            return


        embed = discord.Embed(
            title="🎂 HAPPY BIRTHDAY! 🎂",
            description=(
                f"🏴‍☠️ **Today is {member.mention}'s "
                "special day!**\n\n"

                "🎉 Everyone wish them a "
                "**Happy Birthday!**\n\n"

                "🍖 May your next adventure be "
                "full of great memories!\n\n"

                "🏴‍☠️ **The Straw Hat crew celebrates "
                "with you!**"
            ),
            color=BIRTHDAY_COLOR
        )


        embed.set_thumbnail(
            url=member.display_avatar.url
        )


        embed.set_footer(
            text="Straw Hat • Birthday Celebration"
        )


        try:

            await channel.send(
                content=member.mention,
                embed=embed
            )

        except (
            discord.Forbidden,
            discord.HTTPException
        ):

            pass


    # ========================================================
    # REMINDER
    # ========================================================

    async def send_reminder(
        self,
        guild_id,
        user_id,
        days
    ):

        guild = self.bot.get_guild(
            guild_id
        )

        if guild is None:
            return


        member = guild.get_member(
            user_id
        )

        if member is None:
            return


        if days == 1:

            title = "🎂 Birthday Tomorrow!"

            description = (
                "Your birthday is tomorrow! 🎉\n\n"
                "🏴‍☠️ The Straw Hat crew is "
                "getting ready to celebrate!"
            )

        else:

            title = "🎂 Birthday Reminder"

            description = (
                f"Your birthday is in **{days} days**!\n\n"
                "🏴‍☠️ The Straw Hat crew will "
                "celebrate with you!"
            )


        embed = discord.Embed(
            title=title,
            description=description,
            color=BIRTHDAY_COLOR
        )


        embed.set_footer(
            text="Straw Hat • Birthday System"
        )


        try:

            await member.send(
                embed=embed
            )

        except (
            discord.Forbidden,
            discord.HTTPException
        ):

            pass


async def setup(bot):

    await bot.add_cog(
        BirthdayEvents(bot)
    )