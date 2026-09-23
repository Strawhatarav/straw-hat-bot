import discord

from discord.ext import commands
from database.database import initialize_database
from views.onboarding import OnboardingView
from services.role_views import RolePanelView
from services import poll_service
from services.poll_views import PollView
from config.settings import DISCORD_TOKEN, GUILD_ID


# Discord intents
intents = discord.Intents.default()
intents.members = True


# Create the bot
class StrawHatBot(commands.Bot):

    def __init__(self):

        super().__init__(
            command_prefix="!",
            intents=intents
        )

    async def setup_hook(self):

        # Register the permanent onboarding buttons
        self.add_view(
            OnboardingView()
        )

        # Load bot extensions
        extensions = [
            "commands.general",
            "commands.utility",
            "commands.configuration",
            "commands.roles",
            "commands.polls",
            "commands.leveling",
            "commands.achievements",
            "commands.starboard"
            "events.ready",
            "events.member_events",
            "events.xp_events",
            "events.achievement_events",
            "events.starboard_events",
        ]

        for extension in extensions:

            try:

                await self.load_extension(
                    extension
                )

                print(
                    f"✅ Loaded: {extension}"
                )

            except Exception as error:

                print(
                    f"❌ Failed to load "
                    f"{extension}: {error}"
                )

        # Register the permanent role panel buttons
        self.add_view(
            RolePanelView()
        )

        # Restore active poll buttons
        active_polls = (
            poll_service.get_active_polls()
        )

        for poll in active_polls:

            if poll["message_id"] is None:
                continue

            self.add_view(
                PollView(
                    poll_id=poll["id"],
                    options=poll["options"],
                    multiple_choice=(
                        poll["multiple_choice"]
                    )
                ),
                message_id=poll["message_id"]
            )

        # Sync slash commands
        guild = discord.Object(
            id=int(GUILD_ID)
        )

        self.tree.copy_global_to(
            guild=guild
        )

        await self.tree.sync(
            guild=guild
        )

        print(
            "✅ Slash commands synced!"
        )


# Initialize database
initialize_database()


# Create the bot
bot = StrawHatBot()


# Check environment variables
if not DISCORD_TOKEN:

    raise RuntimeError(
        "DISCORD_TOKEN was not found "
        "in the .env file."
    )


if not GUILD_ID:

    raise RuntimeError(
        "GUILD_ID was not found "
        "in the .env file."
    )


# Start the bot
bot.run(
    DISCORD_TOKEN
)