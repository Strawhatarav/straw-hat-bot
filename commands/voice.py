# ============================================================
# STRAW HAT — VOICE COMMANDS
# ============================================================

import discord

from discord import app_commands
from discord.ext import commands

from services.embed_service import (
    create_embed,
    RED,
    GREEN,
    YELLOW,
)

from config.banners import HELP_BANNER

from config.temporary_voice import (
    MODERATOR_ROLE_NAME,
    ADMIN_ROLE_NAME,
)

# Backward-compatible alias for the role used by the temporary
# voice lock/unlock permission helpers.
CREWMATE_ROLE_NAME = ADMIN_ROLE_NAME

from services.temporary_voice_service import (
    get_voice_channel,
    set_voice_locked,
    set_voice_limit,
    delete_voice_channel_record,
)


# ============================================================
# PERMISSION HELPERS
# ============================================================

def has_staff_voice_access(
    member: discord.Member
) -> bool:

    role_names = {
        role.name
        for role in member.roles
    }

    return (
        MODERATOR_ROLE_NAME in role_names
        or ADMIN_ROLE_NAME in role_names
    )


# ============================================================
# GET CURRENT TEMPORARY VC
# ============================================================

def get_current_voice_record(
    member: discord.Member
):

    if member.voice is None:
        return None

    if member.voice.channel is None:
        return None

    return get_voice_channel(
        member.voice.channel.id
    )


# ============================================================
# VOICE CONTROL VIEW
# ============================================================

class VoiceControlView(
    discord.ui.View
):

    def __init__(
        self,
        owner_id: int
    ):

        super().__init__(
            timeout=300
        )

        self.owner_id = owner_id

    @discord.ui.button(
        label="Limit",
        emoji="👥",
        style=discord.ButtonStyle.secondary
    )
    async def limit_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.user.id != self.owner_id:

            await interaction.response.send_message(
                "❌ Only the Crew owner can change the limit.",
                ephemeral=True
            )

            return

        await interaction.response.send_modal(
            VoiceLimitModal()
        )

    # --------------------------------------------------------
    # RENAME
    # --------------------------------------------------------

    @discord.ui.button(
        label="Rename",
        emoji="✏️",
        style=discord.ButtonStyle.danger
    )
    async def rename_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.user.id != self.owner_id:

            await interaction.response.send_message(
                "❌ Only the Crew owner can rename this channel.",
                ephemeral=True
            )

            return

        await interaction.response.send_modal(
            RenameVoiceModal()
        )

    # --------------------------------------------------------
    # LOCK
    # --------------------------------------------------------

    @discord.ui.button(
        label="Lock",
        emoji="🔒",
        style=discord.ButtonStyle.danger
    )
    async def lock_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await lock_voice_channel(
            interaction
        )

    # --------------------------------------------------------
    # UNLOCK
    # --------------------------------------------------------

    @discord.ui.button(
        label="Unlock",
        emoji="🔓",
        style=discord.ButtonStyle.success
    )
    async def unlock_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await unlock_voice_channel(
            interaction
        )

    # --------------------------------------------------------
    # MEMBERS
    # --------------------------------------------------------

    @discord.ui.button(
        label="Members",
        emoji="👥",
        style=discord.ButtonStyle.secondary
    )
    async def members_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await show_members(
            interaction
        )

    # --------------------------------------------------------
    # DELETE
    # --------------------------------------------------------

    @discord.ui.button(
        label="Delete",
        emoji="🗑️",
        style=discord.ButtonStyle.danger
    )
    async def delete_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await delete_voice(
            interaction
        )


# ============================================================
# RENAME MODAL
# ============================================================

class RenameVoiceModal(
    discord.ui.Modal,
    title="Rename Your Crew"
):

    name = discord.ui.TextInput(
        label="New Channel Name",
        placeholder="Enter your new Crew name...",
        max_length=90,
        required=True
    )

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        record = get_current_voice_record(
            interaction.user
        )

        if record is None:

            await interaction.response.send_message(
                "❌ You are not inside a temporary Crew channel.",
                ephemeral=True
            )

            return

        if record["owner_id"] != interaction.user.id:

            await interaction.response.send_message(
                "❌ Only the Crew owner can rename this channel.",
                ephemeral=True
            )

            return

        channel = interaction.guild.get_channel(
            record["channel_id"]
        )

        if channel is None:

            await interaction.response.send_message(
                "❌ This temporary channel no longer exists.",
                ephemeral=True
            )

            return

        new_name = self.name.value.strip()

        if not new_name:

            await interaction.response.send_message(
                "❌ Channel name cannot be empty.",
                ephemeral=True
            )

            return

        try:

            await channel.edit(
                name=f"🏴‍☠️ {new_name}",
                reason="Temporary VC owner renamed channel"
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ Straw Hat cannot rename this channel.",
                ephemeral=True
            )

            return

        embed = create_embed(
            title="✏️ Crew Renamed",
            description=(
                "Your temporary voice channel has "
                "been renamed successfully."
            ),
            color=GREEN,
            banner_url=HELP_BANNER,
            footer_text="Straw Hat • Temporary Crew"
        )

        embed.add_field(
            name="🔊 New Name",
            value=channel.mention,
            inline=False
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


# ============================================================
# LOCK
# ============================================================

async def lock_voice_channel(
    interaction: discord.Interaction
):

    record = get_current_voice_record(
        interaction.user
    )

    if record is None:

        await interaction.response.send_message(
            "❌ You are not inside a temporary Crew channel.",
            ephemeral=True
        )

        return

    if record["owner_id"] != interaction.user.id:

        await interaction.response.send_message(
            "❌ Only the Crew owner can lock this channel.",
            ephemeral=True
        )

        return

    channel = interaction.guild.get_channel(
        record["channel_id"]
    )

    if channel is None:
        return

    await apply_lock_permissions(
        channel,
        interaction.guild
    )

    set_voice_locked(
        channel.id,
        True
    )

    embed = create_embed(
        title="🔒 Crew Locked",
        description=(
            "Your temporary Crew is now locked.\n\n"
            "Regular members cannot join until "
            "you unlock it."
        ),
        color=YELLOW,
        banner_url=HELP_BANNER,
        footer_text="Straw Hat • Temporary Crew"
    )

    embed.add_field(
        name="🛡️ Staff Access",
        value="Moderators and Crewmates can still join.",
        inline=False
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


# ============================================================
# UNLOCK
# ============================================================

async def unlock_voice_channel(
    interaction: discord.Interaction
):

    record = get_current_voice_record(
        interaction.user
    )

    if record is None:

        await interaction.response.send_message(
            "❌ You are not inside a temporary Crew channel.",
            ephemeral=True
        )

        return

    if record["owner_id"] != interaction.user.id:

        await interaction.response.send_message(
            "❌ Only the Crew owner can unlock this channel.",
            ephemeral=True
        )

        return

    channel = interaction.guild.get_channel(
        record["channel_id"]
    )

    if channel is None:
        return

    await apply_unlock_permissions(
        channel,
        interaction.guild
    )

    set_voice_locked(
        channel.id,
        False
    )

    embed = create_embed(
        title="🔓 Crew Unlocked",
        description=(
            "Your temporary Crew is now open "
            "to regular members."
        ),
        color=GREEN,
        banner_url=HELP_BANNER,
        footer_text="Straw Hat • Temporary Crew"
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


# ============================================================
# APPLY LOCK PERMISSIONS
# ============================================================

async def apply_lock_permissions(
    channel: discord.VoiceChannel,
    guild: discord.Guild
):

    await channel.set_permissions(
        guild.default_role,
        connect=False
    )

    moderator_role = discord.utils.get(
        guild.roles,
        name=MODERATOR_ROLE_NAME
    )

    crewmate_role = discord.utils.get(
        guild.roles,
        name=CREWMATE_ROLE_NAME
    )

    if moderator_role:

        await channel.set_permissions(
            moderator_role,
            connect=True
        )

    if crewmate_role:

        await channel.set_permissions(
            crewmate_role,
            connect=True
        )


# ============================================================
# APPLY UNLOCK PERMISSIONS
# ============================================================

async def apply_unlock_permissions(
    channel: discord.VoiceChannel,
    guild: discord.Guild
):

    await channel.set_permissions(
        guild.default_role,
        connect=True
    )

    moderator_role = discord.utils.get(
        guild.roles,
        name=MODERATOR_ROLE_NAME
    )

    crewmate_role = discord.utils.get(
        guild.roles,
        name=CREWMATE_ROLE_NAME
    )

    if moderator_role:

        await channel.set_permissions(
            moderator_role,
            connect=True
        )

    if crewmate_role:

        await channel.set_permissions(
            crewmate_role,
            connect=True
        )


# ============================================================
# SHOW MEMBERS
# ============================================================

async def show_members(
    interaction: discord.Interaction
):

    record = get_current_voice_record(
        interaction.user
    )

    if record is None:

        await interaction.response.send_message(
            "❌ You are not inside a temporary Crew channel.",
            ephemeral=True
        )

        return

    channel = interaction.guild.get_channel(
        record["channel_id"]
    )

    if channel is None:

        await interaction.response.send_message(
            "❌ This temporary channel no longer exists.",
            ephemeral=True
        )

        return

    members = channel.members

    if members:

        member_lines = []

        for member in members:

            if member.id == record["owner_id"]:

                member_lines.append(
                    f"👑 {member.mention}"
                )

            else:

                member_lines.append(
                    f"👤 {member.mention}"
                )

        member_text = "\n".join(
            member_lines
        )

    else:

        member_text = "No members."

    embed = create_embed(
        title="👥 Crew Members",
        description=(
            f"Current members inside "
            f"**{channel.name}**."
        ),
        color=RED,
        banner_url=HELP_BANNER,
        footer_text="Straw Hat • Temporary Crew"
    )

    embed.add_field(
        name="👥 Members",
        value=member_text,
        inline=False
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


# ============================================================
# DELETE
# ============================================================

async def delete_voice(
    interaction: discord.Interaction
):

    record = get_current_voice_record(
        interaction.user
    )

    if record is None:

        await interaction.response.send_message(
            "❌ You are not inside a temporary Crew channel.",
            ephemeral=True
        )

        return

    if record["owner_id"] != interaction.user.id:

        await interaction.response.send_message(
            "❌ Only the Crew owner can delete this channel.",
            ephemeral=True
        )

        return

    channel = interaction.guild.get_channel(
        record["channel_id"]
    )

    if channel is None:

        delete_voice_channel_record(
            record["channel_id"]
        )

        await interaction.response.send_message(
            "❌ The channel was already deleted.",
            ephemeral=True
        )

        return

    await interaction.response.send_message(
        embed=create_embed(
            title="🗑️ Delete Crew?",
            description=(
                "Are you sure you want to permanently "
                "delete your temporary Crew channel?"
            ),
            color=YELLOW,
            banner_url=HELP_BANNER,
            footer_text="Straw Hat • Confirmation"
        ),
        view=DeleteConfirmationView(
            channel.id
        ),
        ephemeral=True
    )


# ============================================================
# DELETE CONFIRMATION
# ============================================================

class DeleteConfirmationView(
    discord.ui.View
):

    def __init__(
        self,
        channel_id: int
    ):

        super().__init__(
            timeout=60
        )

        self.channel_id = channel_id

    @discord.ui.button(
        label="Delete",
        emoji="🗑️",
        style=discord.ButtonStyle.danger
    )
    async def confirm(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        record = get_voice_channel(
            self.channel_id
        )

        if record is None:

            await interaction.response.edit_message(
                content="❌ This Crew no longer exists.",
                embed=None,
                view=None
            )

            return

        if record["owner_id"] != interaction.user.id:

            await interaction.response.send_message(
                "❌ Only the Crew owner can delete this channel.",
                ephemeral=True
            )

            return

        channel = interaction.guild.get_channel(
            self.channel_id
        )

        if channel:

            await channel.delete(
                reason="Temporary Crew owner deleted channel."
            )

        delete_voice_channel_record(
            self.channel_id
        )

        embed = create_embed(
            title="🗑️ Crew Deleted",
            description=(
                "Your temporary Crew channel "
                "has been deleted successfully."
            ),
            color=GREEN,
            banner_url=HELP_BANNER,
            footer_text="Straw Hat • Temporary Crew"
        )

        await interaction.response.edit_message(
            embed=embed,
            view=None
        )

    @discord.ui.button(
        label="Cancel",
        emoji="❌",
        style=discord.ButtonStyle.secondary
    )
    async def cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.edit_message(
            content="🏴‍☠️ Crew deletion cancelled.",
            embed=None,
            view=None
        )

# ============================================================
# USER LIMIT MODAL
# ============================================================

class VoiceLimitModal(
    discord.ui.Modal,
    title="Set Crew Member Limit"
):

    limit = discord.ui.TextInput(
        label="Maximum Members",
        placeholder="Enter 0 for unlimited...",
        max_length=2,
        required=True
    )

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        record = get_current_voice_record(
            interaction.user
        )

        if record is None:

            await interaction.response.send_message(
                "❌ You are not inside a temporary Crew.",
                ephemeral=True
            )

            return

        if record["owner_id"] != interaction.user.id:

            await interaction.response.send_message(
                "❌ Only the Crew owner can change the limit.",
                ephemeral=True
            )

            return

        try:

            limit = int(
                self.limit.value
            )

        except ValueError:

            await interaction.response.send_message(
                "❌ Please enter a valid number.",
                ephemeral=True
            )

            return

        if limit < 0 or limit > 99:

            await interaction.response.send_message(
                "❌ The limit must be between 0 and 99.",
                ephemeral=True
            )

            return

        channel = interaction.guild.get_channel(
            record["channel_id"]
        )

        if channel is None:

            await interaction.response.send_message(
                "❌ Your temporary Crew no longer exists.",
                ephemeral=True
            )

            return

        await channel.edit(
            user_limit=limit
        )

        set_voice_limit(
            channel.id,
            limit
        )

        embed = create_embed(
            title="👥 Crew Limit Updated",
            description=(
                "Your temporary Crew member limit "
                "has been updated."
            ),
            color=GREEN,
            banner_url=HELP_BANNER,
            footer_text="Straw Hat • Temporary Crew"
        )

        embed.add_field(
            name="👥 Maximum Members",
            value=(
                str(limit)
                if limit > 0
                else "Unlimited"
            ),
            inline=False
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

# ============================================================
# VOICE COMMAND
# ============================================================

class Voice(commands.Cog):

    def __init__(
        self,
        bot
    ):
        self.bot = bot

    @app_commands.command(
        name="voice",
        description="Open your temporary Crew voice controls."
    )
    async def voice(
        self,
        interaction: discord.Interaction
    ):

        if interaction.guild is None:

            await interaction.response.send_message(
                "❌ This command can only be used inside a server.",
                ephemeral=True
            )

            return

        member = interaction.guild.get_member(
            interaction.user.id
        )

        if member is None:

            await interaction.response.send_message(
                "❌ Member information could not be found.",
                ephemeral=True
            )

            return

        record = get_current_voice_record(
            member
        )

        if record is None:

            embed = create_embed(
                title="🔊 No Active Crew",
                description=(
                    "You are not currently inside a "
                    "temporary Crew voice channel.\n\n"
                    "🏴‍☠️ Join **🔊 Join to Create** "
                    "to create your own Crew."
                ),
                color=RED,
                banner_url=HELP_BANNER,
                footer_text="Straw Hat • Temporary Crew"
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

            return

        channel = interaction.guild.get_channel(
            record["channel_id"]
        )

        if channel is None:

            await interaction.response.send_message(
                "❌ Your temporary Crew channel no longer exists.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # OWNER CONTROLS
        # ----------------------------------------------------

        is_owner = (
            record["owner_id"]
            == interaction.user.id
        )

        # ----------------------------------------------------
        # STAFF CAN VIEW CONTROLS
        # BUT ONLY OWNER CAN MANAGE
        # ----------------------------------------------------

        if not is_owner and not has_staff_voice_access(
            member
        ):

            embed = create_embed(
                title="❌ Not Your Crew",
                description=(
                    f"You are currently in "
                    f"**{channel.name}**.\n\n"
                    "Only the Crew owner can manage "
                    "this temporary voice channel."
                ),
                color=RED,
                banner_url=HELP_BANNER,
                footer_text="Straw Hat • Temporary Crew"
            )

            embed.add_field(
                name="👑 Owner",
                value=f"<@{record['owner_id']}>",
                inline=False
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

            return

        embed = create_embed(
            title="🏴‍☠️ Crew Control",
            description=(
                "Manage your temporary voice channel "
                "using the controls below."
            ),
            color=RED,
            banner_url=HELP_BANNER,
            footer_text="Straw Hat • Temporary Crew"
        )

        embed.add_field(
            name="🔊 Channel",
            value=channel.mention,
            inline=True
        )

        embed.add_field(
            name="👑 Owner",
            value=f"<@{record['owner_id']}>",
            inline=True
        )

        embed.add_field(
            name="👥 Members",
            value=str(len(channel.members)),
            inline=True
        )

        embed.add_field(
            name="🔐 Status",
            value=(
                "🔒 Locked"
                if record["locked"]
                else "🔓 Unlocked"
            ),
            inline=True
        )

        embed.add_field(
            name="👥 Limit",
            value=(
                str(record["user_limit"])
                if record["user_limit"] > 0
                else "Unlimited"
            ),
            inline=True
        )

        await interaction.response.send_message(
            embed=embed,
            view=VoiceControlView(
                record["owner_id"]
            ),
            ephemeral=True
        )


async def setup(
    bot
):

    await bot.add_cog(
        Voice(bot)
    )