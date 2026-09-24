# ============================================================
# STRAW HAT REMINDER SERVICE
# ============================================================

import sqlite3

from datetime import datetime, timezone, timedelta

from database.database import DATABASE_PATH


# ============================================================
# LIMITS
# ============================================================

MAX_PERSONAL_REMINDERS = 25
MAX_SERVER_SCHEDULES = 50
MAX_RECURRING_REMINDERS = 10

MAX_MESSAGE_LENGTH = 500

MAX_REMINDER_DAYS = 365


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    return sqlite3.connect(
        DATABASE_PATH
    )


# ============================================================
# TIME HELPERS
# ============================================================

def utc_now():

    return datetime.now(
        timezone.utc
    )

def datetime_to_string(value):

    return value.astimezone(
        timezone.utc
    ).isoformat()

def string_to_datetime(value):

    return datetime.fromisoformat(
        value
    )

# ============================================================
# TIMEZONE
# ============================================================

def get_user_timezone(
    user_id: int
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT timezone
        FROM user_timezones
        WHERE user_id = ?
        """,
        (user_id,)
    )

    result = cursor.fetchone()

    connection.close()

    if result is None:
        return "UTC"

    return result[0]

def set_user_timezone(
    user_id: int,
    timezone_name: str
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO user_timezones
        (
            user_id,
            timezone
        )
        VALUES (?, ?)

        ON CONFLICT(user_id)
        DO UPDATE SET timezone = excluded.timezone
        """,
        (
            user_id,
            timezone_name
        )
    )

    connection.commit()

    connection.close()

# ============================================================
# COUNT PERSONAL REMINDERS
# ============================================================

def count_personal_reminders(
    user_id: int
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM reminders
        WHERE user_id = ?
        AND active = 1
        AND recurring = 0
        """,
        (user_id,)
    )

    count = cursor.fetchone()[0]

    connection.close()

    return count

# ============================================================
# COUNT RECURRING REMINDERS
# ============================================================

def count_recurring_reminders(
    user_id: int
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM reminders
        WHERE user_id = ?
        AND active = 1
        AND recurring = 1
        """,
        (user_id,)
    )

    count = cursor.fetchone()[0]

    connection.close()

    return count

# ============================================================
# COUNT SERVER SCHEDULES
# ============================================================

def count_server_schedules(
    guild_id: int
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM reminders
        WHERE guild_id = ?
        AND active = 1
        """,
        (guild_id,)
    )

    count = cursor.fetchone()[0]

    connection.close()

    return count

# ============================================================
# CREATE REMINDER
# ============================================================

def create_reminder(
    user_id: int,
    guild_id,
    channel_id,
    message: str,
    scheduled_at: datetime,
    timezone_name: str = "UTC",
    recurring: bool = False,
    recurrence: str | None = None
):

    connection = get_connection()

    cursor = connection.cursor()

    created_at = utc_now()

    cursor.execute(
        """
        INSERT INTO reminders
        (
            user_id,
            guild_id,
            channel_id,
            message,
            reminder_type,
            scheduled_at,
            timezone,
            recurring,
            recurrence,
            active,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
        """,
        (
            user_id,
            guild_id,
            channel_id,
            message,
            (
                "recurring"
                if recurring
                else (
                    "server"
                    if guild_id is not None
                    else "personal"
                )
            ),
            datetime_to_string(
                scheduled_at
            ),
            timezone_name,
            1 if recurring else 0,
            recurrence,
            datetime_to_string(
                created_at
            )
        )
    )

    reminder_id = cursor.lastrowid

    connection.commit()

    connection.close()

    return reminder_id

# ============================================================
# GET USER REMINDERS
# ============================================================

def get_user_reminders(
    user_id: int
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            message,
            scheduled_at,
            timezone,
            recurring,
            recurrence,
            guild_id,
            channel_id
        FROM reminders
        WHERE user_id = ?
        AND active = 1
        ORDER BY scheduled_at ASC
        """,
        (user_id,)
    )

    results = cursor.fetchall()

    connection.close()

    return results

# ============================================================
# GET REMINDER
# ============================================================

def get_reminder(
    reminder_id: int,
    user_id: int
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            message,
            scheduled_at,
            timezone,
            recurring,
            recurrence,
            guild_id,
            channel_id
        FROM reminders
        WHERE id = ?
        AND user_id = ?
        AND active = 1
        """,
        (
            reminder_id,
            user_id
        )
    )

    result = cursor.fetchone()

    connection.close()

    return result

# ============================================================
# CANCEL REMINDER
# ============================================================

def cancel_reminder(
    reminder_id: int,
    user_id: int
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM reminders
        WHERE id = ?
        AND user_id = ?
        """,
        (
            reminder_id,
            user_id
        )
    )

    deleted = cursor.rowcount > 0

    connection.commit()

    connection.close()

    return deleted

# ============================================================
# GET DUE REMINDERS
# ============================================================

def get_due_reminders():

    connection = get_connection()

    cursor = connection.cursor()

    now = datetime_to_string(
        utc_now()
    )

    cursor.execute(
        """
        SELECT
            id,
            user_id,
            guild_id,
            channel_id,
            message,
            reminder_type,
            scheduled_at,
            timezone,
            recurring,
            recurrence
        FROM reminders
        WHERE active = 1
        AND scheduled_at <= ?
        ORDER BY scheduled_at ASC
        """,
        (now,)
    )

    results = cursor.fetchall()

    connection.close()

    return results

# ============================================================
# DELETE ONE-TIME REMINDER
# ============================================================

def delete_reminder(
    reminder_id: int
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM reminders
        WHERE id = ?
        """,
        (reminder_id,)
    )

    connection.commit()

    connection.close()

# ============================================================
# UPDATE RECURRING REMINDER
# ============================================================

def update_next_occurrence(
    reminder_id: int,
    next_time: datetime
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE reminders
        SET scheduled_at = ?
        WHERE id = ?
        """,
        (
            datetime_to_string(
                next_time
            ),
            reminder_id
        )
    )

    connection.commit()

    connection.close()