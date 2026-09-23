# ============================================================
# STRAW HAT ACHIEVEMENT CONFIGURATION
# ============================================================

# ------------------------------------------------------------
# Achievement categories
# ------------------------------------------------------------
# These are used for organizing achievements in /achievements.
# ------------------------------------------------------------

CATEGORY_SOCIAL = "Social"
CATEGORY_BOUNTY = "Bounty"
CATEGORY_CREW = "Crew"
CATEGORY_TIME = "Time"
CATEGORY_STARBOARD = "Starboard"
CATEGORY_SPECIAL = "Special"


# ------------------------------------------------------------
# Achievement rarity
# ------------------------------------------------------------
# Rarity is only a description of how uncommon an achievement is.
# It does NOT rank users.
# ------------------------------------------------------------

RARITY_COMMON = "Common"
RARITY_UNCOMMON = "Uncommon"
RARITY_RARE = "Rare"
RARITY_EPIC = "Epic"
RARITY_LEGENDARY = "Legendary"
RARITY_MYTHICAL = "Mythical"


# ------------------------------------------------------------
# Default achievements
# ------------------------------------------------------------
# These are automatically inserted into the database.
#
# "key" is an internal unique identifier.
# Never use the achievement's display name as the database ID.
# ------------------------------------------------------------

DEFAULT_ACHIEVEMENTS = [

    {
        "key": "straw_hat_member",
        "name": "🏴‍☠️ Straw Hat Member",
        "description": "Join the Straw Hat crew.",
        "category": CATEGORY_CREW,
        "rarity": RARITY_COMMON,
        "hidden": False,
        "requirement_type": "join",
        "requirement_value": 1,
        "reward_bounty": 100,
    },

    {
        "key": "first_message",
        "name": "💬 First Voyage",
        "description": "Send your first message in the server.",
        "category": CATEGORY_SOCIAL,
        "rarity": RARITY_COMMON,
        "hidden": False,
        "requirement_type": "messages",
        "requirement_value": 1,
        "reward_bounty": 50,
    },

    {
        "key": "message_100",
        "name": "💬 Chatterbox",
        "description": "Send 100 messages.",
        "category": CATEGORY_SOCIAL,
        "rarity": RARITY_UNCOMMON,
        "hidden": False,
        "requirement_type": "messages",
        "requirement_value": 100,
        "reward_bounty": 250,
    },

    {
        "key": "level_10",
        "name": "⚔️ Rising Pirate",
        "description": "Reach Bounty Level 10.",
        "category": CATEGORY_BOUNTY,
        "rarity": RARITY_UNCOMMON,
        "hidden": False,
        "requirement_type": "level",
        "requirement_value": 10,
        "reward_bounty": 250,
    },

    {
        "key": "level_50",
        "name": "🌊 Grand Line Veteran",
        "description": "Reach Bounty Level 50.",
        "category": CATEGORY_BOUNTY,
        "rarity": RARITY_LEGENDARY,
        "hidden": False,
        "requirement_type": "level",
        "requirement_value": 50,
        "reward_bounty": 1000,
    },

    {
        "key": "night_owl",
        "name": "🌙 Night Owl",
        "description": "Send a message during the night.",
        "category": CATEGORY_TIME,
        "rarity": RARITY_RARE,
        "hidden": False,
        "requirement_type": "night_message",
        "requirement_value": 1,
        "reward_bounty": 300,
    },

    {
        "key": "first_starboard",
        "name": "⭐ First Star",
        "description": "Get your first message onto the Starboard.",
        "category": CATEGORY_STARBOARD,
        "rarity": RARITY_COMMON,
        "hidden": False,
        "requirement_type": "starboard_posts",
        "requirement_value": 1,
        "reward_bounty": 100,
    },

    {
        "key": "star_10",
        "name": "🌟 Shining Star",
        "description": "Get 10 messages onto the Starboard.",
        "category": CATEGORY_STARBOARD,
        "rarity": RARITY_EPIC,
        "hidden": False,
        "requirement_type": "starboard_posts",
        "requirement_value": 10,
        "reward_bounty": 500,
    },

    {
        "key": "viral_post",
        "name": "💫 Viral Pirate",
        "description": "Get 10 stars on one message.",
        "category": CATEGORY_STARBOARD,
        "rarity": RARITY_RARE,
        "hidden": False,
        "requirement_type": "single_star_count",
        "requirement_value": 10,
        "reward_bounty": 500,
    },

    {
        "key": "secret_pirate",
        "name": "☠️ Secret Pirate",
        "description": "You discovered a hidden achievement.",
        "category": CATEGORY_SPECIAL,
        "rarity": RARITY_MYTHICAL,
        "hidden": True,
        "requirement_type": "secret",
        "requirement_value": 1,
        "reward_bounty": 1000,
    },
]