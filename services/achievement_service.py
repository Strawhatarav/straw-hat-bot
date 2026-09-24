import sqlite3
import time

from database.database import get_connection


# ============================================================
# ACHIEVEMENT SERVICE
# ============================================================
# This file contains achievement BUSINESS LOGIC.
#
# It does not listen to Discord events.
# It does not create Discord embeds.
#
# It simply manages achievement data.
# ============================================================


def get_achievement_by_key(guild_id: int, key: str):
    """
    Find an achievement using its internal key.
    """

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM achievements
        WHERE guild_id = ?
        AND achievement_key = ?
    """, (guild_id, key))

    result = cursor.fetchone()

    conn.close()

    return result


def is_unlocked(
    guild_id: int,
    user_id: int,
    achievement_id: int
) -> bool:
    """
    Check whether a user has already unlocked an achievement.
    """

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT 1
        FROM user_achievements
        WHERE guild_id = ?
        AND user_id = ?
        AND achievement_id = ?
    """, (
        guild_id,
        user_id,
        achievement_id
    ))

    result = cursor.fetchone()

    conn.close()

    return result is not None


def unlock_achievement(
    guild_id: int,
    user_id: int,
    achievement_id: int
) -> bool:
    """
    Unlock an achievement.

    Returns:
        True  -> newly unlocked
        False -> already unlocked
    """

    conn = get_connection()

    cursor = conn.cursor()

    # Prevent duplicate unlocks.
    cursor.execute("""
        SELECT 1
        FROM user_achievements
        WHERE guild_id = ?
        AND user_id = ?
        AND achievement_id = ?
    """, (
        guild_id,
        user_id,
        achievement_id
    ))

    if cursor.fetchone():
        conn.close()
        return False

    cursor.execute("""
        INSERT INTO user_achievements (
            guild_id,
            user_id,
            achievement_id,
            unlocked_at
        )
        VALUES (?, ?, ?, ?)
    """, (
        guild_id,
        user_id,
        achievement_id,
        time.time()
    ))

    conn.commit()
    conn.close()

    return True


def increment_message_count(
    guild_id: int,
    user_id: int
):
    """
    Increase the user's message counter by one.
    """

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO achievement_stats (
            guild_id,
            user_id,
            message_count
        )
        VALUES (?, ?, 1)

        ON CONFLICT(guild_id, user_id)
        DO UPDATE SET
            message_count = message_count + 1
    """, (
        guild_id,
        user_id
    ))

    conn.commit()
    conn.close()


def get_message_count(
    guild_id: int,
    user_id: int
) -> int:
    """
    Return the user's total tracked messages.
    """

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT message_count
        FROM achievement_stats
        WHERE guild_id = ?
        AND user_id = ?
    """, (
        guild_id,
        user_id
    ))

    row = cursor.fetchone()

    conn.close()

    if row is None:
        return 0

    return row[0]


def increment_starboard_posts(
    guild_id: int,
    user_id: int
):
    """
    Increase the number of messages a user
    has successfully placed on Starboard.
    """

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO achievement_stats (
            guild_id,
            user_id,
            starboard_posts
        )
        VALUES (?, ?, 1)

        ON CONFLICT(guild_id, user_id)
        DO UPDATE SET
            starboard_posts = starboard_posts + 1
    """, (
        guild_id,
        user_id
    ))

    conn.commit()
    conn.close()


def get_starboard_posts(
    guild_id: int,
    user_id: int
) -> int:

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT starboard_posts
        FROM achievement_stats
        WHERE guild_id = ?
        AND user_id = ?
    """, (
        guild_id,
        user_id
    ))

    row = cursor.fetchone()

    conn.close()

    if row is None:
        return 0

    return row[0]


def get_user_achievements(
    guild_id: int,
    user_id: int
):
    """
    Return all achievements and whether the user
    has unlocked them.
    """

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            a.*,
            ua.unlocked_at
        FROM achievements a
        LEFT JOIN user_achievements ua
            ON a.achievement_id = ua.achievement_id
            AND ua.guild_id = ?
            AND ua.user_id = ?
        WHERE a.guild_id = ?
        ORDER BY a.achievement_id
    """, (
        guild_id,
        user_id,
        guild_id
    ))

    rows = cursor.fetchall()

    conn.close()

    return rows

# ============================================================
# PROCESS MESSAGE ACHIEVEMENTS
# ============================================================

def process_message_achievements(
    guild_id: int,
    user_id: int
):
    """
    Process achievements related to sending messages.

    Returns:
        List of achievement keys that were newly unlocked.
    """

    unlocked = []

    # --------------------------------------------------------
    # Increase message counter
    # --------------------------------------------------------

    increment_message_count(
        guild_id,
        user_id
    )

    message_count = get_message_count(
        guild_id,
        user_id
    )

    # --------------------------------------------------------
    # First Message
    # --------------------------------------------------------

    if message_count >= 1:

        achievement = get_achievement_by_key(
            guild_id,
            "first_message"
        )

        if achievement:

            newly_unlocked = unlock_achievement(
                guild_id,
                user_id,
                achievement[0]
            )

            if newly_unlocked:
                unlocked.append(
                    "first_message"
                )

    # --------------------------------------------------------
    # 100 Messages
    # --------------------------------------------------------

    if message_count >= 100:

        achievement = get_achievement_by_key(
            guild_id,
            "message_100"
        )

        if achievement:

            newly_unlocked = unlock_achievement(
                guild_id,
                user_id,
                achievement[0]
            )

            if newly_unlocked:
                unlocked.append(
                    "message_100"
                )

    return unlocked