# ============================================================
# STRAW HAT TICKET VIEWS
# ============================================================

import discord
import io
import html

from services.ticket_service import (
    get_ticket_config,
    get_open_ticket,
    get_ticket_by_channel,
    get_next_ticket_number,
    create_ticket,
    claim_ticket,
    unclaim_ticket,
    close_ticket,
    reopen_ticket,
    delete_ticket_record
)

from services.embed_service import (
    create_embed,
    RED,
    GREEN,
    YELLOW
)

from config.banners import TICKET_BANNER


# ============================================================
# CATEGORY INFORMATION
# ============================================================

TICKET_CATEGORIES = {

    "support": {
        "name": "Support",
        "emoji": "🎫",
        "description": "Get help from the Straw Hat Crew.",
        "prefix": "support"
    },

    "bug": {
        "name": "Report Bug",
        "emoji": "🐛",
        "description": "Report a problem with the server or bot.",
        "prefix": "bug"
    },

    "appeal": {
        "name": "Moderation Appeal",
        "emoji": "🛡️",
        "description": "Request a review of a moderation action.",
        "prefix": "appeal"
    },

    "suggestion": {
        "name": "Suggestion",
        "emoji": "💡",
        "description": "Suggest an improvement for Straw Hats.",
        "prefix": "suggestion"
    }
}


# ============================================================
# TRANSCRIPT GENERATOR
# ============================================================

async def generate_transcript(
    channel: discord.TextChannel
):

    messages = []

    async for message in channel.history(
        limit=None,
        oldest_first=True
    ):

        content = html.escape(
            message.content or ""
        )

        timestamp = message.created_at.strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )

        attachments = ""

        for attachment in message.attachments:

            attachments += (
                f'<div>'
                f'📎 <a href="{html.escape(attachment.url)}">'
                f'{html.escape(attachment.filename)}'
                f'</a>'
                f'</div>'
            )

        messages.append(
            f"""
            <div class="message">
                <div class="author">
                    {html.escape(message.author.display_name)}
                </div>

                <div class="time">
                    {timestamp}
                </div>

                <div class="content">
                    {content}
                </div>

                {attachments}
            </div>
            """
        )

    transcript = f"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<title>
Straw Hat Ticket Transcript
</title>

<style>

body {{
    background: #111827;
    color: #f9fafb;
    font-family: Arial, sans-serif;
    padding: 30px;
}}

.header {{
    border-left: 6px solid #dc2626;
    padding-left: 15px;
    margin-bottom: 30px;
}}

.message {{
    background: #1f2937;
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 12px;
}}

.author {{
    font-weight: bold;
    color: #f87171;
}}

.time {{
    font-size: 12px;
    color: #9ca3af;
    margin-bottom: 8px;
}}

.content {{
    white-space: pre-wrap;
}}

a {{
    color: #60a5fa;
}}

</style>

</head>

<body>

<div class="header">

<h1>
🏴‍☠️ Straw Hat Ticket Transcript
</h1>

<p>
Ticket: #{html.escape(channel.name)}
</p>

</div>

{"".join(messages)}

</body>

</html>
"""

    return transcript


# ============================================================
# TICKET PANEL SELECT
# ============================================================

class TicketCategorySelect(
    discord.ui.Select
):

    def __init__(self):

        options = []

        for key, data in TICKET_CATEGORIES.items():

            options.append(
                discord.SelectOption(
                    label=data["name"],
                    description=data["description"],
                    emoji=data["emoji"],
                    value=key
                )
            )

        super().__init__(
            placeholder="🎫 Select a ticket category...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="strawhat_ticket_category"
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        guild = interaction.guild

        if guild is None:

            await interaction.response.send_message(
                "❌ This can only be used inside a server.",
                ephemeral=True
            )

            return

        config = get_ticket_config(
            guild.id
        )

        if config is None or not config[5]:

            await interaction.response.send_message(
                "⚠️ The ticket system is currently disabled.",
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

        category_key = self.values[0]

        category_data = TICKET_CATEGORIES[
            category_key
        ]

        existing_ticket = get_open_ticket(
            guild.id,
            interaction.user.id
        )

        if existing_ticket:

            channel_id = existing_ticket[3]

            channel = guild.get_channel(
                channel_id
            )

            channel_text = (
                channel.mention
                if channel
                else "your existing ticket"
            )

            await interaction.response.send_message(
                embed=create_embed(
                    title="⚠️ Ticket Already Open",
                    description=(
                        "You already have an open ticket.\n\n"
                        f"🎫 **Ticket:** {channel_text}\n\n"
                        "Please use your existing ticket before "
                        "creating another one."
                    ),
                    color=YELLOW,
                    footer_text="Straw Hat • Ticket System"
                ),
                ephemeral=True
            )

            return

        ticket_category = guild.get_channel(
            ticket_category_id
        )

        staff_role = guild.get_role(
            staff_role_id
        )

        if not isinstance(
            ticket_category,
            discord.CategoryChannel
        ):

            await interaction.response.send_message(
                "❌ The configured ticket category is invalid.",
                ephemeral=True
            )

            return

        if staff_role is None:

            await interaction.response.send_message(
                "❌ The configured staff role no longer exists.",
                ephemeral=True
            )

            return

        ticket_number = get_next_ticket_number(
            guild.id
        )

        channel_name = (
            f"{category_data['prefix']}-"
            f"{ticket_number:03d}"
        )

        bot_member = guild.me

        overwrites = {

            guild.default_role:
                discord.PermissionOverwrite(
                    view_channel=False
                ),

            interaction.user:
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True
                ),

            staff_role:
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True
                ),

            bot_member:
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    manage_channels=True,
                    manage_messages=True,
                    attach_files=True,
                    embed_links=True
                )
        }

        try:

            channel = await guild.create_text_channel(
                name=channel_name,
                category=ticket_category,
                overwrites=overwrites,
                reason=(
                    f"Straw Hat ticket created by "
                    f"{interaction.user}"
                )
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                embed=create_embed(
                    title="❌ Ticket Creation Failed",
                    description=(
                        "I don't have permission to create "
                        "ticket channels.\n\n"
                        "Please check my **Manage Channels** "
                        "permission."
                    ),
                    color=RED,
                    footer_text="Straw Hat • Ticket System"
                ),
                ephemeral=True
            )

            return

        except discord.HTTPException:

            await interaction.response.send_message(
                embed=create_embed(
                    title="❌ Ticket Creation Failed",
                    description=(
                        "Discord rejected the channel creation "
                        "request. Please try again."
                    ),
                    color=RED,
                    footer_text="Straw Hat • Ticket System"
                ),
                ephemeral=True
            )

            return

        create_ticket(
            guild.id,
            channel.id,
            interaction.user.id,
            category_key,
            ticket_number
        )

        embed = create_embed(
            title=(
                f"{category_data['emoji']} "
                f"{category_data['name']}"
            ),
            description=(
                f"Welcome aboard, {interaction.user.mention}! "
                "🏴‍☠️\n\n"
                "Your ticket has been created successfully.\n\n"
                "Please explain your issue clearly and provide "
                "any useful information that can help the Crew."
            ),
            color=RED,
            banner_url=TICKET_BANNER,
            thumbnail_url=(
                interaction.user.display_avatar.url
            ),
            footer_text=(
                "Straw Hat • Ticket System"
            )
        )

        embed.add_field(
            name="📂 Category",
            value=category_data["name"],
            inline=True
        )

        embed.add_field(
            name="👤 Ticket Owner",
            value=interaction.user.mention,
            inline=True
        )

        embed.add_field(
            name="🕐 Created",
            value=discord.utils.format_dt(
                discord.utils.utcnow(),
                style="F"
            ),
            inline=False
        )

        await channel.send(
            content=(
                f"{interaction.user.mention} "
                f"{staff_role.mention}"
            ),
            embed=embed,
            view=TicketActionView()
        )

        await interaction.response.send_message(
            embed=create_embed(
                title="🎫 Ticket Created",
                description=(
                    "Your ticket has been created successfully!\n\n"
                    f"📂 **Category:** "
                    f"{category_data['name']}\n"
                    f"🎫 **Ticket:** {channel.mention}\n\n"
                    "Please continue inside your ticket."
                ),
                color=GREEN,
                thumbnail_url=interaction.user.display_avatar.url,
                footer_text="Straw Hat • Ticket System"
            ),
            ephemeral=True
        )

        log_channel = guild.get_channel(
            log_channel_id
        )

        if isinstance(
            log_channel,
            discord.TextChannel
        ):

            log_embed = create_embed(
                title="🎫 Ticket Created",
                description=(
                    f"{interaction.user.mention} created "
                    f"{channel.mention}."
                ),
                color=RED,
                thumbnail_url=interaction.user.display_avatar.url,
                footer_text="Straw Hat • Ticket Logs"
            )

            log_embed.add_field(
                name="📂 Category",
                value=category_data["name"],
                inline=True
            )

            log_embed.add_field(
                name="👤 User",
                value=interaction.user.mention,
                inline=True
            )

            await log_channel.send(
                embed=log_embed
            )


# ============================================================
# TICKET PANEL VIEW
# ============================================================

class TicketPanelView(
    discord.ui.View
):

    def __init__(self):

        super().__init__(
            timeout=None
        )

        self.add_item(
            TicketCategorySelect()
        )


# ============================================================
# CLOSE BUTTON
# ============================================================

class CloseTicketButton(
    discord.ui.Button
):

    def __init__(self):

        super().__init__(
            label="Close Ticket",
            emoji="🔒",
            style=discord.ButtonStyle.danger,
            custom_id="strawhat_ticket_close"
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        ticket = get_ticket_by_channel(
            interaction.channel.id
        )

        if ticket is None:

            await interaction.response.send_message(
                "❌ This is not a registered ticket.",
                ephemeral=True
            )

            return

        staff_role_id = get_ticket_config(
            interaction.guild.id
        )[3]

        is_staff = (
            interaction.user.guild_permissions.manage_guild
            or interaction.user.get_role(
                staff_role_id
            ) is not None
        )

        is_owner = (
            interaction.user.id == ticket[4]
        )

        if not is_staff and not is_owner:

            await interaction.response.send_message(
                "🛡️ You don't have permission to close this ticket.",
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            embed=create_embed(
                title="🔒 Close Ticket?",
                description=(
                    "Are you sure you want to close this ticket?\n\n"
                    "The ticket will become read-only and a "
                    "transcript will be generated."
                ),
                color=YELLOW,
                footer_text="Straw Hat • Ticket System"
            ),
            view=CloseConfirmationView(),
            ephemeral=True
        )


# ============================================================
# CLOSE CONFIRMATION
# ============================================================

class ConfirmCloseButton(
    discord.ui.Button
):

    def __init__(self):

        super().__init__(
            label="Confirm Close",
            emoji="🔒",
            style=discord.ButtonStyle.danger
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        channel = interaction.channel

        ticket = get_ticket_by_channel(
            channel.id
        )

        if ticket is None:

            await interaction.response.send_message(
                "❌ Ticket not found.",
                ephemeral=True
            )

            return

        config = get_ticket_config(
            interaction.guild.id
        )

        staff_role_id = config[3]

        staff_role = interaction.guild.get_role(
            staff_role_id
        )

        member = interaction.guild.get_member(
            ticket[4]
        )

        if member:

            await channel.set_permissions(
                member,
                send_messages=False
            )

        if staff_role:

            await channel.set_permissions(
                staff_role,
                send_messages=True
            )

        close_ticket(
            channel.id,
            interaction.user.id
        )

        transcript = await generate_transcript(
            channel
        )

        transcript_file = discord.File(
            io.BytesIO(
                transcript.encode("utf-8")
            ),
            filename=f"{channel.name}-transcript.html"
        )

        log_channel = interaction.guild.get_channel(
            config[4]
        )

        if isinstance(
            log_channel,
            discord.TextChannel
        ):

            log_embed = create_embed(
                title="🔒 Ticket Closed",
                description=(
                    f"{channel.mention} has been closed."
                ),
                color=RED,
                footer_text="Straw Hat • Ticket Logs"
            )

            log_embed.add_field(
                name="👤 Ticket Owner",
                value=(
                    member.mention
                    if member
                    else f"<@{ticket[4]}>"
                ),
                inline=True
            )

            log_embed.add_field(
                name="👮 Closed By",
                value=interaction.user.mention,
                inline=True
            )

            await log_channel.send(
                embed=log_embed,
                file=transcript_file
            )

        embed = create_embed(
            title="🔒 Ticket Closed",
            description=(
                f"This ticket has been closed by "
                f"{interaction.user.mention}.\n\n"
                "The ticket is now read-only.\n\n"
                "A transcript has been generated and sent "
                "to the staff ticket logs."
            ),
            color=RED,
            banner_url=TICKET_BANNER,
            footer_text="Straw Hat • Ticket System"
        )

        await channel.send(
            embed=embed,
            view=ClosedTicketView()
        )

        await interaction.response.edit_message(
            embed=create_embed(
                title="✅ Ticket Closed",
                description=(
                    "The ticket has been successfully closed."
                ),
                color=GREEN,
                footer_text="Straw Hat • Ticket System"
            ),
            view=None
        )


class CancelCloseButton(
    discord.ui.Button
):

    def __init__(self):

        super().__init__(
            label="Cancel",
            emoji="❌",
            style=discord.ButtonStyle.secondary
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        await interaction.response.edit_message(
            embed=create_embed(
                title="❌ Close Cancelled",
                description=(
                    "The ticket remains open."
                ),
                color=GREEN,
                footer_text="Straw Hat • Ticket System"
            ),
            view=None
        )


class CloseConfirmationView(
    discord.ui.View
):

    def __init__(self):

        super().__init__(
            timeout=60
        )

        self.add_item(
            ConfirmCloseButton()
        )

        self.add_item(
            CancelCloseButton()
        )


# ============================================================
# REOPEN BUTTON
# ============================================================

class ReopenTicketButton(
    discord.ui.Button
):

    def __init__(self):

        super().__init__(
            label="Reopen Ticket",
            emoji="🔓",
            style=discord.ButtonStyle.success,
            custom_id="strawhat_ticket_reopen"
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        ticket = get_ticket_by_channel(
            interaction.channel.id
        )

        if ticket is None:

            await interaction.response.send_message(
                "❌ Ticket not found.",
                ephemeral=True
            )

            return

        config = get_ticket_config(
            interaction.guild.id
        )

        staff_role_id = config[3]

        if (
            not interaction.user.guild_permissions.manage_guild
            and interaction.user.get_role(
                staff_role_id
            ) is None
        ):

            await interaction.response.send_message(
                "🛡️ Only Crew members can reopen tickets.",
                ephemeral=True
            )

            return

        member = interaction.guild.get_member(
            ticket[4]
        )

        if member:

            await interaction.channel.set_permissions(
                member,
                send_messages=True
            )

        reopen_ticket(
            interaction.channel.id
        )

        embed = create_embed(
            title="🔓 Ticket Reopened",
            description=(
                f"This ticket has been reopened by "
                f"{interaction.user.mention}.\n\n"
                "The ticket owner can continue the conversation."
            ),
            color=GREEN,
            banner_url=TICKET_BANNER,
            footer_text="Straw Hat • Ticket System"
        )

        await interaction.response.send_message(
            embed=embed
        )


# ============================================================
# CLAIM BUTTON
# ============================================================

class ClaimTicketButton(
    discord.ui.Button
):

    def __init__(self):

        super().__init__(
            label="Claim",
            emoji="👤",
            style=discord.ButtonStyle.primary,
            custom_id="strawhat_ticket_claim"
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        ticket = get_ticket_by_channel(
            interaction.channel.id
        )

        if ticket is None:

            await interaction.response.send_message(
                "❌ Ticket not found.",
                ephemeral=True
            )

            return

        config = get_ticket_config(
            interaction.guild.id
        )

        staff_role_id = config[3]

        if (
            not interaction.user.guild_permissions.manage_guild
            and interaction.user.get_role(
                staff_role_id
            ) is None
        ):

            await interaction.response.send_message(
                "🛡️ Only Crew members can claim tickets.",
                ephemeral=True
            )

            return

        claim_ticket(
            interaction.channel.id,
            interaction.user.id
        )

        await interaction.response.send_message(
            embed=create_embed(
                title="👤 Ticket Claimed",
                description=(
                    f"{interaction.user.mention} is now "
                    "handling this ticket."
                ),
                color=GREEN,
                footer_text="Straw Hat • Ticket System"
            )
        )


# ============================================================
# UNCLAIM BUTTON
# ============================================================

class UnclaimTicketButton(
    discord.ui.Button
):

    def __init__(self):

        super().__init__(
            label="Unclaim",
            emoji="↩️",
            style=discord.ButtonStyle.secondary,
            custom_id="strawhat_ticket_unclaim"
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        config = get_ticket_config(
            interaction.guild.id
        )

        staff_role_id = config[3]

        if (
            not interaction.user.guild_permissions.manage_guild
            and interaction.user.get_role(
                staff_role_id
            ) is None
        ):

            await interaction.response.send_message(
                "🛡️ Only Crew members can unclaim tickets.",
                ephemeral=True
            )

            return

        unclaim_ticket(
            interaction.channel.id
        )

        await interaction.response.send_message(
            embed=create_embed(
                title="↩️ Ticket Unclaimed",
                description=(
                    "This ticket is available for another "
                    "Crew member to handle."
                ),
                color=GREEN,
                footer_text="Straw Hat • Ticket System"
            )
        )


# ============================================================
# DELETE BUTTON
# ============================================================

class DeleteTicketButton(
    discord.ui.Button
):

    def __init__(self):

        super().__init__(
            label="Delete",
            emoji="🗑️",
            style=discord.ButtonStyle.danger,
            custom_id="strawhat_ticket_delete"
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        config = get_ticket_config(
            interaction.guild.id
        )

        staff_role_id = config[3]

        if (
            not interaction.user.guild_permissions.manage_guild
            and interaction.user.get_role(
                staff_role_id
            ) is None
        ):

            await interaction.response.send_message(
                "🛡️ Only Crew members can delete tickets.",
                ephemeral=True
            )

            return

        ticket = get_ticket_by_channel(
            interaction.channel.id
        )

        if ticket is None:

            await interaction.response.send_message(
                "❌ Ticket not found.",
                ephemeral=True
            )

            return

        delete_ticket_record(
            interaction.channel.id
        )

        await interaction.response.send_message(
            embed=create_embed(
                title="🗑️ Ticket Deleted",
                description=(
                    "This ticket channel will now be deleted."
                ),
                color=RED,
                footer_text="Straw Hat • Ticket System"
            )
        )

        await interaction.channel.delete(
            reason=(
                f"Ticket deleted by "
                f"{interaction.user}"
            )
        )


# ============================================================
# OPEN TICKET VIEW
# ============================================================

class TicketActionView(
    discord.ui.View
):

    def __init__(self):

        super().__init__(
            timeout=None
        )

        self.add_item(
            CloseTicketButton()
        )

        self.add_item(
            ClaimTicketButton()
        )

        self.add_item(
            UnclaimTicketButton()
        )


# ============================================================
# CLOSED TICKET VIEW
# ============================================================

class ClosedTicketView(
    discord.ui.View
):

    def __init__(self):

        super().__init__(
            timeout=None
        )

        self.add_item(
            ReopenTicketButton()
        )

        self.add_item(
            DeleteTicketButton()
        )


# ============================================================
# REGISTER PERSISTENT VIEWS
# ============================================================

def register_ticket_views(
    bot
):

    bot.add_view(
        TicketPanelView()
    )

    bot.add_view(
        TicketActionView()
    )

    bot.add_view(
        ClosedTicketView()
    )