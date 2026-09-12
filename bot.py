import os

import discord
from discord.ext import commands

# Load environment variables
from config.settings import DISCORD_TOKEN, GUILD_ID

# Discord intents
intents = discord.Intents.default()


# Create the bot
class StrawHatBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents
        )

    async def setup_hook(self):

        extensions = [
           "commands.general",
           "commands.utility",
           "events.ready",
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