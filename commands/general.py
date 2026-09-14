import discord
from discord.ext import commands


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(
        name="ping",
        description="Check if Straw Hat is online."
    )
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "🏴‍☠️ Pong! Straw Hat is online!",
            ephemeral=True
        )

    @discord.app_commands.command(
        name="hello",
        description="Say hello to Straw Hat."
    )
    async def hello(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "🏴‍☠️ Hello! Straw Hat is here!",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(General(bot))