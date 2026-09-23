# ============================================================
# STRAW HAT XP SERVICE
# ============================================================

import sqlite3
import time

from database.database import DATABASE_PATH
from config.xp_config import (
    bounty_required_for_level,
    DEFAULT_MIN_BOUNTY,
    DEFAULT_MAX_BOUNTY,
    DEFAULT_COOLDOWN,
)

# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    """
    Create and return a new SQLite database connection.
    """

    return sqlite3.connect(DATABASE_PATH)

# ============================================================
# LEVEL CALCULATION
# ============================================================
def calculate_level(bounty: int) -> int:

    level = 0

    while bounty >= bounty_required_for_level(level + 1):
        level += 1

    return level
# ============================================================
# XP PROGRESS
# ============================================================

def calculate_progress(bounty: int, level: int):
    """
    Calculate progress toward the next level.

    Returns:
        progress_bounty,
        required_bounty,
        percentage
    """

    current_level_bounty = bounty_required_for_level(level)

    next_level_bounty = bounty_required_for_level(level + 1)

    progress_bounty = bounty - current_level_bounty

    required_bounty = (
        next_level_bounty - current_level_bounty
    )

    if required_bounty <= 0:
        percentage = 100

    else:
        percentage = int(
            (progress_bounty / required_bounty) * 100
        )

    percentage = max(
        0,
        min(100, percentage)
    )

    return (
        progress_bounty,
        required_bounty,
        percentage
    )

# ============================================================
# CREATE USER
# ============================================================

def create_user_if_not_exists(
    guild_id: int,
    user_id: int
):
    """
    Create an XP record for a Discord user
    if one does not already exist.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO user_xp
        (
            guild_id,
            user_id,
            xp,
            level
        )
        VALUES (?, ?, 0, 0)
        """,
        (
            guild_id,
            user_id
        )
    )

    connection.commit()

    connection.close()

# ============================================================
# GET USER XP
# ============================================================

def get_user_xp(
    guild_id: int,
    user_id: int
):
    """
    Return the user's current XP and level.

    Returns:
        (bounty, level)
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT xp, level
        FROM user_xp
        WHERE guild_id = ?
        AND user_id = ?
        """,
        (
            guild_id,
            user_id
        )
    )

    result = cursor.fetchone()

    connection.close()

    if result is None:
        return 0, 0

    return result

# ============================================================
# ADD XP
# ============================================================

def add_xp(
    guild_id: int,
    user_id: int,
    amount: int
):
    """
    Add XP to a user.

    Returns:

        old_xp
        new_xp
        old_level
        new_level

    This allows the event system to detect
    whether the user has leveled up.
    """

    connection = get_connection()

    cursor = connection.cursor()


    # --------------------------------------------------------
    # Make sure user exists
    # --------------------------------------------------------

    cursor.execute(
        """
        INSERT OR IGNORE INTO user_xp
        (
            guild_id,
            user_id,
            xp,
            level
        )
        VALUES (?, ?, 0, 0)
        """,
        (
            guild_id,
            user_id
        )
    )


    # --------------------------------------------------------
    # Get current XP
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT xp, level
        FROM user_xp
        WHERE guild_id = ?
        AND user_id = ?
        """,
        (
            guild_id,
            user_id
        )
    )

    result = cursor.fetchone()

    old_xp, old_level = result


    # --------------------------------------------------------
    # Calculate new XP
    # --------------------------------------------------------

    new_xp = old_xp + amount


    # --------------------------------------------------------
    # Calculate new level
    # --------------------------------------------------------

    new_level = calculate_level(new_xp)


    # --------------------------------------------------------
    # Save new values
    # --------------------------------------------------------

    cursor.execute(
        """
        UPDATE user_xp
        SET xp = ?,
            level = ?,
            last_message_at = ?,
            last_decay_at = NULL
        WHERE guild_id = ?
        AND user_id = ?
        """,
        (
            new_xp,
            new_level,
            time.time(),
            guild_id,
            user_id
        )
    )


    connection.commit()

    connection.close()


    # --------------------------------------------------------
    # Return old and new values
    # --------------------------------------------------------

    return (
        old_xp,
        new_xp,
        old_level,
        new_level
    )

# ============================================================
# LEADERBOARD
# ============================================================

def get_leaderboard(
    guild_id: int,
    limit: int = 10
):
    """
    Return users ordered from highest XP
    to lowest XP.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT user_id, xp, level
        FROM user_xp
        WHERE guild_id = ?
        ORDER BY xp DESC
        LIMIT ?
        """,
        (
            guild_id,
            limit
        )
    )

    results = cursor.fetchall()

    connection.close()

    return results

# ============================================================
# SERVER RANK
# ============================================================

def get_user_rank(
    guild_id: int,
    user_id: int
):
    """
    Calculate a user's position on the server
    XP leaderboard.
    """

    connection = get_connection()

    cursor = connection.cursor()


    # --------------------------------------------------------
    # Get user's XP
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT xp
        FROM user_xp
        WHERE guild_id = ?
        AND user_id = ?
        """,
        (
            guild_id,
            user_id
        )
    )

    result = cursor.fetchone()

    if result is None:
        connection.close()
        return None

    user_xp = result[0]


    # --------------------------------------------------------
    # Count users with more XP
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM user_xp
        WHERE guild_id = ?
        AND xp > ?
        """,
        (
            guild_id,
            user_xp
        )
    )

    users_above = cursor.fetchone()[0]

    connection.close()


    return users_above + 1

# ============================================================
# XP SETTINGS
# ============================================================

def create_default_settings(
    guild_id: int
):
    """
    Create default XP settings for a guild
    if they don't already exist.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO xp_settings
        (
            guild_id,
            enabled,
            min_xp,
            max_xp,
            cooldown,
            levelup_channel_id
        )
        VALUES (?, 1, ?, ?, ?, NULL)
        """,
        (
            guild_id,
            DEFAULT_MIN_BOUNTY,
            DEFAULT_MAX_BOUNTY,
            DEFAULT_COOLDOWN
        )
    )

    connection.commit()

    connection.close()


def get_xp_settings(
    guild_id: int
):
    """
    Return all XP settings for a guild.

    Returns:

        enabled
        min_xp
        max_xp
        cooldown
        levelup_channel_id
    """

    create_default_settings(guild_id)

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            enabled,
            min_xp,
            max_xp,
            cooldown,
            levelup_channel_id
        FROM xp_settings
        WHERE guild_id = ?
        """,
        (guild_id,)
    )

    result = cursor.fetchone()

    connection.close()

    if result is None:
        return (
            1,
            DEFAULT_MIN_BOUNTY,
            DEFAULT_MAX_BOUNTY,
            DEFAULT_COOLDOWN,
            None,
        )

    return result


def update_xp_setting(
    guild_id: int,
    setting: str,
    value
):
    """
    Update one XP setting.

    Only predefined settings are allowed.
    """

    allowed_settings = {
        "enabled",
        "min_xp",
        "max_xp",
        "cooldown",
        "levelup_channel_id",

        "decay_enabled",
        "decay_grace_days",
        "decay_percent",
        "decay_interval_days",
        "max_decay",
    }

    if setting not in allowed_settings:
        raise ValueError(
            "Invalid Bounty setting."
        )

    create_default_settings(guild_id)

    connection = get_connection()

    cursor = connection.cursor()

    query = f"""
        UPDATE xp_settings
        SET {setting} = ?
        WHERE guild_id = ?
    """

    cursor.execute(
        query,
        (
            value,
            guild_id
        )
    )

    connection.commit()

    connection.close()

# ============================================================
# INACTIVITY DECAY
# ============================================================

def apply_inactivity_decay(guild_id: int):
    """
    Apply configured inactivity decay to inactive users.

    Returns:
        A list of tuples:
        (user_id, old_bounty, new_bounty)
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            decay_enabled,
            decay_grace_days,
            decay_percent,
            decay_interval_days,
            max_decay
        FROM xp_settings
        WHERE guild_id = ?
        """,
        (guild_id,),
    )

    settings = cursor.fetchone()

    if settings is None:
        connection.close()
        return []

    (
        decay_enabled,
        grace_days,
        decay_percent,
        interval_days,
        max_decay,
    ) = settings

    if not decay_enabled:
        connection.close()
        return []

    now = time.time()
    grace_seconds = grace_days * 86400
    interval_seconds = interval_days * 86400

    cursor.execute(
        """
        SELECT
            user_id,
            xp,
            last_message_at,
            last_decay_at
        FROM user_xp
        WHERE guild_id = ?
        AND xp > 0
        """,
        (guild_id,),
    )

    users = cursor.fetchall()
    decayed_users = []

    for user_id, bounty, last_message_at, last_decay_at in users:
        if last_message_at is None:
            continue

        inactive_for = now - last_message_at

        if inactive_for < grace_seconds:
            continue

        if last_decay_at is not None:
            if now - last_decay_at < interval_seconds:
                continue

        decay_amount = int(bounty * (decay_percent / 100))

        if decay_amount <= 0:
            continue

        decay_amount = min(decay_amount, max_decay)
        new_bounty = max(0, bounty - decay_amount)

        cursor.execute(
            """
            UPDATE user_xp
            SET xp = ?,
                level = ?,
                last_decay_at = ?
            WHERE guild_id = ?
            AND user_id = ?
            """,
            (
                new_bounty,
                calculate_level(new_bounty),
                now,
                guild_id,
                user_id,
            ),
        )

        decayed_users.append(
            (user_id, bounty, new_bounty)
        )

    connection.commit()
    connection.close()

    return decayed_users


# ============================================================
# IGNORED CHANNELS
# ============================================================

def is_channel_ignored(
    guild_id: int,
    channel_id: int
) -> bool:
    """
    Check whether a channel is ignored
    by the XP system.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT 1
        FROM xp_ignored_channels
        WHERE guild_id = ?
        AND channel_id = ?
        """,
        (
            guild_id,
            channel_id
        )
    )

    result = cursor.fetchone()

    connection.close()

    return result is not None


def add_ignored_channel(
    guild_id: int,
    channel_id: int
):
    """
    Add a channel to the XP ignore list.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO xp_ignored_channels
        (
            guild_id,
            channel_id
        )
        VALUES (?, ?)
        """,
        (
            guild_id,
            channel_id
        )
    )

    connection.commit()

    connection.close()


def remove_ignored_channel(
    guild_id: int,
    channel_id: int
):
    """
    Remove a channel from the XP ignore list.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM xp_ignored_channels
        WHERE guild_id = ?
        AND channel_id = ?
        """,
        (
            guild_id,
            channel_id
        )
    )

    connection.commit()

    connection.close()


def get_ignored_channels(
    guild_id: int
):
    """
    Return all ignored channel IDs.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT channel_id
        FROM xp_ignored_channels
        WHERE guild_id = ?
        """,
        (guild_id,)
    )

    results = cursor.fetchall()

    connection.close()

    return [
        row[0]
        for row in results
    ]

# ============================================================
# LEVEL REWARDS
# ============================================================

def add_level_reward(
    guild_id: int,
    level: int,
    role_id: int
):
    """
    Create or replace a role reward for a level.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT OR REPLACE INTO level_rewards
        (
            guild_id,
            level,
            role_id
        )
        VALUES (?, ?, ?)
        """,
        (
            guild_id,
            level,
            role_id
        )
    )

    connection.commit()

    connection.close()


def remove_level_reward(
    guild_id: int,
    level: int
):
    """
    Remove a role reward from a level.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM level_rewards
        WHERE guild_id = ?
        AND level = ?
        """,
        (
            guild_id,
            level
        )
    )

    connection.commit()

    connection.close()


def get_level_reward(
    guild_id: int,
    level: int
):
    """
    Return the Discord role ID associated
    with a particular level.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT role_id
        FROM level_rewards
        WHERE guild_id = ?
        AND level = ?
        """,
        (
            guild_id,
            level
        )
    )

    result = cursor.fetchone()

    connection.close()

    if result is None:
        return None

    return result[0]


def get_level_rewards(
    guild_id: int
):
    """
    Return all configured level rewards.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT level, role_id
        FROM level_rewards
        WHERE guild_id = ?
        ORDER BY level ASC
        """,
        (guild_id,)
    )

    results = cursor.fetchall()

    connection.close()

    return results