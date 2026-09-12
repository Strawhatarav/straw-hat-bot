import discord
from discord.ext import commands


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(
        name="about",
        description="Show information about Straw Hat."
    )
    async def about(self, interaction: discord.Interaction):

        await interaction.response.send_message(
            "🏴‍☠️ **Straw Hat Bot**\n"
            "A custom Discord bot built with Python."
        )


async def setup(bot):
    await bot.add_cog(Utility(bot))