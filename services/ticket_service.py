# ============================================================
# STRAW HAT TICKET SERVICE
# ============================================================

import sqlite3
from datetime import datetime, timezone

from database.database import DATABASE_PATH


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    return sqlite3.connect(DATABASE_PATH)


# ============================================================
# TICKET CONFIGURATION
# ============================================================

def save_ticket_config(
    guild_id: int,
    panel_channel_id: int,
    ticket_category_id: int,
    staff_role_id: int,
    log_channel_id: int
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO ticket_config
        (
            guild_id,
            panel_channel_id,
            ticket_category_id,
            staff_role_id,
            log_channel_id,
            enabled
        )
        VALUES (?, ?, ?, ?, ?, 1)

        ON CONFLICT(guild_id)
        DO UPDATE SET
            panel_channel_id = excluded.panel_channel_id,
            ticket_category_id = excluded.ticket_category_id,
            staff_role_id = excluded.staff_role_id,
            log_channel_id = excluded.log_channel_id,
            enabled = 1
        """,
        (
            guild_id,
            panel_channel_id,
            ticket_category_id,
            staff_role_id,
            log_channel_id
        )
    )

    connection.commit()
    connection.close()


def get_ticket_config(guild_id: int):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            guild_id,
            panel_channel_id,
            ticket_category_id,
            staff_role_id,
            log_channel_id,
            enabled
        FROM ticket_config
        WHERE guild_id = ?
        """,
        (guild_id,)
    )

    result = cursor.fetchone()

    connection.close()

    return result


def disable_ticket_system(guild_id: int):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE ticket_config
        SET enabled = 0
        WHERE guild_id = ?
        """,
        (guild_id,)
    )

    connection.commit()
    connection.close()


# ============================================================
# FIND OPEN TICKET
# ============================================================

def get_open_ticket(
    guild_id: int,
    user_id: int
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            guild_id,
            ticket_number,
            channel_id,
            user_id,
            category,
            status,
            claimed_by,
            created_at,
            closed_at,
            closed_by
        FROM tickets
        WHERE guild_id = ?
        AND user_id = ?
        AND status = 'open'
        LIMIT 1
        """,
        (
            guild_id,
            user_id
        )
    )

    result = cursor.fetchone()

    connection.close()

    return result


# ============================================================
# GET TICKET BY CHANNEL
# ============================================================

def get_ticket_by_channel(
    channel_id: int
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            guild_id,
            ticket_number,
            channel_id,
            user_id,
            category,
            status,
            claimed_by,
            created_at,
            closed_at,
            closed_by
        FROM tickets
        WHERE channel_id = ?
        LIMIT 1
        """,
        (channel_id,)
    )

    result = cursor.fetchone()

    connection.close()

    return result


# ============================================================
# NEXT TICKET NUMBER
# ============================================================

def get_next_ticket_number(
    guild_id: int
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT MAX(ticket_number)
        FROM tickets
        WHERE guild_id = ?
        """,
        (guild_id,)
    )

    result = cursor.fetchone()

    connection.close()

    if result is None or result[0] is None:
        return 1

    return result[0] + 1


# ============================================================
# CREATE TICKET
# ============================================================

def create_ticket(
    guild_id: int,
    channel_id: int,
    user_id: int,
    category: str,
    ticket_number: int
):

    connection = get_connection()
    cursor = connection.cursor()

    created_at = datetime.now(
        timezone.utc
    ).isoformat()

    cursor.execute(
        """
        INSERT INTO tickets
        (
            guild_id,
            ticket_number,
            channel_id,
            user_id,
            category,
            status,
            claimed_by,
            created_at,
            closed_at,
            closed_by
        )
        VALUES (?, ?, ?, ?, ?, 'open', NULL, ?, NULL, NULL)
        """,
        (
            guild_id,
            ticket_number,
            channel_id,
            user_id,
            category,
            created_at
        )
    )

    connection.commit()

    ticket_id = cursor.lastrowid

    connection.close()

    return ticket_id


# ============================================================
# CLAIM TICKET
# ============================================================

def claim_ticket(
    channel_id: int,
    user_id: int
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE tickets
        SET claimed_by = ?
        WHERE channel_id = ?
        AND status = 'open'
        """,
        (
            user_id,
            channel_id
        )
    )

    connection.commit()
    connection.close()


# ============================================================
# UNCLAIM TICKET
# ============================================================

def unclaim_ticket(
    channel_id: int
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE tickets
        SET claimed_by = NULL
        WHERE channel_id = ?
        """,
        (channel_id,)
    )

    connection.commit()
    connection.close()


# ============================================================
# CLOSE TICKET
# ============================================================

def close_ticket(
    channel_id: int,
    closed_by: int
):

    connection = get_connection()
    cursor = connection.cursor()

    closed_at = datetime.now(
        timezone.utc
    ).isoformat()

    cursor.execute(
        """
        UPDATE tickets
        SET
            status = 'closed',
            closed_at = ?,
            closed_by = ?
        WHERE channel_id = ?
        """,
        (
            closed_at,
            closed_by,
            channel_id
        )
    )

    connection.commit()
    connection.close()


# ============================================================
# REOPEN TICKET
# ============================================================

def reopen_ticket(
    channel_id: int
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE tickets
        SET
            status = 'open',
            closed_at = NULL,
            closed_by = NULL
        WHERE channel_id = ?
        """,
        (channel_id,)
    )

    connection.commit()
    connection.close()


# ============================================================
# DELETE TICKET RECORD
# ============================================================

def delete_ticket_record(
    channel_id: int
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM tickets
        WHERE channel_id = ?
        """,
        (channel_id,)
    )

    connection.commit()
    connection.close()