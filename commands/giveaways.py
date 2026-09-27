import time

import discord
from discord import app_commands
from discord.ext import commands, tasks

from config.banners import GIVEAWAY_BANNER
from database import giveaway_db
from services import giveaway_service
from services.giveaway_views import GiveawayView


RED = discord.Color.from_rgb(
    220,
    38,
    38,
)


class Giveaways(commands.GroupCog, name="giveaway"):
    """
    Straw Hat giveaway system.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        if not self.giveaway_loop.is_running():
            self.giveaway_loop.start()

    def cog_unload(self):
        self.giveaway_loop.cancel()

    @app_commands.command(
        name="create",
        description="Create a new Straw Hat giveaway.",
    )
    @app_commands.describe(
        prize="What is being given away?",
        duration="Duration such as 10m, 1h, 24h, 3d or 1w.",
        winners="Number of winners.",
        channel="Channel where the giveaway will be posted.",
    )
    async def create(
        self,
        interaction: discord.Interaction,
        prize: str,
        duration: str,
        winners: app_commands.Range[int, 1, 20],
        channel: discord.TextChannel | None = None,
    ):
        if not isinstance(interaction.user, discord.Member):
            return

        if not giveaway_service.can_manage_giveaway(
            interaction.user
        ):
            embed = discord.Embed(
                title="🚫 ACCESS DENIED",
                description=(
                    "You don't have permission to manage giveaways.\n\n"
                    "> ⚓ Giveaway management is restricted "
                    "to the Captain, Crew, and Marines."
                ),
                color=RED,
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True,
            )

            return

        duration_seconds = giveaway_service.parse_duration(
            duration
        )

        if duration_seconds is None:
            embed = discord.Embed(
                title="❌ INVALID GIVEAWAY",
                description=(
                    f"The duration `{duration}` is invalid.\n\n"
                    "> 💡 Use a duration such as:\n"
                    "> `10m` • `1h` • `24h` • `3d` • `1w`"
                ),
                color=RED,
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True,
            )

            return

        if duration_seconds < 60:
            embed = discord.Embed(
                title="❌ INVALID DURATION",
                description=(
                    "A giveaway must last at least **1 minute**."
                ),
                color=RED,
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True,
            )

            return

        if duration_seconds > 30 * 24 * 60 * 60:
            embed = discord.Embed(
                title="❌ INVALID DURATION",
                description=(
                    "A giveaway cannot last longer than **30 days**."
                ),
                color=RED,
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True,
            )

            return

        target_channel = channel or interaction.channel

        if not isinstance(
            target_channel,
            discord.TextChannel,
        ):
            await interaction.response.send_message(
                "❌ Invalid giveaway channel.",
                ephemeral=True,
            )

            return

        giveaway_id = giveaway_service.create_giveaway(
            guild_id=interaction.guild.id,
            channel_id=target_channel.id,
            prize=prize,
            host_id=interaction.user.id,
            winner_count=winners,
            duration_seconds=duration_seconds,
        )

        ends_at = int(time.time()) + duration_seconds

        embed = discord.Embed(
            title="🎁 GIVEAWAY",
            description=(
                "🏴‍☠️ **A new treasure has appeared!**\n\n"
                "> ⚓ Gather your crew and enter!\n"
                "> Everyone has a chance to claim the treasure."
            ),
            color=RED,
        )

        embed.add_field(
            name="🎁 PRIZE",
            value=prize,
            inline=False,
        )

        embed.add_field(
            name="🏆 WINNERS",
            value=str(winners),
            inline=True,
        )

        embed.add_field(
            name="👑 HOSTED BY",
            value=interaction.user.mention,
            inline=True,
        )

        embed.add_field(
            name="⏰ ENDS",
            value=f"<t:{ends_at}:R>\n<t:{ends_at}:F>",
            inline=False,
        )

        embed.add_field(
            name="👥 ENTRIES",
            value="0",
            inline=True,
        )

        embed.set_thumbnail(
            url=self.bot.user.display_avatar.url
        )

        if GIVEAWAY_BANNER:
            embed.set_image(
                url=GIVEAWAY_BANNER
            )

        embed.set_footer(
            text=f"Straw Hat Giveaway • ID #{giveaway_id:04d}"
        )

        message = await target_channel.send(
            embed=embed,
            view=GiveawayView(giveaway_id),
        )

        giveaway_db.set_message_id(
            giveaway_id,
            message.id,
        )

        confirmation = discord.Embed(
            title="🎁 GIVEAWAY CREATED",
            description=(
                f"Your giveaway has been successfully launched "
                f"in {target_channel.mention}!\n\n"
                "> 🏴‍☠️ The treasure has been released!"
            ),
            color=RED,
        )

        confirmation.add_field(
            name="🎁 Prize",
            value=prize,
            inline=False,
        )

        confirmation.add_field(
            name="🏆 Winners",
            value=str(winners),
            inline=True,
        )

        confirmation.add_field(
            name="⏰ Duration",
            value=duration,
            inline=True,
        )

        await interaction.response.send_message(
            embed=confirmation,
            ephemeral=True,
        )

    @app_commands.command(
        name="end",
        description="End an active giveaway immediately.",
    )
    @app_commands.describe(
        giveaway_id="The giveaway ID.",
    )
    async def end(
        self,
        interaction: discord.Interaction,
        giveaway_id: int,
    ):
        if not isinstance(interaction.user, discord.Member):
            return

        if not giveaway_service.can_manage_giveaway(
            interaction.user
        ):
            await self.permission_error(interaction)
            return

        result = giveaway_service.end_giveaway(
            giveaway_id
        )

        if not result[0]:
            embed = discord.Embed(
                title="❌ GIVEAWAY NOT FOUND",
                description=(
                    "That giveaway does not exist or is no longer active."
                ),
                color=RED,
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True,
            )

            return

        giveaway, winners = result

        await self.update_ended_message(
            giveaway,
            winners,
        )

        winner_text = (
            "\n".join(
                f"🏆 <@{user_id}>"
                for user_id in winners
            )
            if winners
            else "No winners"
        )

        embed = discord.Embed(
            title="🏁 GIVEAWAY ENDED",
            description=(
                "The giveaway has been manually ended."
            ),
            color=RED,
        )

        embed.add_field(
            name="🎁 Prize",
            value=giveaway[4],
            inline=False,
        )

        embed.add_field(
            name="🏆 Winners",
            value=winner_text,
            inline=False,
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
        )

    @app_commands.command(
        name="cancel",
        description="Cancel an active giveaway.",
    )
    @app_commands.describe(
        giveaway_id="The giveaway ID.",
    )
    async def cancel(
        self,
        interaction: discord.Interaction,
        giveaway_id: int,
    ):
        if not isinstance(interaction.user, discord.Member):
            return

        if not giveaway_service.can_cancel_giveaway(
            interaction.user
        ):
            await self.permission_error(interaction)
            return

        giveaway = giveaway_service.cancel_giveaway(
            giveaway_id
        )

        if not giveaway:
            embed = discord.Embed(
                title="❌ GIVEAWAY NOT FOUND",
                description=(
                    "That giveaway does not exist or is no longer active."
                ),
                color=RED,
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True,
            )

            return

        await self.update_cancelled_message(
            giveaway
        )

        embed = discord.Embed(
            title="🚫 GIVEAWAY CANCELLED",
            description=(
                f"Giveaway `#{giveaway_id:04d}` has been cancelled."
            ),
            color=RED,
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
        )

    @app_commands.command(
        name="reroll",
        description="Select another winner for a giveaway.",
    )
    @app_commands.describe(
        giveaway_id="The giveaway ID.",
    )
    async def reroll(
        self,
        interaction: discord.Interaction,
        giveaway_id: int,
    ):
        if not isinstance(interaction.user, discord.Member):
            return

        if not giveaway_service.can_manage_giveaway(
            interaction.user
        ):
            await self.permission_error(interaction)
            return

        giveaway = giveaway_db.get_giveaway(
            giveaway_id
        )

        if not giveaway:
            embed = discord.Embed(
                title="❌ GIVEAWAY NOT FOUND",
                description="That giveaway does not exist.",
                color=RED,
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True,
            )

            return

        winner = giveaway_service.reroll_winner(
            giveaway_id
        )

        if winner is None:
            embed = discord.Embed(
                title="❌ CANNOT REROLL",
                description=(
                    "There are no eligible participants remaining.\n\n"
                    "> ⚠️ Everyone who entered has already "
                    "been selected."
                ),
                color=RED,
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True,
            )

            return

        embed = discord.Embed(
            title="🔄 GIVEAWAY REROLLED",
            description=(
                "A new winner has been selected.\n\n"
                f"🏆 **New Winner:** <@{winner}>\n\n"
                "> ☠️ The Grand Line has chosen another pirate!"
            ),
            color=RED,
        )

        embed.add_field(
            name="🎁 Prize",
            value=giveaway[4],
            inline=False,
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
        )

        await self.send_reroll_public(
            giveaway,
            winner,
        )

    @app_commands.command(
        name="info",
        description="View information about a giveaway.",
    )
    @app_commands.describe(
        giveaway_id="The giveaway ID.",
    )
    async def info(
        self,
        interaction: discord.Interaction,
        giveaway_id: int,
    ):
        giveaway = giveaway_db.get_giveaway(
            giveaway_id
        )

        if not giveaway:
            embed = discord.Embed(
                title="❌ GIVEAWAY NOT FOUND",
                description="That giveaway does not exist.",
                color=RED,
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True,
            )

            return

        entry_count = giveaway_db.get_entry_count(
            giveaway_id
        )

        status = giveaway[9]

        status_display = {
            "active": "🟢 Active",
            "ended": "🏆 Ended",
            "cancelled": "🚫 Cancelled",
        }.get(
            status,
            status,
        )

        embed = discord.Embed(
            title="🎁 GIVEAWAY INFORMATION",
            color=RED,
        )

        embed.add_field(
            name="🆔 Giveaway",
            value=f"#{giveaway_id:04d}",
            inline=True,
        )

        embed.add_field(
            name="📊 Status",
            value=status_display,
            inline=True,
        )

        embed.add_field(
            name="🎁 Prize",
            value=giveaway[4],
            inline=False,
        )

        embed.add_field(
            name="👑 Host",
            value=f"<@{giveaway[5]}>",
            inline=True,
        )

        embed.add_field(
            name="👥 Entries",
            value=str(entry_count),
            inline=True,
        )

        embed.add_field(
            name="🏆 Winners",
            value=str(giveaway[6]),
            inline=True,
        )

        if status == "active":
            embed.add_field(
                name="⏰ Ends",
                value=f"<t:{giveaway[8]}:R>",
                inline=False,
            )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
        )

    async def permission_error(
        self,
        interaction: discord.Interaction,
    ):
        embed = discord.Embed(
            title="🚫 ACCESS DENIED",
            description=(
                "You don't have permission to manage giveaways.\n\n"
                "> ⚓ Giveaway management is restricted "
                "to the Captain, Crew, and Marines."
            ),
            color=RED,
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
        )

    async def update_ended_message(
        self,
        giveaway,
        winners,
    ):
        channel = self.bot.get_channel(
            giveaway[2]
        )

        if not isinstance(
            channel,
            discord.TextChannel,
        ):
            return

        try:
            message = await channel.fetch_message(
                giveaway[3]
            )
        except discord.NotFound:
            return

        winner_text = (
            "\n".join(
                f"🏆 <@{user_id}>"
                for user_id in winners
            )
            if winners
            else "No winners"
        )

        entry_count = giveaway_db.get_entry_count(
            giveaway[0]
        )

        embed = discord.Embed(
            title="🏆 GIVEAWAY ENDED",
            description=(
                "The treasure has been claimed!\n\n"
                "> 🎉 Congratulations to the winners!"
            ),
            color=RED,
        )

        embed.add_field(
            name="🎁 PRIZE",
            value=giveaway[4],
            inline=False,
        )

        embed.add_field(
            name="👥 ENTRIES",
            value=str(entry_count),
            inline=True,
        )

        embed.add_field(
            name="🏆 WINNERS",
            value=winner_text,
            inline=False,
        )

        embed.set_footer(
            text=f"Straw Hat Giveaway • ID #{giveaway[0]:04d}"
        )

        await message.edit(
            embed=embed,
            view=None,
        )

    async def update_cancelled_message(
        self,
        giveaway,
    ):
        channel = self.bot.get_channel(
            giveaway[2]
        )

        if not isinstance(
            channel,
            discord.TextChannel,
        ):
            return

        try:
            message = await channel.fetch_message(
                giveaway[3]
            )
        except discord.NotFound:
            return

        entry_count = giveaway_db.get_entry_count(
            giveaway[0]
        )

        embed = discord.Embed(
            title="🚫 GIVEAWAY CANCELLED",
            description=(
                "> ⚓ This voyage has been cancelled.\n"
                "> No winners will be selected."
            ),
            color=RED,
        )

        embed.add_field(
            name="🎁 PRIZE",
            value=giveaway[4],
            inline=False,
        )

        embed.add_field(
            name="👥 ENTRIES",
            value=str(entry_count),
            inline=True,
        )

        embed.set_footer(
            text=f"Straw Hat Giveaway • ID #{giveaway[0]:04d}"
        )

        await message.edit(
            embed=embed,
            view=None,
        )

    async def send_reroll_public(
        self,
        giveaway,
        winner_id,
    ):
        channel = self.bot.get_channel(
            giveaway[2]
        )

        if not isinstance(
            channel,
            discord.TextChannel,
        ):
            return

        embed = discord.Embed(
            title="🔄 GIVEAWAY REROLLED",
            description=(
                f"🏆 **New Winner:** <@{winner_id}>\n\n"
                "> 🏴‍☠️ A new pirate has claimed the treasure!"
            ),
            color=RED,
        )

        embed.add_field(
            name="🎁 Prize",
            value=giveaway[4],
            inline=False,
        )

        await channel.send(
            embed=embed
        )

    @tasks.loop(seconds=30)
    async def giveaway_loop(self):
        expired = giveaway_db.get_ended_giveaways()

        for giveaway in expired:
            try:
                result = giveaway_service.end_giveaway(
                    giveaway[0]
                )

                ended_giveaway, winners = result

                if ended_giveaway:
                    await self.update_ended_message(
                        ended_giveaway,
                        winners,
                    )

            except Exception as error:
                print(
                    f"[Giveaway] Failed to end "
                    f"giveaway #{giveaway[0]}: {error}"
                )

    @giveaway_loop.before_loop
    async def before_giveaway_loop(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(
        Giveaways(bot)
    )

