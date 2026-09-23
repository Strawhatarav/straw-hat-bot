# ============================================================
# STRAW HAT BOUNTY CONFIGURATION
# ============================================================


# ------------------------------------------------------------
# DEFAULT BOUNTY SETTINGS
# ------------------------------------------------------------

# Minimum Berries a user can receive from an eligible message.
DEFAULT_MIN_BOUNTY = 15

# Maximum Berries a user can receive from an eligible message.
DEFAULT_MAX_BOUNTY = 25

# Number of seconds a user must wait before earning Berries again.
DEFAULT_COOLDOWN = 60


# ------------------------------------------------------------
# INACTIVITY DECAY
# ------------------------------------------------------------

# Number of days a user can remain inactive before
# Bounty decay begins.
DEFAULT_DECAY_GRACE_DAYS = 14

# Percentage of the user's current Bounty removed
# during each decay event.
DEFAULT_DECAY_PERCENT = 5

# Number of days between decay events.
DEFAULT_DECAY_INTERVAL_DAYS = 7

# Maximum Berries that can be removed during one
# decay event.
DEFAULT_MAX_DECAY = 500


# ------------------------------------------------------------
# LEVEL SYSTEM
# ------------------------------------------------------------

# Berries required for a particular level:
#
# Level 1    = 100 Berries
# Level 2    = 400 Berries
# Level 3    = 900 Berries
# Level 4    = 1600 Berries
# Level 5    = 2500 Berries
# Level 10   = 10,000 Berries
#
# Formula:
# Berries = 100 × level²


def bounty_required_for_level(level: int) -> int:
    """
    Calculate the total Berries required to reach a level.

    Example:
        bounty_required_for_level(5)
        → 2500
    """

    return 100 * (level ** 2)


# ------------------------------------------------------------
# LEVEL TITLES
# ------------------------------------------------------------

def get_level_title(level: int) -> str:
    """
    Return the Straw Hat title associated with a level.
    """

    if level >= 1000:
        return "☠️ Legend"

    if level >= 500:
        return "👑 Emperor"

    if level >= 250:
        return "⚡ Yonko Commander"

    if level >= 100:
        return "🔥 Supernova"

    if level >= 50:
        return "🌊 Grand Line Veteran"

    if level >= 25:
        return "🏴‍☠️ Pirate"

    if level >= 10:
        return "⚔️ Crew Member"

    return "🌱 Rookie"


# ------------------------------------------------------------
# RANK PROGRESS DISPLAY
# ------------------------------------------------------------

# Symbol used for completed progress.
PROGRESS_SYMBOL_FILLED = "◆"

# Symbol used for incomplete progress.
PROGRESS_SYMBOL_EMPTY = "◇"

# Number of symbols displayed in the progress bar.
PROGRESS_SYMBOL_COUNT = 10