# ============================================================
# STRAW HAT — TEMPORARY VOICE CHANNEL SERVICE
# ============================================================

import json

from database.database import get_connection


# ============================================================
# CREATE TEMPORARY VOICE RECORD
# ============================================================

def create_voice_channel_record(
    guild_id: int,
    channel_id: int,
    owner_id: int
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT OR REPLACE INTO temporary_voice_channels
        (
            guild_id,
            channel_id,
            owner_id,
            join_order,
            locked,
            user_limit
        )
        VALUES (?, ?, ?, ?, 0, 0)
        """,
        (
            guild_id,
            channel_id,
            owner_id,
            json.dumps([owner_id])
        )
    )

    connection.commit()
    connection.close()


# ============================================================
# GET CHANNEL RECORD
# ============================================================

def get_voice_channel(channel_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            guild_id,
            channel_id,
            owner_id,
            join_order,
            locked,
            user_limit
        FROM temporary_voice_channels
        WHERE channel_id = ?
        """,
        (channel_id,)
    )

    result = cursor.fetchone()

    connection.close()

    if result is None:
        return None

    return {
        "guild_id": result[0],
        "channel_id": result[1],
        "owner_id": result[2],
        "join_order": json.loads(result[3]),
        "locked": bool(result[4]),
        "user_limit": result[5],
    }


# ============================================================
# ADD MEMBER TO JOIN ORDER
# ============================================================

def add_member_to_join_order(
    channel_id: int,
    user_id: int
):
    record = get_voice_channel(channel_id)

    if record is None:
        return

    join_order = record["join_order"]

    # Don't add duplicate active history entries.
    if user_id in join_order:
        return

    join_order.append(user_id)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE temporary_voice_channels
        SET join_order = ?
        WHERE channel_id = ?
        """,
        (
            json.dumps(join_order),
            channel_id
        )
    )

    connection.commit()
    connection.close()


# ============================================================
# SET OWNER
# ============================================================

def set_voice_owner(
    channel_id: int,
    owner_id: int
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE temporary_voice_channels
        SET owner_id = ?
        WHERE channel_id = ?
        """,
        (
            owner_id,
            channel_id
        )
    )

    connection.commit()
    connection.close()


# ============================================================
# SET LOCK STATE
# ============================================================

def set_voice_locked(
    channel_id: int,
    locked: bool
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE temporary_voice_channels
        SET locked = ?
        WHERE channel_id = ?
        """,
        (
            1 if locked else 0,
            channel_id
        )
    )

    connection.commit()
    connection.close()


# ============================================================
# SET USER LIMIT
# ============================================================

def set_voice_limit(
    channel_id: int,
    user_limit: int
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE temporary_voice_channels
        SET user_limit = ?
        WHERE channel_id = ?
        """,
        (
            user_limit,
            channel_id
        )
    )

    connection.commit()
    connection.close()


# ============================================================
# DELETE RECORD
# ============================================================

def delete_voice_channel_record(
    channel_id: int
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM temporary_voice_channels
        WHERE channel_id = ?
        """,
        (channel_id,)
    )

    connection.commit()
    connection.close()


# ============================================================
# GET ALL TEMPORARY CHANNELS
# ============================================================

def get_all_voice_channels():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT channel_id
        FROM temporary_voice_channels
        """
    )

    result = cursor.fetchall()

    connection.close()

    return [
        row[0]
        for row in result
    ]