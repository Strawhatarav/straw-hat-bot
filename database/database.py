import sqlite3
from pathlib import Path
from config.achievement_config import DEFAULT_ACHIEVEMENTS
from config.settings import GUILD_ID

DATABASE_PATH = Path("database/strawhat.db")
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

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

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS self_roles (
            guild_id INTEGER NOT NULL,
            role_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            PRIMARY KEY (guild_id, role_id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS polls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL,
            message_id INTEGER,
            creator_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            options TEXT NOT NULL,
            multiple_choice INTEGER NOT NULL DEFAULT 0,
            anonymous INTEGER NOT NULL DEFAULT 0,
            ends_at TEXT,
            closed INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS poll_votes (
            poll_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            option_index INTEGER NOT NULL,
            PRIMARY KEY (poll_id, user_id, option_index)
        )
        """
    )

    # ========================================================
    # XP USER TABLE
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_xp (
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            xp INTEGER NOT NULL DEFAULT 0,
            level INTEGER NOT NULL DEFAULT 0,
            last_message_at REAL,
            last_decay_at REAL,
            PRIMARY KEY (guild_id, user_id)
        )
    """)


    # ========================================================
    # XP SETTINGS TABLE
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS xp_settings (
            guild_id INTEGER PRIMARY KEY,
            enabled INTEGER NOT NULL DEFAULT 1,
            min_xp INTEGER NOT NULL DEFAULT 15,
            max_xp INTEGER NOT NULL DEFAULT 25,
            cooldown INTEGER NOT NULL DEFAULT 60,
            levelup_channel_id INTEGER,
            decay_enabled INTEGER NOT NULL DEFAULT 1,
            decay_grace_days INTEGER NOT NULL DEFAULT 14,
            decay_percent INTEGER NOT NULL DEFAULT 5,
            decay_interval_days INTEGER NOT NULL DEFAULT 7,
            max_decay INTEGER NOT NULL DEFAULT 500
        )
    """)


    # ========================================================
    # BOUNTY DATABASE MIGRATIONS
    # ========================================================

    # CREATE TABLE IF NOT EXISTS does not add new columns to an
    # existing SQLite table, so we add the Phase 8 columns here.

    cursor.execute("PRAGMA table_info(user_xp)")
    user_xp_columns = {
        column[1]
        for column in cursor.fetchall()
    }

    if "last_message_at" not in user_xp_columns:
        cursor.execute(
            "ALTER TABLE user_xp ADD COLUMN last_message_at REAL"
        )

    if "last_decay_at" not in user_xp_columns:
        cursor.execute(
            "ALTER TABLE user_xp ADD COLUMN last_decay_at REAL"
        )

    cursor.execute("PRAGMA table_info(xp_settings)")
    xp_settings_columns = {
        column[1]
        for column in cursor.fetchall()
    }

    xp_setting_defaults = {
        "decay_enabled": "INTEGER NOT NULL DEFAULT 1",
        "decay_grace_days": "INTEGER NOT NULL DEFAULT 14",
        "decay_percent": "INTEGER NOT NULL DEFAULT 5",
        "decay_interval_days": "INTEGER NOT NULL DEFAULT 7",
        "max_decay": "INTEGER NOT NULL DEFAULT 500",
    }

    for column_name, definition in xp_setting_defaults.items():
        if column_name not in xp_settings_columns:
            cursor.execute(
                f"ALTER TABLE xp_settings ADD COLUMN "
                f"{column_name} {definition}"
            )

    # ========================================================
    # IGNORED CHANNELS TABLE
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS xp_ignored_channels (
            guild_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL,

            PRIMARY KEY (guild_id, channel_id)
        )
    """)


    # ========================================================
    # LEVEL REWARDS TABLE
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS level_rewards (
            guild_id INTEGER NOT NULL,
            level INTEGER NOT NULL,
            role_id INTEGER NOT NULL,

            PRIMARY KEY (guild_id, level)
        )
    """)

    # ============================================================
    # ACHIEVEMENT TABLES
    # ============================================================
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS achievements (
            achievement_id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            achievement_key TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            rarity TEXT NOT NULL,
            hidden INTEGER NOT NULL DEFAULT 0,
            requirement_type TEXT NOT NULL,
            requirement_value INTEGER NOT NULL DEFAULT 1,
            reward_bounty INTEGER NOT NULL DEFAULT 0,
    
            UNIQUE(guild_id, achievement_key)
        )
    """)
    
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_achievements (
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            achievement_id INTEGER NOT NULL,
            unlocked_at REAL NOT NULL,
    
            PRIMARY KEY (
                guild_id,
                user_id,
                achievement_id
            ),
    
            FOREIGN KEY (achievement_id)
            REFERENCES achievements(achievement_id)
        )
    """)
    
    
    # ------------------------------------------------------------
    # Tracks user statistics needed by achievements.
    # ------------------------------------------------------------
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS achievement_stats (
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
    
            message_count INTEGER NOT NULL DEFAULT 0,
            starboard_posts INTEGER NOT NULL DEFAULT 0,
    
            PRIMARY KEY (guild_id, user_id)
        )
    """)

    # ============================================================
    # INSERT DEFAULT ACHIEVEMENTS
    # ============================================================
    
    for achievement in DEFAULT_ACHIEVEMENTS:
    
        cursor.execute("""
            INSERT OR IGNORE INTO achievements (
                guild_id,
                achievement_key,
                name,
                description,
                category,
                rarity,
                hidden,
                requirement_type,
                requirement_value,
                reward_bounty
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            GUILD_ID,
            achievement["key"],
            achievement["name"],
            achievement["description"],
            achievement["category"],
            achievement["rarity"],
            int(achievement["hidden"]),
            achievement["requirement_type"],
            achievement["requirement_value"],
            achievement["reward_bounty"],
        ))

    
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
        SET goodbye_message = ?
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
        SET goodbye_message = ?
        WHERE guild_id = ?
        """,
        (message, guild_id)
    )

    connection.commit()
    connection.close()                 

def add_self_role(
    guild_id: int,
    role_id: int,
    category: str
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT OR REPLACE INTO self_roles
        (guild_id, role_id, category)
        VALUES (?, ?, ?)
        """,
        (guild_id, role_id, category)
    )

    connection.commit()
    connection.close()

def remove_self_role(
    guild_id: int,
    role_id: int
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM self_roles
        WHERE guild_id = ?
        AND role_id = ?
        """,
        (guild_id, role_id)
    )

    connection.commit()
    connection.close()

def is_self_role(
    guild_id: int,
    role_id: int
) -> bool:

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT 1
        FROM self_roles
        WHERE guild_id = ?
        AND role_id = ?
        """,
        (guild_id, role_id)
    )

    result = cursor.fetchone()

    connection.close()

    return result is not None

def get_self_roles(
    guild_id: int,
    category: str | None = None
):

    connection = get_connection()
    cursor = connection.cursor()

    if category is None:
        cursor.execute(
            """
            SELECT role_id, category
            FROM self_roles
            WHERE guild_id = ?
            """,
            (guild_id,)
        )
    else:
        cursor.execute(
            """
            SELECT role_id, category
            FROM self_roles
            WHERE guild_id = ?
            AND category = ?
            """,
            (guild_id, category)
        )

    results = cursor.fetchall()

    connection.close()

    return results