from database.database import get_connection


# ============================================================
# STARBOARD SETTINGS
# ============================================================

def get_settings(guild_id: int):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            guild_id,
            channel_id,
            threshold,
            enabled
        FROM starboard_settings
        WHERE guild_id = ?
    """, (guild_id,))

    row = cursor.fetchone()

    conn.close()

    return row


def create_default_settings(guild_id: int):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO starboard_settings (
            guild_id,
            threshold,
            enabled
        )
        VALUES (?, 3, 0)
    """, (guild_id,))

    conn.commit()
    conn.close()


def update_setting(
    guild_id: int,
    setting: str,
    value
):

    allowed_settings = {
        "channel_id",
        "threshold",
        "enabled"
    }

    if setting not in allowed_settings:
        raise ValueError(
            "Invalid Starboard setting."
        )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        f"""
        UPDATE starboard_settings
        SET {setting} = ?
        WHERE guild_id = ?
        """,
        (
            value,
            guild_id
        )
    )

    conn.commit()
    conn.close()


# ============================================================
# STARBOARD MESSAGE MAPPING
# ============================================================

def get_starboard_message(
    guild_id: int,
    original_message_id: int
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            starboard_message_id,
            star_count
        FROM starboard_messages
        WHERE guild_id = ?
        AND original_message_id = ?
    """, (
        guild_id,
        original_message_id
    ))

    row = cursor.fetchone()

    conn.close()

    return row


def save_starboard_message(
    guild_id: int,
    original_message_id: int,
    starboard_message_id: int,
    star_count: int
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO starboard_messages (
            guild_id,
            original_message_id,
            starboard_message_id,
            star_count
        )
        VALUES (?, ?, ?, ?)
    """, (
        guild_id,
        original_message_id,
        starboard_message_id,
        star_count
    ))

    conn.commit()
    conn.close()


def update_star_count(
    guild_id: int,
    original_message_id: int,
    star_count: int
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE starboard_messages
        SET star_count = ?
        WHERE guild_id = ?
        AND original_message_id = ?
    """, (
        star_count,
        guild_id,
        original_message_id
    ))

    conn.commit()
    conn.close()


def delete_starboard_message(
    guild_id: int,
    original_message_id: int
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM starboard_messages
        WHERE guild_id = ?
        AND original_message_id = ?
    """, (
        guild_id,
        original_message_id
    ))

    conn.commit()
    conn.close()