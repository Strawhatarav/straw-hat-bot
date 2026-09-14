import discord
from discord.ext import commands
from database.database import get_guild_config
from config.banners import (
    WELCOME_BANNER,
    FAREWELL_BANNER,
    WELCOME_THUMBNAIL,
    FAREWELL_THUMBNAIL
)
from views.onboarding import OnboardingView

class MemberEvents(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_member_join(
        self,
        member: discord.Member
    ):
    
        config = get_guild_config(member.guild.id)
    
        if config is None:
            return
    
        (
            guild_id,
            welcome_channel_id,
            goodbye_channel_id,
            default_role_id,
            welcome_message,
            goodbye_message
        ) = config
    
        if default_role_id:
    
            role = member.guild.get_role(
                default_role_id
            )
    
            if role is not None:
    
                try:
                    await member.add_roles(role)
    
                except discord.Forbidden:
    
                    print(
                        f"❌ Cannot assign role "
                        f"{role.name} "
                        f"in {member.guild.name}"
                    )
    
        if not welcome_channel_id:
            return
    
        channel = member.guild.get_channel(welcome_channel_id)

        if channel is None:
            return

        embed = discord.Embed(
            title="🏴‍☠️ Welcome to the Straw Hat Crew!",
            description=(
                f"Welcome {member.mention} to **Straw Hat**! 🎉\n\n"
                "Start your journey by completing the "
                "onboarding steps below."
            )
        )

        embed.set_thumbnail(
            url=WELCOME_THUMBNAIL
        )

        embed.set_image(
            url=WELCOME_BANNER
        )

        embed.set_footer(
            text="Straw Hat • Your adventure starts here"
        )

        await channel.send(
            content=f"🏴‍☠️ Welcome {member.mention}!",
            embed=embed,
            view=OnboardingView()
        )
    
    @commands.Cog.listener()
    async def on_member_remove(
        self,
        member: discord.Member
    ):
    
        config = get_guild_config(member.guild.id)
    
        if config is None:
            return
    
        (
            guild_id,
            welcome_channel_id,
            goodbye_channel_id,
            default_role_id,
            welcome_message,
            goodbye_message
        ) = config
    
        if not goodbye_channel_id:
            return

        channel = member.guild.get_channel(goodbye_channel_id)

        if channel is None:
            return
    
        embed = discord.Embed(
            title="🏴‍☠️ Our Crew Member Has Departed",
            description=(
                f"**{member.name}** has left our crew "
                "to move forward on their own journey.\n\n"
                "We all wish them the very best of luck "
                "on the journey ahead. 🍂🏴‍☠️"
            )
        )
    
        # Custom farewell thumbnail
        embed.set_thumbnail(
            url=FAREWELL_THUMBNAIL
        )
    
        # Custom farewell banner
        embed.set_image(
            url=FAREWELL_BANNER
        )
    
        embed.set_footer(
            text="Straw Hat • Once a crew member, always part of the journey."
        )
    
        await channel.send(
            embed=embed
        )


async def setup(bot):
    await bot.add_cog(MemberEvents(bot))