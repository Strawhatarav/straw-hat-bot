# ============================================================
# STRAW HAT REMINDER SCHEDULER
# ============================================================

import asyncio

from datetime import timedelta

import discord

from discord.ext import tasks

from services.reminder_service import (
    get_due_reminders,
    delete_reminder,
    update_next_occurrence,
    string_to_datetime,
)


class ReminderScheduler:

    def __init__(
        self,
        bot
    ):

        self.bot = bot

        self.started = False


    # ========================================================
    # START
    # ========================================================

    def start(self):

        if self.started:
            return

        self.started = True

        self.check_reminders.start()


    # ========================================================
    # STOP
    # ========================================================

    def stop(self):

        if self.check_reminders.is_running():

            self.check_reminders.cancel()

    # ========================================================
    # BACKGROUND TASK
    # ========================================================

    @tasks.loop(
        seconds=15
    )
    async def check_reminders(
        self
    ):

        reminders = get_due_reminders()

        for reminder in reminders:

            try:

                await self.process_reminder(
                    reminder
                )

            except Exception as error:

                print(
                    "❌ Reminder processing error:",
                    error
                )

    # ========================================================
    # WAIT UNTIL BOT READY
    # ========================================================

    @check_reminders.before_loop
    async def before_check_reminders(
        self
    ):

        await self.bot.wait_until_ready()

    # ========================================================
    # PROCESS REMINDER
    # ========================================================

    async def process_reminder(
        self,
        reminder
    ):

        (
            reminder_id,
            user_id,
            guild_id,
            channel_id,
            message,
            reminder_type,
            scheduled_at,
            timezone_name,
            recurring,
            recurrence
        ) = reminder


        # ====================================================
        # PERSONAL REMINDER
        # ====================================================

        if reminder_type == "personal":

            await self.send_personal_reminder(
                reminder
            )

            delete_reminder(
                reminder_id
            )

            return


        # ====================================================
        # SERVER / SCHEDULED MESSAGE
        # ====================================================

        if reminder_type in (
            "server",
            "recurring"
        ):

            await self.send_server_message(
                reminder
            )


        # ====================================================
        # RECURRING REMINDER
        # ====================================================

        if recurring:

            next_time = (
                string_to_datetime(
                    scheduled_at
                )
                + self.get_recurrence_delta(
                    recurrence
                )
            )

            update_next_occurrence(
                reminder_id,
                next_time
            )

        else:

            delete_reminder(
                reminder_id
            )

    # ========================================================
    # PERSONAL DM
    # ========================================================

    async def send_personal_reminder(
        self,
        reminder
    ):

        (
            reminder_id,
            user_id,
            guild_id,
            channel_id,
            message,
            reminder_type,
            scheduled_at,
            timezone_name,
            recurring,
            recurrence
        ) = reminder


        user = self.bot.get_user(
            user_id
        )


        if user is None:

            try:

                user = await self.bot.fetch_user(
                    user_id
                )

            except (
                discord.NotFound,
                discord.HTTPException
            ):

                return


        embed = discord.Embed(

            title="🔔 Reminder",

            description=(
                "You asked me to remind you:\n\n"
                f"📝 **{message}**"
            ),

            color=discord.Color.from_rgb(
                220,
                38,
                38
            )
        )


        embed.add_field(
            name="⏰ Reminder Time",
            value=discord.utils.format_dt(
                string_to_datetime(
                    scheduled_at
                ),
                style="F"
            ),
            inline=False
        )


        embed.set_footer(
            text="Straw Hat • Reminder System"
        )


        try:

            await user.send(
                embed=embed
            )

        except discord.Forbidden:

            print(
                f"⚠️ Could not DM user {user_id}"
            )

    # ========================================================
    # SERVER MESSAGE
    # ========================================================

    async def send_server_message(
        self,
        reminder
    ):

        (
            reminder_id,
            user_id,
            guild_id,
            channel_id,
            message,
            reminder_type,
            scheduled_at,
            timezone_name,
            recurring,
            recurrence
        ) = reminder


        if channel_id is None:
            return


        channel = self.bot.get_channel(
            channel_id
        )


        if channel is None:

            try:

                channel = await self.bot.fetch_channel(
                    channel_id
                )

            except (
                discord.NotFound,
                discord.Forbidden,
                discord.HTTPException
            ):

                return


        embed = discord.Embed(

            title=(
                "🏴‍☠️ Recurring Reminder"
                if recurring
                else "🏴‍☠️ Scheduled Message"
            ),

            description=(
                f"📢 {message}"
            ),

            color=discord.Color.from_rgb(
                220,
                38,
                38
            )
        )


        embed.set_footer(
            text="Straw Hat • Reminder System"
        )


        try:

            await channel.send(
                embed=embed
            )

        except (
            discord.Forbidden,
            discord.HTTPException
        ):

            return

    # ========================================================
    # RECURRENCE
    # ========================================================

    def get_recurrence_delta(
        self,
        recurrence
    ):

        if recurrence == "daily":

            return timedelta(
                days=1
            )

        if recurrence == "weekly":

            return timedelta(
                weeks=1
            )

        if recurrence == "monthly":

            return timedelta(
                days=30
            )

        return timedelta(
            days=1
        )