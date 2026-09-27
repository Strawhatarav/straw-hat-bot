from database.database import get_connection


def create_giveaway(
    guild_id: int,
    channel_id: int,
    prize: str,
    host_id: int,
    winner_count: int,
    started_at: int,
    ends_at: int,
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO giveaways (
            guild_id,
            channel_id,
            message_id,
            prize,
            host_id,
            winner_count,
            started_at,
            ends_at,
            status,
            ended_at
        )
        VALUES (?, ?, NULL, ?, ?, ?, ?, ?, 'active', NULL)
        """,
        (
            guild_id,
            channel_id,
            prize,
            host_id,
            winner_count,
            started_at,
            ends_at,
        ),
    )

    giveaway_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return giveaway_id


def set_message_id(giveaway_id: int, message_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE giveaways
        SET message_id = ?
        WHERE id = ?
        """,
        (message_id, giveaway_id),
    )

    connection.commit()
    connection.close()


def get_giveaway(giveaway_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            guild_id,
            channel_id,
            message_id,
            prize,
            host_id,
            winner_count,
            started_at,
            ends_at,
            status,
            ended_at
        FROM giveaways
        WHERE id = ?
        """,
        (giveaway_id,),
    )

    giveaway = cursor.fetchone()

    connection.close()

    return giveaway


def get_active_giveaway(giveaway_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            guild_id,
            channel_id,
            message_id,
            prize,
            host_id,
            winner_count,
            started_at,
            ends_at,
            status,
            ended_at
        FROM giveaways
        WHERE id = ?
        AND status = 'active'
        """,
        (giveaway_id,),
    )

    giveaway = cursor.fetchone()

    connection.close()

    return giveaway


def set_giveaway_status(
    giveaway_id: int,
    status: str,
    ended_at: int | None = None,
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE giveaways
        SET status = ?, ended_at = ?
        WHERE id = ?
        """,
        (status, ended_at, giveaway_id),
    )

    connection.commit()
    connection.close()


def add_entry(giveaway_id: int, user_id: int) -> bool:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT 1
        FROM giveaway_entries
        WHERE giveaway_id = ?
        AND user_id = ?
        """,
        (giveaway_id, user_id),
    )

    existing = cursor.fetchone()

    if existing:
        connection.close()
        return False

    cursor.execute(
        """
        INSERT INTO giveaway_entries (
            giveaway_id,
            user_id,
            entered_at
        )
        VALUES (?, ?, strftime('%s', 'now'))
        """,
        (giveaway_id, user_id),
    )

    connection.commit()
    connection.close()

    return True


def get_entries(giveaway_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT user_id
        FROM giveaway_entries
        WHERE giveaway_id = ?
        ORDER BY entered_at ASC
        """,
        (giveaway_id,),
    )

    entries = [row[0] for row in cursor.fetchall()]

    connection.close()

    return entries


def get_entry_count(giveaway_id: int) -> int:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM giveaway_entries
        WHERE giveaway_id = ?
        """,
        (giveaway_id,),
    )

    count = cursor.fetchone()[0]

    connection.close()

    return count


def add_winner(giveaway_id: int, user_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO giveaway_winners (
            giveaway_id,
            user_id,
            selected_at
        )
        VALUES (?, ?, strftime('%s', 'now'))
        """,
        (giveaway_id, user_id),
    )

    connection.commit()
    connection.close()


def get_winners(giveaway_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT user_id
        FROM giveaway_winners
        WHERE giveaway_id = ?
        ORDER BY selected_at ASC
        """,
        (giveaway_id,),
    )

    winners = [row[0] for row in cursor.fetchall()]

    connection.close()

    return winners


def get_ended_giveaways():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            guild_id,
            channel_id,
            message_id,
            prize,
            host_id,
            winner_count,
            started_at,
            ends_at,
            status,
            ended_at
        FROM giveaways
        WHERE status = 'active'
        AND ends_at <= strftime('%s', 'now')
        ORDER BY ends_at ASC
        """
    )

    giveaways = cursor.fetchall()

    connection.close()

    return giveaways


def get_active_giveaways():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            guild_id,
            channel_id,
            message_id,
            prize,
            host_id,
            winner_count,
            started_at,
            ends_at,
            status,
            ended_at
        FROM giveaways
        WHERE status = 'active'
        ORDER BY ends_at ASC
        """
    )

    giveaways = cursor.fetchall()

    connection.close()

    return giveaways


def delete_winners(giveaway_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM giveaway_winners
        WHERE giveaway_id = ?
        """,
        (giveaway_id,),
    )

    connection.commit()
    connection.close()