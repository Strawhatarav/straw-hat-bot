import os

import discord
from discord.ext import commands
from database.database import initialize_database
from views.onboarding import OnboardingView
from services.role_views import RolePanelView

# Load environment variables
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

        self.add_view(OnboardingView())
        
        extensions = [
           "commands.general",
           "commands.utility",
           "commands.configuration",
           "commands.roles",
           "events.ready",
           "events.member_events",
        ]

        for extension in extensions:
            try:
                await self.load_extension(extension)
                print(f"✅ Loaded: {extension}")

            except Exception as error:
                print(f"❌ Failed to load {extension}: {error}")

        guild = discord.Object(id=int(GUILD_ID))
        
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

        # Register the permanent role panel buttons
        self.add_view(
            RolePanelView()
        )
    
        guild = discord.Object(
            id=int(GUILD_ID)
        )
    
        self.tree.copy_global_to(
            guild=guild
        )
    
        await self.tree.sync(
            guild=guild
        )

# Initialize database
initialize_database()

# Create the bot
bot = StrawHatBot()


if not DISCORD_TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN was not found in the .env file."
    )

if not GUILD_ID:
    raise RuntimeError(
        "GUILD_ID was not found in the .env file."
    )

bot.run(DISCORD_TOKEN)