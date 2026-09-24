# ============================================================
# STRAW HAT REMINDER COMMANDS
# ============================================================

import re

from datetime import datetime, timedelta, timezone

from zoneinfo import ZoneInfo, available_timezones

import discord

from discord import app_commands

from discord.ext import commands

from services.reminder_service import (
    create_reminder,
    get_user_reminders,
    get_reminder,
    cancel_reminder,
    get_user_timezone,
    set_user_timezone,
    count_personal_reminders,
    count_recurring_reminders,
    count_server_schedules,
    MAX_PERSONAL_REMINDERS,
    MAX_RECURRING_REMINDERS,
    MAX_SERVER_SCHEDULES,
    MAX_MESSAGE_LENGTH,
    MAX_REMINDER_DAYS,
)


# ============================================================
# TIME PARSER
# ============================================================

def parse_duration(
    value: str
):

    value = value.lower().strip()

    match = re.fullmatch(
        r"(\d+)(m|h|d|w)",
        value
    )

    if not match:
        return None

    amount = int(
        match.group(1)
    )

    unit = match.group(2)


    if unit == "m":

        delta = timedelta(
            minutes=amount
        )

    elif unit == "h":

        delta = timedelta(
            hours=amount
        )

    elif unit == "d":

        delta = timedelta(
            days=amount
        )

    else:

        delta = timedelta(
            weeks=amount
        )


    if delta > timedelta(
        days=MAX_REMINDER_DAYS
    ):

        return None


    return (
        datetime.now(
            timezone.utc
        )
        + delta
    )


# ============================================================
# FORMAT TIME
# ============================================================

def format_timestamp(
    value
):

    return discord.utils.format_dt(
        value,
        style="F"
    )


# ============================================================
# REMINDER COG
# ============================================================

class Reminders(
    commands.Cog
):

    def __init__(
        self,
        bot
    ):

        self.bot = bot


    # ========================================================
    # /REMIND
    # ========================================================

    @app_commands.command(
        name="remind",
        description="Create a personal reminder."
    )
    @app_commands.describe(
        when="When should I remind you? Example: 30m, 2h, 1d.",
        message="What should I remind you about?"
    )
    async def remind(
        self,
        interaction: discord.Interaction,
        when: str,
        message: str
    ):

        await interaction.response.defer(
            ephemeral=True
        )


        # ----------------------------------------------------
        # MESSAGE LENGTH
        # ----------------------------------------------------

        if len(message) > MAX_MESSAGE_LENGTH:

            embed = discord.Embed(

                title="⚠️ Reminder Too Long",

                description=(
                    f"Your reminder can contain "
                    f"at most **{MAX_MESSAGE_LENGTH} characters**."
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

            await interaction.followup.send(
                embed=embed,
                ephemeral=True
            )

            return


        # ----------------------------------------------------
        # LIMIT
        # ----------------------------------------------------

        current_count = count_personal_reminders(
            interaction.user.id
        )

        if current_count >= MAX_PERSONAL_REMINDERS:

            embed = discord.Embed(

                title="⚠️ Reminder Limit Reached",

                description=(
                    f"You already have "
                    f"**{MAX_PERSONAL_REMINDERS} active personal reminders**."
                    "\n\n"
                    "Cancel an existing reminder before creating another one."
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

            await interaction.followup.send(
                embed=embed,
                ephemeral=True
            )

            return


        # ----------------------------------------------------
        # PARSE TIME
        # ----------------------------------------------------

        scheduled_at = parse_duration(
            when
        )

        if scheduled_at is None:

            embed = discord.Embed(

                title="⚠️ Invalid Reminder Time",

                description=(
                    "I couldn't understand that time.\n\n"
                    "Try one of these:\n"
                    "⏱️ `30m`\n"
                    "⏰ `2h`\n"
                    "📅 `1d`\n"
                    "🗓️ `1w`"
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

            await interaction.followup.send(
                embed=embed,
                ephemeral=True
            )

            return


        # ----------------------------------------------------
        # CREATE
        # ----------------------------------------------------

        timezone_name = get_user_timezone(
            interaction.user.id
        )


        reminder_id = create_reminder(

            user_id=interaction.user.id,

            guild_id=None,

            channel_id=None,

            message=message,

            scheduled_at=scheduled_at,

            timezone_name=timezone_name
        )


        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        embed = discord.Embed(

            title="🏴‍☠️ Reminder Created",

            description=(
                "Your personal reminder has been scheduled."
            ),

            color=discord.Color.from_rgb(
                220,
                38,
                38
            )
        )


        embed.add_field(
            name="📝 Reminder",
            value=message,
            inline=False
        )


        embed.add_field(
            name="⏰ Scheduled",
            value=format_timestamp(
                scheduled_at
            ),
            inline=False
        )


        embed.add_field(
            name="🌍 Timezone",
            value=timezone_name,
            inline=True
        )


        embed.add_field(
            name="🆔 Reminder ID",
            value=f"`#{reminder_id}`",
            inline=True
        )


        embed.set_footer(
            text="Straw Hat • Reminder System"
        )


        await interaction.followup.send(
            embed=embed,
            ephemeral=True
        )


    # ========================================================
    # /REMINDERS
    # ========================================================

    @app_commands.command(
        name="reminders",
        description="View your active personal reminders."
    )
    async def reminders(
        self,
        interaction: discord.Interaction
    ):

        results = get_user_reminders(
            interaction.user.id
        )


        if not results:

            embed = discord.Embed(

                title="⏰ Your Reminders",

                description=(
                    "You currently have no active reminders."
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

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

            return


        embed = discord.Embed(

            title="⏰ Your Reminders",

            description=(
                f"You have **{len(results)} active reminder(s)**."
            ),

            color=discord.Color.from_rgb(
                220,
                38,
                38
            )
        )


        for row in results[:10]:

            (
                reminder_id,
                message,
                scheduled_at,
                timezone_name,
                recurring,
                recurrence,
                guild_id,
                channel_id
            ) = row


            reminder_datetime = datetime.fromisoformat(
                scheduled_at
            )


            repeat_text = (
                f"🔁 {recurrence.title()}"
                if recurring
                else "⏰ One-time"
            )


            embed.add_field(

                name=(
                    f"#{reminder_id} • "
                    f"{repeat_text}"
                ),

                value=(
                    f"📝 {message}\n"
                    f"📅 {format_timestamp(reminder_datetime)}\n"
                    f"🌍 {timezone_name}"
                ),

                inline=False
            )


        embed.set_footer(
            text="Straw Hat • Reminder System"
        )


        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


    # ========================================================
    # /CANCELREMINDER
    # ========================================================

    @app_commands.command(
        name="cancelreminder",
        description="Cancel one of your reminders."
    )
    @app_commands.describe(
        reminder_id="The reminder ID shown by /reminders."
    )
    async def cancelreminder(
        self,
        interaction: discord.Interaction,
        reminder_id: int
    ):

        reminder = get_reminder(
            reminder_id,
            interaction.user.id
        )


        if reminder is None:

            embed = discord.Embed(

                title="⚠️ Reminder Not Found",

                description=(
                    "That reminder does not exist or has already been cancelled."
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

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

            return


        cancelled = cancel_reminder(
            reminder_id,
            interaction.user.id
        )


        if not cancelled:

            await interaction.response.send_message(
                "⚠️ The reminder could not be cancelled.",
                ephemeral=True
            )

            return


        embed = discord.Embed(

            title="🏴‍☠️ Reminder Cancelled",

            description=(
                "Your reminder has been cancelled successfully."
            ),

            color=discord.Color.from_rgb(
                220,
                38,
                38
            )
        )


        embed.add_field(
            name="📝 Reminder",
            value=reminder[1],
            inline=False
        )


        embed.add_field(
            name="🆔 Reminder ID",
            value=f"`#{reminder_id}`",
            inline=True
        )


        embed.set_footer(
            text="Straw Hat • Reminder System"
        )


        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


    # ========================================================
    # /TIMEZONE
    # ========================================================

    @app_commands.command(
        name="timezone",
        description="Set your reminder timezone."
    )
    @app_commands.describe(
        timezone_name="IANA timezone, for example Asia/Kolkata."
    )
    async def timezone(
        self,
        interaction: discord.Interaction,
        timezone_name: str
    ):

        timezone_name = timezone_name.strip()


        if timezone_name not in available_timezones():

            embed = discord.Embed(

                title="⚠️ Invalid Timezone",

                description=(
                    "That timezone was not recognized.\n\n"
                    "For India, use:\n"
                    "`Asia/Kolkata`"
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

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

            return


        set_user_timezone(
            interaction.user.id,
            timezone_name
        )


        embed = discord.Embed(

            title="🌍 Timezone Updated",

            description=(
                "Your reminder timezone has been updated."
            ),

            color=discord.Color.from_rgb(
                220,
                38,
                38
            )
        )


        embed.add_field(
            name="🌍 Timezone",
            value=timezone_name,
            inline=False
        )


        embed.set_footer(
            text="Straw Hat • Reminder System"
        )


        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


    # ========================================================
    # /SERVERREMIND
    # ========================================================

    @app_commands.command(
        name="serverremind",
        description="Schedule a public server reminder."
    )
    @app_commands.describe(
        when="When should the reminder be posted? Example: 2h.",
        message="Message that will be posted publicly."
    )
    @app_commands.checks.has_permissions(
        manage_guild=True
    )
    async def serverremind(
        self,
        interaction: discord.Interaction,
        when: str,
        message: str
    ):

        if interaction.guild is None:

            await interaction.response.send_message(
                "This command can only be used inside a server.",
                ephemeral=True
            )

            return


        if len(message) > MAX_MESSAGE_LENGTH:

            await interaction.response.send_message(
                f"⚠️ Message cannot exceed {MAX_MESSAGE_LENGTH} characters.",
                ephemeral=True
            )

            return


        current_count = count_server_schedules(
            interaction.guild.id
        )


        if current_count >= MAX_SERVER_SCHEDULES:

            await interaction.response.send_message(

                f"⚠️ This server already has "
                f"{MAX_SERVER_SCHEDULES} active schedules.",

                ephemeral=True
            )

            return


        scheduled_at = parse_duration(
            when
        )


        if scheduled_at is None:

            await interaction.response.send_message(

                "⚠️ Invalid time. Use `30m`, `2h`, `1d`, or `1w`.",

                ephemeral=True
            )

            return


        reminder_id = create_reminder(

            user_id=interaction.user.id,

            guild_id=interaction.guild.id,

            channel_id=interaction.channel.id,

            message=message,

            scheduled_at=scheduled_at,

            timezone_name="UTC"
        )


        embed = discord.Embed(

            title="🏴‍☠️ Server Reminder Scheduled",

            description=(
                "The reminder will be posted publicly in this channel."
            ),

            color=discord.Color.from_rgb(
                220,
                38,
                38
            )
        )


        embed.add_field(
            name="📢 Message",
            value=message,
            inline=False
        )


        embed.add_field(
            name="⏰ Scheduled",
            value=format_timestamp(
                scheduled_at
            ),
            inline=False
        )


        embed.add_field(
            name="📍 Channel",
            value=interaction.channel.mention,
            inline=True
        )


        embed.add_field(
            name="🆔 ID",
            value=f"`#{reminder_id}`",
            inline=True
        )


        embed.set_footer(
            text="Straw Hat • Server Reminder"
        )


        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


    # ========================================================
    # /SCHEDULE
    # ========================================================

    @app_commands.command(
        name="schedule",
        description="Schedule a public message."
    )
    @app_commands.describe(
        when="When should the message be posted? Example: 2h.",
        message="Message to post publicly."
    )
    @app_commands.checks.has_permissions(
        manage_guild=True
    )
    async def schedule(
        self,
        interaction: discord.Interaction,
        when: str,
        message: str
    ):

        if interaction.guild is None:

            await interaction.response.send_message(
                "This command can only be used inside a server.",
                ephemeral=True
            )

            return


        if len(message) > MAX_MESSAGE_LENGTH:

            await interaction.response.send_message(
                f"⚠️ Message cannot exceed {MAX_MESSAGE_LENGTH} characters.",
                ephemeral=True
            )

            return


        current_count = count_server_schedules(
            interaction.guild.id
        )


        if current_count >= MAX_SERVER_SCHEDULES:

            await interaction.response.send_message(

                f"⚠️ This server already has "
                f"{MAX_SERVER_SCHEDULES} active schedules.",

                ephemeral=True
            )

            return


        scheduled_at = parse_duration(
            when
        )


        if scheduled_at is None:

            await interaction.response.send_message(

                "⚠️ Invalid time. Use `30m`, `2h`, `1d`, or `1w`.",

                ephemeral=True
            )

            return


        reminder_id = create_reminder(

            user_id=interaction.user.id,

            guild_id=interaction.guild.id,

            channel_id=interaction.channel.id,

            message=message,

            scheduled_at=scheduled_at,

            timezone_name="UTC"
        )


        embed = discord.Embed(

            title="📅 Scheduled Message Created",

            description=(
                "Your message has been scheduled."
            ),

            color=discord.Color.from_rgb(
                220,
                38,
                38
            )
        )


        embed.add_field(
            name="📝 Message",
            value=message,
            inline=False
        )


        embed.add_field(
            name="⏰ Scheduled",
            value=format_timestamp(
                scheduled_at
            ),
            inline=False
        )


        embed.add_field(
            name="📍 Channel",
            value=interaction.channel.mention,
            inline=True
        )


        embed.add_field(
            name="🆔 ID",
            value=f"`#{reminder_id}`",
            inline=True
        )


        embed.set_footer(
            text="Straw Hat • Scheduled Messages"
        )


        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


    # ========================================================
    # /SCHEDULE_REPEAT
    # ========================================================

    @app_commands.command(
        name="schedule_repeat",
        description="Create a recurring public message."
    )
    @app_commands.describe(
        when="When should it first run? Example: 1d.",
        recurrence="daily, weekly, or monthly.",
        message="Message to post."
    )
    @app_commands.checks.has_permissions(
        manage_guild=True
    )
    async def schedule_repeat(
        self,
        interaction: discord.Interaction,
        when: str,
        recurrence: str,
        message: str
    ):

        if interaction.guild is None:

            await interaction.response.send_message(
                "This command can only be used inside a server.",
                ephemeral=True
            )

            return


        recurrence = recurrence.lower()


        if recurrence not in (
            "daily",
            "weekly",
            "monthly"
        ):

            await interaction.response.send_message(

                "⚠️ Recurrence must be `daily`, `weekly`, or `monthly`.",

                ephemeral=True
            )

            return


        if len(message) > MAX_MESSAGE_LENGTH:

            await interaction.response.send_message(
                f"⚠️ Message cannot exceed {MAX_MESSAGE_LENGTH} characters.",
                ephemeral=True
            )

            return


        current_count = count_server_schedules(
            interaction.guild.id
        )


        if current_count >= MAX_SERVER_SCHEDULES:

            await interaction.response.send_message(

                f"⚠️ This server already has "
                f"{MAX_SERVER_SCHEDULES} active schedules.",

                ephemeral=True
            )

            return


        scheduled_at = parse_duration(
            when
        )


        if scheduled_at is None:

            await interaction.response.send_message(

                "⚠️ Invalid time. Use `30m`, `2h`, `1d`, or `1w`.",

                ephemeral=True
            )

            return


        reminder_id = create_reminder(

            user_id=interaction.user.id,

            guild_id=interaction.guild.id,

            channel_id=interaction.channel.id,

            message=message,

            scheduled_at=scheduled_at,

            timezone_name="UTC",

            recurring=True,

            recurrence=recurrence
        )


        embed = discord.Embed(

            title="🔁 Recurring Message Created",

            description=(
                "The message will be posted automatically."
            ),

            color=discord.Color.from_rgb(
                220,
                38,
                38
            )
        )


        embed.add_field(
            name="📝 Message",
            value=message,
            inline=False
        )


        embed.add_field(
            name="⏰ First Run",
            value=format_timestamp(
                scheduled_at
            ),
            inline=False
        )


        embed.add_field(
            name="🔁 Repeats",
            value=recurrence.title(),
            inline=True
        )


        embed.add_field(
            name="📍 Channel",
            value=interaction.channel.mention,
            inline=True
        )


        embed.add_field(
            name="🆔 ID",
            value=f"`#{reminder_id}`",
            inline=True
        )


        embed.set_footer(
            text="Straw Hat • Scheduled Messages"
        )


        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


# ============================================================
# EXTENSION SETUP
# ============================================================

async def setup(
    bot
):

    await bot.add_cog(
        Reminders(bot)
    )