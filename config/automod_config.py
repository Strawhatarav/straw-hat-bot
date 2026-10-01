# Basic AutoMod defaults.
# AutoMod is disabled until you enable it in the server.

SPAM_MESSAGE_LIMIT = 5
SPAM_WINDOW_SECONDS = 8
SPAM_TIMEOUT_SECONDS = 30

MAX_JOIN_COUNT = 8
RAID_WINDOW_SECONDS = 20

# Add words you want the bot to block.
# Keep this list appropriate for your community.
BLOCKED_WORDS = [
    "example_blocked_word",
]

# Link filtering is intentionally configurable.
# Add trusted domains here if you later want an allowlist.
ALLOWED_LINK_DOMAINS = [
    "discord.com",
    "discord.gg",
]