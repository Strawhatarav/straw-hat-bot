import asyncio
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands

from config.banners import POLL_BANNER
from services import poll_service

from services.poll_views import (
    PollView,
    build_results_embed,
    PollCloseConfirmationView
)


RED = discord.Color.from_rgb(
    190,
    35,
    45
)


def build_banner_embed() -> discord.Embed:
    """
    Creates a separate image-only embed.

    This makes the poll banner appear ABOVE
    the actual poll embed.
    """

    embed = discord.Embed(
        color=RED
    )

    embed.set_image(
        url=POLL_BANNER
    )

    return embed


def build_poll_embed(
    poll: dict
) -> discord.Embed:

    embed = discord.Embed(
        title="📊 Straw Hat Poll",
        description=(
            f"**{poll['question']}**"
        ),
        color=RED
    )

    # Add poll options
    for index, option in enumerate(
        poll["options"],
        start=1
    ):

        embed.add_field(
            name=f"{index}. {option}",
            value="Select your choice below.",
            inline=False
        )

    # Voting type
    voting_type = (
        "Multiple choice"
        if poll["multiple_choice"]
        else "Single choice"
    )

    # Privacy type
    privacy = (
        "Anonymous"
        if poll["anonymous"]
        else "Non-anonymous"
    )

    embed.add_field(
        name="🗳️ Voting",
        value=voting_type,
        inline=True
    )

    embed.add_field(
        name="🔐 Privacy",
        value=privacy,
        inline=True
    )

    # End time
    if poll["ends_at"]:

        timestamp = int(
            poll["ends_at"].timestamp()
        )

        embed.add_field(
            name="⏰ Ends",
            value=f"<t:{timestamp}:R>",
            inline=True
        )

    else:

        embed.add_field(
            name="⏰ Ends",
            value="No time limit",
            inline=True
        )

    # IMPORTANT:
    # We deliberately DO NOT use embed.set_image()
    # here.
    #
    # The banner is now a separate message above
    # this embed.

    embed.set_footer(
        text=(
            f"Straw Hat • Poll #{poll['id']}"
        )
    )

    return embed


async def close_expired_poll(
    bot,
    poll: dict
):

    poll_service.close_poll(
        poll["id"]
    )

    channel = bot.get_channel(
        poll["channel_id"]
    )

    if channel is None:
        return

    try:

        message = await channel.fetch_message(
            poll["message_id"]
        )

        updated_poll = (
            poll_service.get_poll(
                poll["id"]
            )
        )

        if updated_poll is None:
            return

        embed = build_results_embed(
            updated_poll
        )

        embed.title = (
            "🔒 Poll Closed — Final Results"
        )

        await message.edit(
            embed=embed,
            view=None
        )

    except discord.NotFound:

        pass

    except discord.Forbidden:

        print(
            f"❌ No permission to update "
            f"poll {poll['id']}."
        )

    except Exception as error:

        print(
            f"❌ Failed to close poll "
            f"{poll['id']}: {error}"
        )


class Poll(commands.GroupCog):

    def __init__(
        self,
        bot
    ):

        self.bot = bot

        self.poll_task = (
            self.bot.loop.create_task(
                self.poll_checker()
            )
        )

    async def cog_unload(
        self
    ):

        if not self.poll_task.done():

            self.poll_task.cancel()

    async def poll_checker(
        self
    ):

        await self.bot.wait_until_ready()

        while not self.bot.is_closed():

            try:

                expired_polls = (
                    poll_service.get_expired_polls()
                )

                for poll in expired_polls:

                    await close_expired_poll(
                        self.bot,
                        poll
                    )

            except asyncio.CancelledError:

                return

            except Exception as error:

                print(
                    f"❌ Poll checker error: {error}"
                )

            await asyncio.sleep(15)

    @app_commands.command(
        name="create",
        description="Create a Straw Hat poll."
    )
    @app_commands.describe(
        question=(
            "The question you want to ask."
        ),
        options=(
            "Options separated by commas."
        ),
        duration=(
            "Duration in minutes. "
            "Use 0 for no time limit."
        ),
        multiple_choice=(
            "Allow members to select multiple options."
        ),
        anonymous=(
            "Hide voter identities from public results."
        )
    )
    async def create(
        self,
        interaction: discord.Interaction,
        question: str,
        options: str,
        duration: int = 0,
        multiple_choice: bool = False,
        anonymous: bool = False
    ):

        # Make sure this is being used inside a server
        if interaction.guild is None:

            await interaction.response.send_message(
                "❌ This command can only be used inside a server.",
                ephemeral=True
            )

            return

        # Clean question
        question = question.strip()

        if not question:

            await interaction.response.send_message(
                "❌ The poll question cannot be empty.",
                ephemeral=True
            )

            return

        if len(question) > 300:

            await interaction.response.send_message(
                "❌ The poll question cannot exceed 300 characters.",
                ephemeral=True
            )

            return

        # Convert comma-separated options into a list
        parsed_options = [
            option.strip()
            for option in options.split(",")
            if option.strip()
        ]

        # Minimum options
        if len(parsed_options) < 2:

            await interaction.response.send_message(
                "❌ A poll needs at least 2 options.",
                ephemeral=True
            )

            return

        # Maximum options
        if len(parsed_options) > 10:

            await interaction.response.send_message(
                "❌ A poll can have at most 10 options.",
                ephemeral=True
            )

            return

        # Maximum option length
        if any(
            len(option) > 80
            for option in parsed_options
        ):

            await interaction.response.send_message(
                "❌ Each option must be 80 characters or fewer.",
                ephemeral=True
            )

            return

        # Check duplicate options
        normalized_options = [
            option.casefold()
            for option in parsed_options
        ]

        if (
            len(normalized_options)
            != len(set(normalized_options))
        ):

            await interaction.response.send_message(
                "❌ Poll options must be unique.",
                ephemeral=True
            )

            return

        # Validate duration
        if duration < 0:

            await interaction.response.send_message(
                "❌ Duration cannot be negative.",
                ephemeral=True
            )

            return

        # Maximum 7 days
        if duration > 10080:

            await interaction.response.send_message(
                "❌ Maximum poll duration is 7 days.",
                ephemeral=True
            )

            return

        # Calculate end time
        ends_at = None

        if duration > 0:

            ends_at = (
                datetime.now(timezone.utc)
                + timedelta(
                    minutes=duration
                )
            )

        # Create database record
        poll_id = (
            poll_service.create_poll(
                guild_id=interaction.guild.id,
                channel_id=interaction.channel.id,
                creator_id=interaction.user.id,
                question=question,
                options=parsed_options,
                multiple_choice=multiple_choice,
                anonymous=anonymous,
                ends_at=ends_at
            )
        )

        # Retrieve newly created poll
        poll = poll_service.get_poll(
            poll_id
        )

        if poll is None:

            await interaction.response.send_message(
                "❌ Something went wrong while creating the poll.",
                ephemeral=True
            )

            return

        # Build poll embed
        poll_embed = build_poll_embed(
            poll
        )

        # Build interactive view
        view = PollView(
            poll_id=poll["id"],
            options=poll["options"],
            multiple_choice=(
                poll["multiple_choice"]
            )
        )

        # ------------------------------------------------
        # SEND THE BANNER FIRST
        # ------------------------------------------------

        banner_embed = build_banner_embed()

        await interaction.response.send_message(
            embed=banner_embed
        )

        # ------------------------------------------------
        # SEND THE ACTUAL POLL AFTER THE BANNER
        # ------------------------------------------------

        poll_message = await interaction.followup.send(
            embed=poll_embed,
            view=view,
            wait=True
        )

        # Save the poll message ID
        poll_service.set_poll_message_id(
            poll_id,
            poll_message.id
        )

    @app_commands.command(
        name="results",
        description="View the results of a poll."
    )
    @app_commands.describe(
        poll_id="The poll ID."
    )
    async def results(
        self,
        interaction: discord.Interaction,
        poll_id: int
    ):

        poll = poll_service.get_poll(
            poll_id
        )

        if poll is None:

            await interaction.response.send_message(
                "❌ Poll not found.",
                ephemeral=True
            )

            return

        if (
            interaction.guild is None
            or poll["guild_id"]
            != interaction.guild.id
        ):

            await interaction.response.send_message(
                "❌ This poll does not belong to this server.",
                ephemeral=True
            )

            return

        embed = build_results_embed(
            poll
        )

        if poll["closed"]:

            embed.title = (
                "🔒 Poll Results"
            )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

    @app_commands.command(
        name="close",
        description="Close a poll."
    )
    @app_commands.describe(
        poll_id="The poll ID to close."
    )
    async def close(
        self,
        interaction: discord.Interaction,
        poll_id: int
    ):

        poll = poll_service.get_poll(
            poll_id
        )

        if poll is None:

            await interaction.response.send_message(
                "❌ Poll not found.",
                ephemeral=True
            )

            return

        if (
            interaction.guild is None
            or poll["guild_id"]
            != interaction.guild.id
        ):

            await interaction.response.send_message(
                "❌ This poll does not belong to this server.",
                ephemeral=True
            )

            return

        if poll["closed"]:

            await interaction.response.send_message(
                "🔒 This poll is already closed.",
                ephemeral=True
            )

            return

        # Poll creator
        is_creator = (
            interaction.user.id
            == poll["creator_id"]
        )

        # Server manager
        can_manage = (
            interaction.user.guild_permissions.manage_guild
        )

        if not (
            is_creator
            or can_manage
        ):

            await interaction.response.send_message(
                "❌ Only the poll creator or a member "
                "with Manage Server permission can close this poll.",
                ephemeral=True
            )

            return

        # Confirmation
        await interaction.response.send_message(
            "⚠️ Are you sure you want to close this poll?",
            view=PollCloseConfirmationView(
                poll_id
            ),
            ephemeral=True
        )


async def setup(
    bot
):

    await bot.add_cog(
        Poll(bot)
    )