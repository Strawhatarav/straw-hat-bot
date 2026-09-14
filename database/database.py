import sqlite3
from pathlib import Path

DATABASE_PATH = Path("database/strawhat.db")

def get_connection():
    return sqlite3.connect(DATABASE_PATH)

def initialize_database():
    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS guild_config (
            guild_id INTEGER PRIMARY KEY,
            welcome_channel_id INTEGER,
            goodbye_channel_id INTEGER,
            default_role_id INTEGER,
            welcome_message TEXT,
            goodbye_message TEXT
        )
        """
    )

    connection.commit()
    connection.close()

def get_guild_config(guild_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            guild_id,
            welcome_channel_id,
            goodbye_channel_id,
            default_role_id,
            welcome_message,
            goodbye_message
        FROM guild_config
        WHERE guild_id = ?
        """,
        (guild_id,)
    )

    config = cursor.fetchone()

    connection.close()

    return config

def create_guild_config(guild_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO guild_config (guild_id)
        VALUES (?)
        """,
        (guild_id,)
    )

    connection.commit()
    connection.close()

def update_welcome_channel(guild_id, channel_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE guild_config
        SET welcome_channel_id = ?
        WHERE guild_id = ?
        """,
        (channel_id, guild_id)
    )

    connection.commit()
    connection.close()

def update_goodbye_channel(guild_id, channel_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE guild_config
        SET goodbye_channel_id = ?
        WHERE guild_id = ?
        """,
        (channel_id, guild_id)
    )

    connection.commit()
    connection.close()   

def update_default_role(guild_id, role_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE guild_config
        SET default_role_id = ?
        WHERE guild_id = ?
        """,
        (role_id, guild_id)
    )

    connection.commit()
    connection.close()

def update_welcome_message(guild_id, message):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE guild_config
        SET welcome_message = ?
        WHERE guild_id = ?
        """,
        (message, guild_id)
    )

    connection.commit()
    connection.close()

def update_goodbye_message(guild_id, message):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE guild_config
        SET welcome_message = ?
        WHERE guild_id = ?
        """,
        (message, guild_id)
    )

    connection.commit()
    connection.close()                 