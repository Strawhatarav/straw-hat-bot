# ============================================================
# STRAW HAT — TEMPORARY VOICE EVENTS
# ============================================================

import discord
from discord.ext import commands

from config.temporary_voice import (
    JOIN_TO_CREATE_CHANNEL_ID,
    TEMPORARY_CHANNEL_PREFIX,
    MODERATOR_ROLE_NAME,
    ADMIN_ROLE_NAME,
)

from services.temporary_voice_service import (
    create_voice_channel_record,
    get_voice_channel,
    add_member_to_join_order,
    set_voice_owner,
    delete_voice_channel_record,
)


class VoiceEvents(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # ========================================================
    # VOICE STATE EVENT
    # ========================================================

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
    ):

        # ----------------------------------------------------
        # Ignore bots
        # ----------------------------------------------------

        if member.bot:
            return

        # ----------------------------------------------------
        # USER JOINED A VOICE CHANNEL
        # ----------------------------------------------------

        if (
            after.channel is not None
            and (
                before.channel is None
                or before.channel.id != after.channel.id
            )
        ):

            await self.handle_voice_join(
                member,
                after.channel
            )

        # ----------------------------------------------------
        # USER LEFT A VOICE CHANNEL
        # ----------------------------------------------------

        if (
            before.channel is not None
            and (
                after.channel is None
                or before.channel.id != after.channel.id
            )
        ):

            await self.handle_voice_leave(
                member,
                before.channel
            )

    # ========================================================
    # HANDLE JOIN
    # ========================================================

    async def handle_voice_join(
        self,
        member: discord.Member,
        channel: discord.VoiceChannel
    ):

        # ----------------------------------------------------
        # JOIN-TO-CREATE
        # ----------------------------------------------------

        if channel.id == JOIN_TO_CREATE_CHANNEL_ID:

            await self.create_temporary_channel(
                member,
                channel
            )

            return

        # ----------------------------------------------------
        # EXISTING TEMPORARY CHANNEL
        # ----------------------------------------------------

        record = get_voice_channel(
            channel.id
        )

        if record is None:
            return

        add_member_to_join_order(
            channel.id,
            member.id
        )

    # ========================================================
    # HANDLE LEAVE
    # ========================================================

    async def handle_voice_leave(
        self,
        member: discord.Member,
        channel: discord.VoiceChannel
    ):

        record = get_voice_channel(
            channel.id
        )

        if record is None:
            return

        # ----------------------------------------------------
        # CHANNEL STILL HAS MEMBERS
        # ----------------------------------------------------

        if len(channel.members) > 0:

            # If owner left, transfer ownership.
            if record["owner_id"] == member.id:

                new_owner = self.find_next_owner(
                    channel,
                    record["join_order"]
                )

                if new_owner is not None:

                    set_voice_owner(
                        channel.id,
                        new_owner.id
                    )

                    await self.send_ownership_transfer(
                        new_owner,
                        channel
                    )

            return

        # ----------------------------------------------------
        # CHANNEL IS EMPTY
        # ----------------------------------------------------

        try:
            await channel.delete(
                reason="Temporary Straw Hat voice channel became empty."
            )

        except discord.NotFound:
            pass

        except discord.Forbidden:
            print(
                f"❌ Straw Hat cannot delete temporary "
                f"voice channel {channel.id}."
            )

        finally:
            delete_voice_channel_record(
                channel.id
            )

    # ========================================================
    # FIND NEXT OWNER
    # ========================================================

    def find_next_owner(
        self,
        channel: discord.VoiceChannel,
        join_order: list[int]
    ):

        active_members = {
            member.id: member
            for member in channel.members
        }

        # Original join order decides ownership.
        for user_id in join_order:

            if user_id in active_members:

                return active_members[user_id]

        return None

    # ========================================================
    # CREATE TEMPORARY CHANNEL
    # ========================================================

    async def create_temporary_channel(
        self,
        member: discord.Member,
        join_channel: discord.VoiceChannel
    ):

        guild = member.guild

        # ----------------------------------------------------
        # FIND STAFF ROLES
        # ----------------------------------------------------

        moderator_role = discord.utils.get(
            guild.roles,
            name=MODERATOR_ROLE_NAME
        )

        admin_role = discord.utils.get(
            guild.roles,
            name=ADMIN_ROLE_NAME
        )

        # ----------------------------------------------------
        # BASE PERMISSIONS
        # ----------------------------------------------------

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                connect=True,
                view_channel=True
            ),
            member: discord.PermissionOverwrite(
                connect=True,
                view_channel=True
            )
        }

        # ----------------------------------------------------
        # MODERATOR BYPASS
        # ----------------------------------------------------

        if moderator_role is not None:

            overwrites[moderator_role] = (
                discord.PermissionOverwrite(
                    connect=True,
                    view_channel=True
                )
            )

        # ----------------------------------------------------
        # ADMIN BYPASS
        # ----------------------------------------------------

        if admin_role is not None:

            overwrites[admin_role] = (
                discord.PermissionOverwrite(
                    connect=True,
                    view_channel=True
                )
            )

        # ----------------------------------------------------
        # CREATE CHANNEL
        # ----------------------------------------------------

        try:

            temporary_channel = await guild.create_voice_channel(
                name=(
                    f"{TEMPORARY_CHANNEL_PREFIX} "
                    f"{member.display_name}'s Crew"
                ),
                category=join_channel.category,
                overwrites=overwrites,
                reason="Straw Hat temporary voice channel"
            )

        except discord.Forbidden:

            print(
                f"❌ Straw Hat does not have permission "
                f"to create voice channels in {guild.name}."
            )

            return

        except discord.HTTPException as error:

            print(
                f"❌ Failed to create temporary voice channel: "
                f"{error}"
            )

            return

        # ----------------------------------------------------
        # SAVE DATABASE RECORD
        # ----------------------------------------------------

        create_voice_channel_record(
            guild.id,
            temporary_channel.id,
            member.id
        )

        # ----------------------------------------------------
        # MOVE MEMBER
        # ----------------------------------------------------

        try:

            await member.move_to(
                temporary_channel,
                reason="Straw Hat temporary voice channel"
            )

        except discord.Forbidden:

            print(
                f"❌ Straw Hat cannot move "
                f"{member} into {temporary_channel.name}."
            )

        except discord.HTTPException as error:

            print(
                f"❌ Failed to move {member}: {error}"
            )

        # ----------------------------------------------------
        # SEND EPHEMERAL CONFIRMATION
        # ----------------------------------------------------

        try:

            await self.send_creation_confirmation(
                member,
                temporary_channel
            )

        except Exception as error:

            print(
                f"❌ Failed to send temporary VC "
                f"confirmation: {error}"
            )

    # ========================================================
    # CREATION CONFIRMATION
    # ========================================================

    async def send_creation_confirmation(
        self,
        member: discord.Member,
        channel: discord.VoiceChannel
    ):

        # Discord voice-state events cannot directly send
        # an ephemeral interaction response.
        #
        # Therefore the actual ephemeral confirmation will
        # be handled by /voice controls.
        #
        # We intentionally do nothing here.

        return

    # ========================================================
    # OWNERSHIP TRANSFER MESSAGE
    # ========================================================

    async def send_ownership_transfer(
        self,
        new_owner: discord.Member,
        channel: discord.VoiceChannel
    ):

        # Discord does not provide a normal way for an event
        # listener to create an ephemeral message.
        #
        # The new owner can see ownership through /voice.
        #
        # We therefore keep this event silent.

        return


async def setup(bot):

    await bot.add_cog(
        VoiceEvents(bot)
    )