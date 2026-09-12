import discord
from discord.ext import commands


class Ready(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"🏴‍☠️ {self.bot.user} is online!")
        print(f"Bot ID: {self.bot.user.id}")


async def setup(bot):
    await bot.add_cog(Ready(bot))