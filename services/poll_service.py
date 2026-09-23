import json
from datetime import datetime, timezone

from database.database import get_connection


def create_poll(
    guild_id: int,
    channel_id: int,
    creator_id: int,
    question: str,
    options: list[str],
    multiple_choice: bool,
    anonymous: bool,
    ends_at: datetime | None
) -> int:

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO polls (
            guild_id,
            channel_id,
            creator_id,
            question,
            options,
            multiple_choice,
            anonymous,
            ends_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            guild_id,
            channel_id,
            creator_id,
            question,
            json.dumps(options),
            int(multiple_choice),
            int(anonymous),
            ends_at.isoformat()
            if ends_at
            else None
        )
    )

    poll_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return poll_id

def get_poll(poll_id: int):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            guild_id,
            channel_id,
            message_id,
            creator_id,
            question,
            options,
            multiple_choice,
            anonymous,
            ends_at,
            closed
        FROM polls
        WHERE id = ?
        """,
        (poll_id,)
    )

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None

    return {
        "id": row[0],
        "guild_id": row[1],
        "channel_id": row[2],
        "message_id": row[3],
        "creator_id": row[4],
        "question": row[5],
        "options": json.loads(row[6]),
        "multiple_choice": bool(row[7]),
        "anonymous": bool(row[8]),
        "ends_at": (
            datetime.fromisoformat(row[9])
            if row[9]
            else None
        ),
        "closed": bool(row[10])
    }

def set_poll_message_id(
    poll_id: int,
    message_id: int
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE polls
        SET message_id = ?
        WHERE id = ?
        """,
        (
            message_id,
            poll_id
        )
    )

    connection.commit()
    connection.close()

def get_user_votes(
    poll_id: int,
    user_id: int
) -> list[int]:

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT option_index
        FROM poll_votes
        WHERE poll_id = ?
        AND user_id = ?
        """,
        (
            poll_id,
            user_id
        )
    )

    rows = cursor.fetchall()

    connection.close()

    return [
        row[0]
        for row in rows
    ]

def add_vote(
    poll_id: int,
    user_id: int,
    option_index: int
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO poll_votes (
            poll_id,
            user_id,
            option_index
        )
        VALUES (?, ?, ?)
        """,
        (
            poll_id,
            user_id,
            option_index
        )
    )

    connection.commit()
    connection.close()

def remove_vote(
    poll_id: int,
    user_id: int,
    option_index: int
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM poll_votes
        WHERE poll_id = ?
        AND user_id = ?
        AND option_index = ?
        """,
        (
            poll_id,
            user_id,
            option_index
        )
    )

    connection.commit()
    connection.close()

def clear_user_votes(
    poll_id: int,
    user_id: int
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM poll_votes
        WHERE poll_id = ?
        AND user_id = ?
        """,
        (
            poll_id,
            user_id
        )
    )

    connection.commit()
    connection.close()

def get_vote_counts(
    poll_id: int,
    option_count: int
) -> list[int]:

    connection = get_connection()

    cursor = connection.cursor()

    counts = [0] * option_count

    cursor.execute(
        """
        SELECT option_index, COUNT(*)
        FROM poll_votes
        WHERE poll_id = ?
        GROUP BY option_index
        """,
        (poll_id,)
    )

    rows = cursor.fetchall()

    connection.close()

    for option_index, count in rows:

        if 0 <= option_index < option_count:

            counts[option_index] = count

    return counts

def get_voters(
    poll_id: int,
    option_index: int
) -> list[int]:

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT user_id
        FROM poll_votes
        WHERE poll_id = ?
        AND option_index = ?
        """,
        (
            poll_id,
            option_index
        )
    )

    rows = cursor.fetchall()

    connection.close()

    return [
        row[0]
        for row in rows
    ]

def close_poll(poll_id: int):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE polls
        SET closed = 1
        WHERE id = ?
        """,
        (poll_id,)
    )

    connection.commit()
    connection.close()

def get_active_polls():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            guild_id,
            channel_id,
            message_id,
            creator_id,
            question,
            options,
            multiple_choice,
            anonymous,
            ends_at,
            closed
        FROM polls
        WHERE closed = 0
        """
    )

    rows = cursor.fetchall()

    connection.close()

    polls = []

    for row in rows:

        polls.append(
            {
                "id": row[0],
                "guild_id": row[1],
                "channel_id": row[2],
                "message_id": row[3],
                "creator_id": row[4],
                "question": row[5],
                "options": json.loads(row[6]),
                "multiple_choice": bool(row[7]),
                "anonymous": bool(row[8]),
                "ends_at": (
                    datetime.fromisoformat(row[9])
                    if row[9]
                    else None
                ),
                "closed": bool(row[10])
            }
        )

    return polls

def get_expired_polls():

    now = datetime.now(timezone.utc)

    active_polls = get_active_polls()

    expired = []

    for poll in active_polls:

        if poll["ends_at"] is None:
            continue

        if now >= poll["ends_at"]:
            expired.append(poll)

    return expired
