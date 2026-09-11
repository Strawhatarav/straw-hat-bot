import os

import discord
from discord import app_commands
from dotenv import load_dotenv


# Load variables from .env
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")


# Basic Discord intents
intents = discord.Intents.default()

# Create the bot
class StrawHatBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)

        # Command tree stores our slash commands
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # Send our slash commands to Discord
        await self.tree.sync()


bot = StrawHatBot()


@bot.event
async def on_ready():
    print(f"🏴‍☠️ {bot.user} is online!")
    print(f"Bot ID: {bot.user.id}")


@bot.tree.command(name="ping", description="Check if Straw Hat is online.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏴‍☠️ Pong! Straw Hat is online!")


if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN was not found in the .env file.")


bot.run(TOKEN)
