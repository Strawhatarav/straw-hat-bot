import discord

from database.moderation_db import (
    get_config,
    log_action,
)
from services.embed_service import (
    create_embed,
    RED,
    YELLOW,
)


def is_staff(member: discord.Member) -> bool:
    """Captain, Crew, and Marines can use moderation commands."""
    if member.guild.owner_id == member.id:
        return True

    return any(
        role.name.lower() in {"crew", "marines"}
        for role in member.roles
    )


def can_moderate(
    moderator: discord.Member,
    target: discord.Member,
    bot_member: discord.Member,
):
    """Check staff authorization and Discord role hierarchy."""
    if not is_staff(moderator):
        return False, "Only Crew and Marines can use this command."

    if target.id == moderator.id:
        return False, "You cannot moderate yourself."

    if target.id == moderator.guild.owner_id:
        return False, "The server owner cannot be moderated."

    if target.top_role >= moderator.top_role:
        return False, "You cannot moderate a member with an equal or higher role."

    if target.top_role >= bot_member.top_role:
        return False, "My role must be higher than the target's highest role."

    return True, None


async def send_log(
    guild: discord.Guild,
    action: str,
    target: discord.abc.User | None,
    moderator: discord.abc.User | None,
    reason: str,
    automod=False,
):
    config = get_config(guild.id)

    channel_id = (
        config["automod_log_channel_id"]
        if automod
        else config["mod_log_channel_id"]
    )

    if not channel_id:
        return

    channel = guild.get_channel(channel_id)
    if channel is None:
        return

    color = YELLOW if action.lower() in {
        "warn", "automod", "spam", "blocked link", "blocked word"
    } else RED

    embed = create_embed(
        title=f"⚖️ Moderation • {action.title()}",
        description=f"> {reason[:1000]}",
        color=color,
    )

    if target is not None:
        embed.add_field(
            name="👤 Target",
            value=f"{target.mention} (`{target.id}`)",
            inline=False,
        )

    if moderator is not None:
        embed.add_field(
            name="🛡️ Moderator",
            value=f"{moderator.mention} (`{moderator.id}`)",
            inline=False,
        )

    try:
        await channel.send(embed=embed)
    except (discord.Forbidden, discord.HTTPException):
        pass

    log_action(
        guild.id,
        target.id if target else None,
        moderator.id if moderator else None,
        action,
        reason,
    )


async def send_private_error(
    interaction: discord.Interaction,
    message: str,
):
    embed = create_embed(
        title="❌ Moderation action unavailable",
        description=message,
        color=RED,
    )
    await interaction.response.send_message(
        embed=embed,
        ephemeral=True,
    )

