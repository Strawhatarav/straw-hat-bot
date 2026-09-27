import random
import re
import time

import discord

from database import giveaway_db


DURATION_PATTERN = re.compile(
    r"^(?P<value>[1-9]\d*)(?P<unit>[mhdw])$",
    re.IGNORECASE,
)


def parse_duration(duration: str) -> int | None:
    """
    Convert:
        10m
        2h
        3d
        1w

    into seconds.
    """

    duration = duration.strip().lower()

    match = DURATION_PATTERN.fullmatch(duration)

    if not match:
        return None

    value = int(match.group("value"))
    unit = match.group("unit")

    multipliers = {
        "m": 60,
        "h": 60 * 60,
        "d": 24 * 60 * 60,
        "w": 7 * 24 * 60 * 60,
    }

    return value * multipliers[unit]


def format_duration(seconds: int) -> str:
    if seconds % (7 * 24 * 60 * 60) == 0:
        return f"{seconds // (7 * 24 * 60 * 60)}w"

    if seconds % (24 * 60 * 60) == 0:
        return f"{seconds // (24 * 60 * 60)}d"

    if seconds % (60 * 60) == 0:
        return f"{seconds // (60 * 60)}h"

    if seconds % 60 == 0:
        return f"{seconds // 60}m"

    return f"{seconds}s"


def create_giveaway(
    guild_id: int,
    channel_id: int,
    prize: str,
    host_id: int,
    winner_count: int,
    duration_seconds: int,
):
    started_at = int(time.time())
    ends_at = started_at + duration_seconds

    return giveaway_db.create_giveaway(
        guild_id=guild_id,
        channel_id=channel_id,
        prize=prize,
        host_id=host_id,
        winner_count=winner_count,
        started_at=started_at,
        ends_at=ends_at,
    )


def select_winners(giveaway_id: int, winner_count: int):
    entries = giveaway_db.get_entries(giveaway_id)

    if not entries:
        return []

    winners = random.SystemRandom().sample(
        entries,
        min(winner_count, len(entries)),
    )

    for user_id in winners:
        giveaway_db.add_winner(giveaway_id, user_id)

    return winners


def reroll_winner(giveaway_id: int):
    entries = giveaway_db.get_entries(giveaway_id)
    existing_winners = giveaway_db.get_winners(giveaway_id)

    eligible = [
        user_id
        for user_id in entries
        if user_id not in existing_winners
    ]

    if not eligible:
        return None

    winner = random.SystemRandom().choice(eligible)

    giveaway_db.add_winner(giveaway_id, winner)

    return winner


def can_manage_giveaway(member: discord.Member) -> bool:
    """
    Straw Hat hierarchy:

    Captain
    Crew
    Marines

    can manage giveaways.
    """

    if member.guild_permissions.administrator:
        return True

    allowed_roles = {
        "Captain",
        "Crew",
        "Marines",
    }

    return any(
        role.name in allowed_roles
        for role in member.roles
    )


def can_cancel_giveaway(member: discord.Member) -> bool:
    return can_manage_giveaway(member)


def get_giveaway(giveaway_id: int):
    return giveaway_db.get_giveaway(giveaway_id)


def get_entry_count(giveaway_id: int):
    return giveaway_db.get_entry_count(giveaway_id)


def add_entry(giveaway_id: int, user_id: int):
    return giveaway_db.add_entry(
        giveaway_id,
        user_id,
    )


def end_giveaway(giveaway_id: int):
    giveaway = giveaway_db.get_active_giveaway(giveaway_id)

    if not giveaway:
        return None, []

    winners = select_winners(
        giveaway_id,
        giveaway[6],
    )

    giveaway_db.set_giveaway_status(
        giveaway_id,
        "ended",
        int(time.time()),
    )

    return giveaway, winners


def cancel_giveaway(giveaway_id: int):
    giveaway = giveaway_db.get_active_giveaway(giveaway_id)

    if not giveaway:
        return None

    giveaway_db.set_giveaway_status(
        giveaway_id,
        "cancelled",
        int(time.time()),
    )

    return giveaway