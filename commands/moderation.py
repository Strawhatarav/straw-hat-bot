import discord
from discord import app_commands
from discord.ext import commands

from database.moderation_db import (
    get_config,
    set_config_value,
    add_warning,
    get_warnings,
    clear_warnings,
)
from services.embed_service import (
    create_embed,
    create_success_embed,
    create_warning_embed,
    RED,
    YELLOW,
    GREEN,
    BLUE,
)
from services.moderation_service import (
    is_staff,
    can_moderate,
    send_log,
    send_private_error,
)


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def check_staff(self, interaction):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return False

        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(
                "Unable to verify your server roles.",
                ephemeral=True,
            )
            return False

        if not is_staff(interaction.user):
            await interaction.response.send_message(
                "❌ Only Crew and Marines can use this command.",
                ephemeral=True,
            )
            return False

        return True

    async def check_target(self, interaction, target):
        if not await self.check_staff(interaction):
            return False

        bot_member = interaction.guild.me
        allowed, reason = can_moderate(
            interaction.user,
            target,
            bot_member,
        )

        if not allowed:
            await interaction.response.send_message(
                f"❌ {reason}",
                ephemeral=True,
            )
            return False

        return True

    # ---------------------------------------------------------
    # CONFIGURATION
    # ---------------------------------------------------------

    config = app_commands.Group(
        name="modconfig",
        description="Configure moderation channels and settings.",
    )

    @config.command(
        name="set-mod-logs",
        description="Set the staff moderation log channel.",
    )
    async def set_mod_logs(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ):
        if not await self.check_staff(interaction):
            return

        set_config_value(
            interaction.guild.id,
            "mod_log_channel_id",
            channel.id,
        )

        await interaction.response.send_message(
            f"✅ Moderation logs will be sent to {channel.mention}.",
            ephemeral=True,
        )

    @config.command(
        name="set-automod-logs",
        description="Set the AutoMod log channel.",
    )
    async def set_automod_logs(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ):
        if not await self.check_staff(interaction):
            return

        set_config_value(
            interaction.guild.id,
            "automod_log_channel_id",
            channel.id,
        )

        await interaction.response.send_message(
            f"✅ AutoMod logs will be sent to {channel.mention}.",
            ephemeral=True,
        )

    @config.command(
        name="set-impel-town",
        description="Set the restricted-member channel.",
    )
    async def set_impel_town(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ):
        if not await self.check_staff(interaction):
            return

        set_config_value(
            interaction.guild.id,
            "impel_town_channel_id",
            channel.id,
        )

        await interaction.response.send_message(
            f"✅ Restricted members' channel set to {channel.mention}.",
            ephemeral=True,
        )

    @config.command(
        name="set-restricted-role",
        description="Set the role used for Impel Town restrictions.",
    )
    async def set_restricted_role(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
    ):
        if not await self.check_staff(interaction):
            return

        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message(
                "❌ My role must be higher than the restricted role.",
                ephemeral=True,
            )
            return

        set_config_value(
            interaction.guild.id,
            "restricted_role_id",
            role.id,
        )

        await interaction.response.send_message(
            f"✅ Restricted role set to {role.mention}.",
            ephemeral=True,
        )

    @config.command(
        name="view",
        description="View moderation channel configuration.",
    )
    async def view_config(
        self,
        interaction: discord.Interaction,
    ):
        if not await self.check_staff(interaction):
            return

        config = get_config(interaction.guild.id)

        def channel_text(channel_id):
            channel = interaction.guild.get_channel(channel_id) if channel_id else None
            return channel.mention if channel else "Not configured"

        role = (
            interaction.guild.get_role(config["restricted_role_id"])
            if config["restricted_role_id"]
            else None
        )

        embed = create_embed(
            title="⚙️ Moderation Configuration",
            description="Current Straw Hat moderation settings.",
            color=RED,
        )
        embed.add_field(
            name="🛡️ Mod Logs",
            value=channel_text(config["mod_log_channel_id"]),
            inline=False,
        )
        embed.add_field(
            name="🤖 AutoMod Logs",
            value=channel_text(config["automod_log_channel_id"]),
            inline=False,
        )
        embed.add_field(
            name="⛓️ Impel Town",
            value=channel_text(config["impel_town_channel_id"]),
            inline=False,
        )
        embed.add_field(
            name="🔒 Restricted Role",
            value=role.mention if role else "Not configured",
            inline=False,
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
        )

    # ---------------------------------------------------------
    # WARNINGS
    # ---------------------------------------------------------

    @app_commands.command(name="warn", description="Warn a member.")
    async def warn(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str,
    ):
        if not await self.check_target(interaction, member):
            return

        warning_id = add_warning(
            interaction.guild.id,
            member.id,
            interaction.user.id,
            reason,
        )

        await send_log(
            interaction.guild,
            "warn",
            member,
            interaction.user,
            f"Warning #{warning_id}: {reason}",
        )

        try:
            await member.send(
                f"⚠️ You received a warning in **{interaction.guild.name}**.\n"
                f"Reason: {reason}"
            )
        except (discord.Forbidden, discord.HTTPException):
            pass

        await interaction.response.send_message(
            embed=create_warning_embed(
                "⚠️ Member warned",
                f"{member.mention} has received warning **#{warning_id}**.\n"
                f"**Reason:** {reason}",
            ),
            ephemeral=True,
        )

    @app_commands.command(
        name="warnings",
        description="View a member's active warnings.",
    )
    async def warnings(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
    ):
        if not await self.check_staff(interaction):
            return

        rows = get_warnings(interaction.guild.id, member.id)

        if not rows:
            await interaction.response.send_message(
                f"✅ {member.mention} has no active warnings.",
                ephemeral=True,
            )
            return

        lines = []
        for row in rows[:10]:
            lines.append(
                f"**#{row['id']}** — {row['reason'][:250]}\n"
                f"Moderator: <@{row['moderator_id']}> • "
                f"{row['created_at'][:10]}"
            )

        embed = create_embed(
            title=f"📋 Warnings • {member}",
            description="\n\n".join(lines),
            color=YELLOW,
        )
        embed.set_footer(text=f"Showing up to 10 of {len(rows)} active warnings")

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
        )

    @app_commands.command(
        name="clearwarnings",
        description="Clear a member's active warnings.",
    )
    async def clearwarnings(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "Warnings cleared by staff",
    ):
        if not await self.check_target(interaction, member):
            return

        count = clear_warnings(interaction.guild.id, member.id)

        await send_log(
            interaction.guild,
            "clear warnings",
            member,
            interaction.user,
            f"{count} warning(s) cleared. Reason: {reason}",
        )

        await interaction.response.send_message(
            embed=create_success_embed(
                "✅ Warnings cleared",
                f"Cleared **{count}** active warning(s) for {member.mention}.",
            ),
            ephemeral=True,
        )

    # ---------------------------------------------------------
    # TIMEOUTS
    # ---------------------------------------------------------

    @app_commands.command(name="timeout", description="Timeout a member.")
    @app_commands.describe(
        minutes="Timeout duration, from 1 to 40320 minutes.",
        reason="Reason for the timeout.",
    )
    async def timeout(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        minutes: app_commands.Range[int, 1, 40320],
        reason: str,
    ):
        if not await self.check_target(interaction, member):
            return

        try:
            await member.timeout(
                discord.utils.utcnow() + discord.timedelta(minutes=minutes),
                reason=reason,
            )
        except discord.Forbidden:
            await send_private_error(
                interaction,
                "I lack permission to timeout this member.",
            )
            return
        except discord.HTTPException as error:
            await send_private_error(interaction, f"Discord error: {error}")
            return

        await send_log(
            interaction.guild,
            "timeout",
            member,
            interaction.user,
            f"{minutes} minutes. {reason}",
        )

        await interaction.response.send_message(
            embed=create_success_embed(
                "⏳ Member timed out",
                f"{member.mention} was timed out for **{minutes} minutes**.\n"
                f"**Reason:** {reason}",
            ),
            ephemeral=True,
        )

    @app_commands.command(
        name="untimeout",
        description="Remove a member's timeout.",
    )
    async def untimeout(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "Timeout removed by staff",
    ):
        if not await self.check_target(interaction, member):
            return

        try:
            await member.timeout(None, reason=reason)
        except discord.Forbidden:
            await send_private_error(interaction, "I cannot remove this timeout.")
            return
        except discord.HTTPException as error:
            await send_private_error(interaction, f"Discord error: {error}")
            return

        await send_log(
            interaction.guild,
            "untimeout",
            member,
            interaction.user,
            reason,
        )

        await interaction.response.send_message(
            embed=create_success_embed(
                "✅ Timeout removed",
                f"Removed the timeout for {member.mention}.",
            ),
            ephemeral=True,
        )

    # ---------------------------------------------------------
    # KICK AND BAN
    # ---------------------------------------------------------

    @app_commands.command(name="kick", description="Kick a member.")
    async def kick(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str,
    ):
        if not await self.check_target(interaction, member):
            return

        try:
            await member.kick(reason=reason)
        except discord.Forbidden:
            await send_private_error(interaction, "I cannot kick this member.")
            return
        except discord.HTTPException as error:
            await send_private_error(interaction, f"Discord error: {error}")
            return

        await send_log(
            interaction.guild,
            "kick",
            member,
            interaction.user,
            reason,
        )

        await interaction.response.send_message(
            embed=create_success_embed(
                "👢 Member kicked",
                f"**{member}** was kicked.\n**Reason:** {reason}",
            ),
            ephemeral=True,
        )

    @app_commands.command(name="ban", description="Ban a member.")
    async def ban(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str,
    ):
        if not await self.check_target(interaction, member):
            return

        try:
            await member.send(
                f"⛔ You were banned from **{interaction.guild.name}**.\n"
                f"Reason: {reason}"
            )
        except (discord.Forbidden, discord.HTTPException):
            pass

        try:
            await interaction.guild.ban(
                member,
                reason=reason,
                delete_message_seconds=0,
            )
        except discord.Forbidden:
            await send_private_error(interaction, "I cannot ban this member.")
            return
        except discord.HTTPException as error:
            await send_private_error(interaction, f"Discord error: {error}")
            return

        await send_log(
            interaction.guild,
            "ban",
            member,
            interaction.user,
            reason,
        )

        await interaction.response.send_message(
            embed=create_success_embed(
                "⛔ Member banned",
                f"**{member}** was banned.\n**Reason:** {reason}",
            ),
            ephemeral=True,
        )

    @app_commands.command(name="unban", description="Unban a user by ID.")
    async def unban(
        self,
        interaction: discord.Interaction,
        user_id: str,
        reason: str = "Unbanned by staff",
    ):
        if not await self.check_staff(interaction):
            return

        try:
            user = await self.bot.fetch_user(int(user_id))
            await interaction.guild.unban(user, reason=reason)
        except ValueError:
            await interaction.response.send_message(
                "❌ Enter a valid numeric user ID.",
                ephemeral=True,
            )
            return
        except discord.NotFound:
            await interaction.response.send_message(
                "❌ That user is not banned.",
                ephemeral=True,
            )
            return
        except discord.Forbidden:
            await send_private_error(interaction, "I cannot unban users.")
            return
        except discord.HTTPException as error:
            await send_private_error(interaction, f"Discord error: {error}")
            return

        await send_log(
            interaction.guild,
            "unban",
            user,
            interaction.user,
            reason,
        )

        await interaction.response.send_message(
            embed=create_success_embed(
                "✅ User unbanned",
                f"{user} (`{user.id}`) has been unbanned.",
            ),
            ephemeral=True,
        )

    # ---------------------------------------------------------
    # CHANNEL MODERATION
    # ---------------------------------------------------------

    @app_commands.command(name="purge", description="Delete recent messages.")
    @app_commands.describe(amount="Number of messages to delete (1–100).")
    async def purge(
        self,
        interaction: discord.Interaction,
        amount: app_commands.Range[int, 1, 100],
    ):
        if not await self.check_staff(interaction):
            return

        if not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message(
                "Use this command in a text channel.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        try:
            deleted = await interaction.channel.purge(
                limit=amount,
                reason=f"Purge by {interaction.user}",
            )
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ I need Manage Messages permission.",
                ephemeral=True,
            )
            return
        except discord.HTTPException as error:
            await interaction.followup.send(
                f"❌ Discord error: {error}",
                ephemeral=True,
            )
            return

        await send_log(
            interaction.guild,
            "purge",
            None,
            interaction.user,
            f"Deleted {len(deleted)} messages in {interaction.channel.mention}.",
        )

        await interaction.followup.send(
            f"🧹 Deleted **{len(deleted)}** messages.",
            ephemeral=True,
        )

    @app_commands.command(
        name="slowmode",
        description="Set a channel's slowmode.",
    )
    async def slowmode(
        self,
        interaction: discord.Interaction,
        seconds: app_commands.Range[int, 0, 21600],
    ):
        if not await self.check_staff(interaction):
            return

        if not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message(
                "Use this command in a text channel.",
                ephemeral=True,
            )
            return

        try:
            await interaction.channel.edit(
                slowmode_delay=seconds,
                reason=f"Slowmode changed by {interaction.user}",
            )
        except discord.Forbidden:
            await send_private_error(interaction, "I need Manage Channels permission.")
            return
        except discord.HTTPException as error:
            await send_private_error(interaction, f"Discord error: {error}")
            return

        await send_log(
            interaction.guild,
            "slowmode",
            None,
            interaction.user,
            f"Slowmode set to {seconds} seconds in {interaction.channel.mention}.",
        )

        await interaction.response.send_message(
            embed=create_success_embed(
                "🐢 Slowmode updated",
                f"Slowmode in {interaction.channel.mention} is now **{seconds} seconds**.",
            ),
            ephemeral=True,
        )

    async def set_channel_locked(
        self,
        interaction: discord.Interaction,
        locked: bool,
    ):
        if not await self.check_staff(interaction):
            return

        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "Use this command in a text channel.",
                ephemeral=True,
            )
            return

        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = not locked

        try:
            await channel.set_permissions(
                interaction.guild.default_role,
                overwrite=overwrite,
                reason=f"Channel {'locked' if locked else 'unlocked'} by {interaction.user}",
            )
        except discord.Forbidden:
            await send_private_error(interaction, "I need Manage Channels permission.")
            return
        except discord.HTTPException as error:
            await send_private_error(interaction, f"Discord error: {error}")
            return

        action = "lock" if locked else "unlock"
        await send_log(
            interaction.guild,
            action,
            None,
            interaction.user,
            f"{channel.mention} was {'locked' if locked else 'unlocked'}.",
        )

        await interaction.response.send_message(
            embed=create_success_embed(
                "🔒 Channel locked" if locked else "🔓 Channel unlocked",
                f"{channel.mention} has been {'locked' if locked else 'unlocked'}.",
            ),
            ephemeral=True,
        )

    @app_commands.command(name="lock", description="Lock this text channel.")
    async def lock(self, interaction: discord.Interaction):
        await self.set_channel_locked(interaction, True)

    @app_commands.command(name="unlock", description="Unlock this text channel.")
    async def unlock(self, interaction: discord.Interaction):
        await self.set_channel_locked(interaction, False)

    @config.command(
        name="automod",
        description="Enable or disable AutoMod.",
    )
    async def automod(
        self,
        interaction: discord.Interaction,
        enabled: bool,
    ):
        if not await self.check_staff(interaction):
            return

        set_config_value(
            interaction.guild.id,
            "automod_enabled",
            int(enabled),
        )

        status = "enabled" if enabled else "disabled"

        await interaction.response.send_message(
            f"🤖 AutoMod is now **{status}**.",
            ephemeral=True,
        )

    @config.command(
        name="filter",
        description="Enable or disable an AutoMod filter.",
    )
    @app_commands.choices(
        filter_type=[
            app_commands.Choice(name="Spam", value="spam_enabled"),
            app_commands.Choice(name="Links", value="links_enabled"),
            app_commands.Choice(name="Blocked words", value="bad_words_enabled"),
            app_commands.Choice(name="Raid alerts", value="raid_enabled"),
        ]
    )
    async def filter(
        self,
        interaction: discord.Interaction,
        filter_type: app_commands.Choice[str],
        enabled: bool,
    ):
        if not await self.check_staff(interaction):
            return

        set_config_value(
            interaction.guild.id,
            filter_type.value,
            int(enabled),
        )

        status = "enabled" if enabled else "disabled"

        await interaction.response.send_message(
            f"🤖 **{filter_type.name}** filter is now **{status}**.",
            ephemeral=True,
        )

    @app_commands.command(
        name="restrict",
        description="Restrict a member to Impel Town.",
    )
    async def restrict(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str,
    ):
        if not await self.check_target(interaction, member):
            return

        config = get_config(interaction.guild.id)

        role_id = config["restricted_role_id"]
        channel_id = config["impel_town_channel_id"]

        role = interaction.guild.get_role(role_id) if role_id else None
        channel = interaction.guild.get_channel(channel_id) if channel_id else None

        if role is None or channel is None:
            await interaction.response.send_message(
                "❌ Configure the restricted role and Impel Town first "
                "using `/modconfig`.",
                ephemeral=True,
            )
            return

        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message(
                "❌ My role must be higher than the restricted role.",
                ephemeral=True,
            )
            return

        try:
            await member.add_roles(role, reason=reason)
        except discord.Forbidden:
            await send_private_error(
                interaction,
                "I cannot assign the restricted role.",
            )
            return
        except discord.HTTPException as error:
            await send_private_error(interaction, f"Discord error: {error}")
            return

        await send_log(
            interaction.guild,
            "restrict",
            member,
            interaction.user,
            reason,
        )

        try:
            await channel.send(
                f"⛓️ {member.mention}, you have been restricted to Impel Town.\n"
                f"**Reason:** {reason}",
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except (discord.Forbidden, discord.HTTPException):
            pass

        await interaction.response.send_message(
            embed=create_success_embed(
                "⛓️ Member restricted",
                f"{member.mention} has been given the restricted role.",
            ),
            ephemeral=True,
        )

    @app_commands.command(
        name="unrestrict",
        description="Remove a member's Impel Town restriction.",
    )
    async def unrestrict(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "Restriction removed by staff",
    ):
        if not await self.check_target(interaction, member):
            return

        config = get_config(interaction.guild.id)
        role_id = config["restricted_role_id"]
        role = interaction.guild.get_role(role_id) if role_id else None

        if role is None:
            await interaction.response.send_message(
                "❌ Configure the restricted role first.",
                ephemeral=True,
            )
            return

        if role not in member.roles:
            await interaction.response.send_message(
                "ℹ️ This member does not have the restricted role.",
                ephemeral=True,
            )
            return

        try:
            await member.remove_roles(role, reason=reason)
        except discord.Forbidden:
            await send_private_error(
                interaction,
                "I cannot remove the restricted role.",
            )
            return
        except discord.HTTPException as error:
            await send_private_error(interaction, f"Discord error: {error}")
            return

        await send_log(
            interaction.guild,
            "unrestrict",
            member,
            interaction.user,
            reason,
        )

        await interaction.response.send_message(
            embed=create_success_embed(
                "✅ Restriction removed",
                f"{member.mention} can access the server according to their roles.",
            ),
            ephemeral=True,
        )

    @app_commands.command(
        name="restrict",
        description="Restrict a member to Impel Town.",
    )
    async def restrict(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str,
    ):
        if not await self.check_target(interaction, member):
            return

        config = get_config(interaction.guild.id)

        role_id = config["restricted_role_id"]
        channel_id = config["impel_town_channel_id"]

        role = interaction.guild.get_role(role_id) if role_id else None
        channel = interaction.guild.get_channel(channel_id) if channel_id else None

        if role is None or channel is None:
            await interaction.response.send_message(
                "❌ Configure the restricted role and Impel Town first "
                "using `/modconfig`.",
                ephemeral=True,
            )
            return

        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message(
                "❌ My role must be higher than the restricted role.",
                ephemeral=True,
            )
            return

        try:
            await member.add_roles(role, reason=reason)
        except discord.Forbidden:
            await send_private_error(
                interaction,
                "I cannot assign the restricted role.",
            )
            return
        except discord.HTTPException as error:
            await send_private_error(interaction, f"Discord error: {error}")
            return

        await send_log(
            interaction.guild,
            "restrict",
            member,
            interaction.user,
            reason,
        )

        try:
            await channel.send(
                f"⛓️ {member.mention}, you have been restricted to Impel Town.\n"
                f"**Reason:** {reason}",
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except (discord.Forbidden, discord.HTTPException):
            pass

        await interaction.response.send_message(
            embed=create_success_embed(
                "⛓️ Member restricted",
                f"{member.mention} has been given the restricted role.",
            ),
            ephemeral=True,
        )

    @app_commands.command(
        name="unrestrict",
        description="Remove a member's Impel Town restriction.",
    )
    async def unrestrict(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "Restriction removed by staff",
    ):
        if not await self.check_target(interaction, member):
            return

        config = get_config(interaction.guild.id)
        role_id = config["restricted_role_id"]
        role = interaction.guild.get_role(role_id) if role_id else None

        if role is None:
            await interaction.response.send_message(
                "❌ Configure the restricted role first.",
                ephemeral=True,
            )
            return

        if role not in member.roles:
            await interaction.response.send_message(
                "ℹ️ This member does not have the restricted role.",
                ephemeral=True,
            )
            return

        try:
            await member.remove_roles(role, reason=reason)
        except discord.Forbidden:
            await send_private_error(
                interaction,
                "I cannot remove the restricted role.",
            )
            return
        except discord.HTTPException as error:
            await send_private_error(interaction, f"Discord error: {error}")
            return

        await send_log(
            interaction.guild,
            "unrestrict",
            member,
            interaction.user,
            reason,
        )

        await interaction.response.send_message(
            embed=create_success_embed(
                "✅ Restriction removed",
                f"{member.mention} can access the server according to their roles.",
            ),
            ephemeral=True,
        )



async def setup(bot):
    await bot.add_cog(Moderation(bot))

