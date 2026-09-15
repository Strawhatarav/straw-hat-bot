import discord

from database.database import is_self_role


def can_manage_role(
    guild: discord.Guild,
    role: discord.Role
) -> tuple[bool, str]:

    bot_member = guild.me

    if bot_member is None:
        return False, "I could not find my member information."

    # Never allow @everyone
    if role.is_default():
        return False, "I cannot manage the @everyone role."

    # Never allow integration-managed roles
    if role.managed:
        return False, "I cannot manage a managed integration role."

    # Bot must be above the role
    if role >= bot_member.top_role:
        return False, (
            "I cannot manage this role because it is "
            "higher than or equal to my highest role."
        )

    # Bot needs Manage Roles
    if not bot_member.guild_permissions.manage_roles:
        return False, (
            "I do not have the Manage Roles permission."
        )

    return True, ""


async def add_role(
    member: discord.Member,
    role: discord.Role
) -> tuple[bool, str]:

    # Make sure the role is configured for self-assignment
    if not is_self_role(
        member.guild.id,
        role.id
    ):
        return False, "This role is not self-assignable."

    can_manage, reason = can_manage_role(
        member.guild,
        role
    )

    if not can_manage:
        return False, reason

    if role in member.roles:
        return False, "You already have this role."

    try:
        await member.add_roles(role)

        return True, (
            f"Added {role.mention}."
        )

    except discord.Forbidden:
        return False, (
            "Discord denied the role assignment."
        )

    except discord.HTTPException:
        return False, (
            "Discord returned an error while assigning the role."
        )


async def remove_role(
    member: discord.Member,
    role: discord.Role
) -> tuple[bool, str]:

    if not is_self_role(
        member.guild.id,
        role.id
    ):
        return False, "This role is not self-assignable."

    can_manage, reason = can_manage_role(
        member.guild,
        role
    )

    if not can_manage:
        return False, reason

    if role not in member.roles:
        return False, "You do not have this role."

    try:
        await member.remove_roles(role)

        return True, (
            f"Removed {role.mention}."
        )

    except discord.Forbidden:
        return False, (
            "Discord denied the role removal."
        )

    except discord.HTTPException:
        return False, (
            "Discord returned an error while removing the role."
        )