# ============================================================
# STRAW HAT TICKET COMMANDS
# ============================================================

import discord

from discord.ext import commands
from discord import app_commands

from services.ticket_service import (
    save_ticket_config,
    get_ticket_config,
    disable_ticket_system
)

from services.embed_service import (
    create_embed,
    RED,
    GREEN,
    YELLOW
)

from config.banners import (
    TICKET_BANNER
)

from views.ticket_views import (
    TicketPanelView
)


# ============================================================
# TICKET COMMANDS
# ============================================================

class Tickets(commands.Cog):

    def __init__(
        self,
        bot
    ):

        self.bot = bot


    # ========================================================
    # /ticketsetup
    # ========================================================

    @app_commands.command(
        name="ticketsetup",
        description="Configure the Straw Hat ticket system."
    )
    @app_commands.checks.has_permissions(
        manage_guild=True
    )
    @app_commands.describe(
        panel_channel="Channel where the ticket panel will be placed.",
        ticket_category="Category where ticket channels will be created.",
        staff_role="Role that can access and manage tickets.",
        log_channel="Private channel for ticket logs and transcripts."
    )
    async def ticketsetup(
        self,
        interaction: discord.Interaction,
        panel_channel: discord.TextChannel,
        ticket_category: discord.CategoryChannel,
        staff_role: discord.Role,
        log_channel: discord.TextChannel
    ):

        guild = interaction.guild

        if guild is None:

            await interaction.response.send_message(
                "❌ This command can only be used in a server.",
                ephemeral=True
            )

            return

        save_ticket_config(
            guild.id,
            panel_channel.id,
            ticket_category.id,
            staff_role.id,
            log_channel.id
        )

        embed = create_embed(
            title="⚙️ Ticket System Configured",
            description=(
                "The Straw Hat ticket system has been configured "
                "successfully."
            ),
            color=GREEN,
            banner_url=TICKET_BANNER,
            footer_text="Straw Hat • Ticket Configuration"
        )

        embed.add_field(
            name="🎫 Panel Channel",
            value=panel_channel.mention,
            inline=False
        )

        embed.add_field(
            name="📂 Ticket Category",
            value=ticket_category.name,
            inline=False
        )

        embed.add_field(
            name="👮 Staff Role",
            value=staff_role.mention,
            inline=False
        )

        embed.add_field(
            name="📜 Log Channel",
            value=log_channel.mention,
            inline=False
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


    # ========================================================
    # /ticketconfig
    # ========================================================

    @app_commands.command(
        name="ticketconfig",
        description="View the current ticket configuration."
    )
    @app_commands.checks.has_permissions(
        manage_guild=True
    )
    async def ticketconfig(
        self,
        interaction: discord.Interaction
    ):

        guild = interaction.guild

        if guild is None:

            await interaction.response.send_message(
                "❌ This command can only be used in a server.",
                ephemeral=True
            )

            return

        config = get_ticket_config(
            guild.id
        )

        if config is None:

            await interaction.response.send_message(
                embed=create_embed(
                    title="⚠️ Ticket System Not Configured",
                    description=(
                        "Use `/ticketsetup` first."
                    ),
                    color=YELLOW,
                    footer_text="Straw Hat • Ticket System"
                ),
                ephemeral=True
            )

            return

        (
            guild_id,
            panel_channel_id,
            ticket_category_id,
            staff_role_id,
            log_channel_id,
            enabled
        ) = config

        panel_channel = guild.get_channel(
            panel_channel_id
        )

        ticket_category = guild.get_channel(
            ticket_category_id
        )

        staff_role = guild.get_role(
            staff_role_id
        )

        log_channel = guild.get_channel(
            log_channel_id
        )

        embed = create_embed(
            title="⚙️ Ticket Configuration",
            description=(
                f"Current ticket configuration for "
                f"**{guild.name}**."
            ),
            color=RED,
            banner_url=TICKET_BANNER,
            thumbnail_url=(
                guild.icon.url
                if guild.icon
                else None
            ),
            footer_text="Straw Hat • Ticket Configuration"
        )

        embed.add_field(
            name="🟢 Status",
            value=(
                "Enabled"
                if enabled
                else "Disabled"
            ),
            inline=True
        )

        embed.add_field(
            name="🎫 Panel Channel",
            value=(
                panel_channel.mention
                if panel_channel
                else "Missing"
            ),
            inline=False
        )

        embed.add_field(
            name="📂 Ticket Category",
            value=(
                ticket_category.name
                if ticket_category
                else "Missing"
            ),
            inline=False
        )

        embed.add_field(
            name="👮 Staff Role",
            value=(
                staff_role.mention
                if staff_role
                else "Missing"
            ),
            inline=False
        )

        embed.add_field(
            name="📜 Log Channel",
            value=(
                log_channel.mention
                if log_channel
                else "Missing"
            ),
            inline=False
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


    # ========================================================
    # /ticketpanel
    # ========================================================

    @app_commands.command(
        name="ticketpanel",
        description="Send the Straw Hat ticket panel."
    )
    @app_commands.checks.has_permissions(
        manage_guild=True
    )
    async def ticketpanel(
        self,
        interaction: discord.Interaction
    ):

        guild = interaction.guild

        if guild is None:

            await interaction.response.send_message(
                "❌ This command can only be used in a server.",
                ephemeral=True
            )

            return

        config = get_ticket_config(
            guild.id
        )

        if config is None or not config[5]:

            await interaction.response.send_message(
                embed=create_embed(
                    title="⚠️ Ticket System Not Ready",
                    description=(
                        "Please configure the ticket system "
                        "with `/ticketsetup` first."
                    ),
                    color=YELLOW,
                    footer_text="Straw Hat • Ticket System"
                ),
                ephemeral=True
            )

            return

        panel_channel = guild.get_channel(
            config[1]
        )

        if not isinstance(
            panel_channel,
            discord.TextChannel
        ):

            await interaction.response.send_message(
                "❌ The configured panel channel is invalid.",
                ephemeral=True
            )

            return

        embed = create_embed(
            title="🎫 Straw Hat Support",
            description=(
                "Need help from the Crew? 🏴‍☠️\n\n"
                "Open a ticket if you need assistance, "
                "want to report a bug, appeal a moderation "
                "action, or have a suggestion.\n\n"
                "Select the appropriate category below."
            ),
            color=RED,
            banner_url=TICKET_BANNER,
            thumbnail_url=(
                guild.icon.url
                if guild.icon
                else None
            ),
            footer_text="Straw Hat • Support Desk"
        )

        embed.add_field(
            name="🎫 Available Tickets",
            value=(
                "🎫 **Support** — General assistance\n"
                "🐛 **Report Bug** — Bot/server problems\n"
                "🛡️ **Moderation Appeal** — Appeal a moderation action\n"
                "💡 **Suggestion** — Suggest an improvement"
            ),
            inline=False
        )

        await panel_channel.send(
            embed=embed,
            view=TicketPanelView()
        )

        await interaction.response.send_message(
            embed=create_embed(
                title="✅ Ticket Panel Sent",
                description=(
                    f"The ticket panel has been sent to "
                    f"{panel_channel.mention}."
                ),
                color=GREEN,
                footer_text="Straw Hat • Ticket System"
            ),
            ephemeral=True
        )


    # ========================================================
    # /ticketdisable
    # ========================================================

    @app_commands.command(
        name="ticketdisable",
        description="Disable the Straw Hat ticket system."
    )
    @app_commands.checks.has_permissions(
        manage_guild=True
    )
    async def ticketdisable(
        self,
        interaction: discord.Interaction
    ):

        guild = interaction.guild

        if guild is None:

            await interaction.response.send_message(
                "❌ This command can only be used in a server.",
                ephemeral=True
            )

            return

        disable_ticket_system(
            guild.id
        )

        await interaction.response.send_message(
            embed=create_embed(
                title="🔴 Ticket System Disabled",
                description=(
                    "New tickets can no longer be created.\n\n"
                    "Existing tickets are not deleted."
                ),
                color=RED,
                footer_text="Straw Hat • Ticket System"
            ),
            ephemeral=True
        )


    # ========================================================
    # PERMISSION ERROR HANDLER
    # ========================================================

    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ):

        if isinstance(
            error,
            app_commands.errors.MissingPermissions
        ):

            if interaction.response.is_done():

                await interaction.followup.send(
                    embed=create_embed(
                        title="🛡️ Permission Denied",
                        description=(
                            "You need **Manage Server** permission "
                            "to use this command."
                        ),
                        color=YELLOW,
                        footer_text="Straw Hat • Permissions"
                    ),
                    ephemeral=True
                )

            else:

                await interaction.response.send_message(
                    embed=create_embed(
                        title="🛡️ Permission Denied",
                        description=(
                            "You need **Manage Server** permission "
                            "to use this command."
                        ),
                        color=YELLOW,
                        footer_text="Straw Hat • Permissions"
                    ),
                    ephemeral=True
                )

            return

        raise error


# ============================================================
# SETUP
# ============================================================

async def setup(
    bot
):

    await bot.add_cog(
        Tickets(bot)
    )