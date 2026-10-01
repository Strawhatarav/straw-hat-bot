import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DATABASE_PATH = Path("database/strawhat.db")


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection

def initialize_moderation_database():
    with get_connection() as connection:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS moderation_config (
                guild_id INTEGER PRIMARY KEY,
                mod_log_channel_id INTEGER,
                automod_log_channel_id INTEGER,
                impel_town_channel_id INTEGER,
                restricted_role_id INTEGER,
                automod_enabled INTEGER NOT NULL DEFAULT 0,
                spam_enabled INTEGER NOT NULL DEFAULT 0,
                links_enabled INTEGER NOT NULL DEFAULT 0,
                bad_words_enabled INTEGER NOT NULL DEFAULT 0,
                raid_enabled INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS moderation_warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                reason TEXT NOT NULL,
                created_at TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1
            );

            CREATE INDEX IF NOT EXISTS idx_moderation_warnings
            ON moderation_warnings(guild_id, user_id, active);

            CREATE TABLE IF NOT EXISTS moderation_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                target_id INTEGER,
                moderator_id INTEGER,
                action TEXT NOT NULL,
                reason TEXT,
                created_at TEXT NOT NULL
            );
        """)

def ensure_config(guild_id):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO moderation_config (guild_id)
            VALUES (?)
            """,
            (guild_id,)
        )

def get_config(guild_id):
    ensure_config(guild_id)

    with get_connection() as connection:
        return connection.execute(
            """
            SELECT * FROM moderation_config
            WHERE guild_id = ?
            """,
            (guild_id,)
        ).fetchone()

def set_config_value(guild_id, column, value):
    allowed = {
        "mod_log_channel_id",
        "automod_log_channel_id",
        "impel_town_channel_id",
        "restricted_role_id",
        "automod_enabled",
        "spam_enabled",
        "links_enabled",
        "bad_words_enabled",
        "raid_enabled",
    }

    if column not in allowed:
        raise ValueError("Invalid moderation setting.")

    ensure_config(guild_id)

    with get_connection() as connection:
        connection.execute(
            f"""
            UPDATE moderation_config
            SET {column} = ?
            WHERE guild_id = ?
            """,
            (value, guild_id)
        )

def add_warning(guild_id, user_id, moderator_id, reason):
    created_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO moderation_warnings
            (guild_id, user_id, moderator_id, reason, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (guild_id, user_id, moderator_id, reason, created_at)
        )
        return cursor.lastrowid

def get_warnings(guild_id, user_id, active_only=True):
    query = """
        SELECT * FROM moderation_warnings
        WHERE guild_id = ? AND user_id = ?
    """
    params = [guild_id, user_id]

    if active_only:
        query += " AND active = 1"

    query += " ORDER BY id DESC"

    with get_connection() as connection:
        return connection.execute(query, params).fetchall()

def clear_warnings(guild_id, user_id):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE moderation_warnings
            SET active = 0
            WHERE guild_id = ? AND user_id = ? AND active = 1
            """,
            (guild_id, user_id)
        )
        return cursor.rowcount

def log_action(guild_id, target_id, moderator_id, action, reason):
    created_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO moderation_actions
            (guild_id, target_id, moderator_id, action, reason, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                guild_id,
                target_id,
                moderator_id,
                action,
                reason,
                created_at
            )
        )

