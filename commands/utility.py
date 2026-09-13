import discord
from discord.ext import commands
from config import emojis
from services.embed_service import (
    create_embed,
    RED,
)

from config.banners import (
    HELP_BANNER,
    SERVERINFO_BANNER,
    USERINFO_BANNER,
)

class HelpSelect(discord.ui.Select):

    def __init__(self):

        options = [
            discord.SelectOption(
                label="General",
                description="General Straw Hat commands",
                emoji="🛠️",
                value="general"
            ),

            discord.SelectOption(
                label="Utility",
                description="Useful information commands",
                emoji="🔧",
                value="utility"
            ),
        ]

        super().__init__(
            placeholder="Select a command category...",
            options=options
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        if self.values[0] == "general":

            embed = create_embed(
                title="🛠️ General Commands",
                description="Basic commands for interacting with Straw Hat.",
                color=RED,
                footer_text="Straw Hat • General",
            )

            embed.add_field(
                name="🏴‍☠️ `/ping`",
                value="Check whether Straw Hat is online.",
                inline=False
            )

            embed.add_field(
                name="👋 `/hello`",
                value="Say hello to Straw Hat.",
                inline=False
            )

        else:

            embed = create_embed(
                title="🔧 Utility Commands",
                description="Useful information and utility commands.",
                color=RED,
                footer_text="Straw Hat • Utility",
            )

            embed.add_field(
                name="📊 `/serverinfo`",
                value="View detailed server information.",
                inline=False
            )

            embed.add_field(
                name="👤 `/userinfo`",
                value="View detailed member information.",
                inline=False
            )

            embed.add_field(
                name="🖼️ `/avatar`",
                value="View a member's avatar.",
                inline=False
            )

            embed.add_field(
                name="🎭 `/roleinfo`",
                value="View information about a role.",
                inline=False
            )

            embed.add_field(
                name="📁 `/channelinfo`",
                value="View information about a channel.",
                inline=False
            )

            embed.add_field(
                name="🏴‍☠️ `/servericon`",
                value="View the server icon.",
                inline=False
            )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

class HelpView(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=180
        )

        self.add_item(
            HelpSelect()
        )

class HelpMenu(discord.ui.View):

    def __init__(self):
        super().__init__()
        self.add_item(HelpSelect())

class Utility(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(
    name="serverinfo",
    description="Show detailed information about this server."
    )
    async def serverinfo(
        self,
        interaction: discord.Interaction
    ):
    
        guild = interaction.guild
    
        if guild is None:
            await interaction.response.send_message(
                "This command can only be used inside a server.",
                ephemeral=True
            )
            return
    
        # MEMBER STATISTICS
    
        total_members = guild.member_count or 0
    
        bot_count = sum(
            1 for member in guild.members
            if member.bot
        )
    
        human_count = total_members - bot_count
    
        # CHANNEL STATISTICS
    
        text_channels = sum(
            1 for channel in guild.channels
            if isinstance(channel, discord.TextChannel)
        )
    
        voice_channels = sum(
            1 for channel in guild.channels
            if isinstance(channel, discord.VoiceChannel)
        )
    
        categories = sum(
            1 for channel in guild.channels
            if isinstance(channel, discord.CategoryChannel)
        )
    
        # OTHER STATISTICS
    
        role_count = len(guild.roles)
    
        emoji_count = len(guild.emojis)
    
        boost_count = guild.premium_subscription_count or 0
    
        boost_level = guild.premium_tier
    
        # OWNER
    
        owner = guild.owner
    
        owner_text = (
            owner.mention
            if owner
            else f"<@{guild.owner_id}>"
            if guild.owner_id
            else "Unknown"
        )
    
        # CREATE EMBED
    
        embed = create_embed(
            title="🏴‍☠️ Server Information",
            description=(
                f"Everything you need to know about **{guild.name}**."
            ),
            color=RED,
            banner_url=SERVERINFO_BANNER,
            thumbnail_url=guild.icon.url if guild.icon else None,
            footer_text=f"Straw Hat • {guild.name}",
        )
    
        # BASIC INFORMATION
    
        embed.add_field(
            name="📛 Server Name",
            value=guild.name,
            inline=True
        )
    
        embed.add_field(
            name="🆔 Server ID",
            value=str(guild.id),
            inline=True
        )
    
        embed.add_field(
            name="👑 Owner",
            value=owner_text,
            inline=True
        )
    
        embed.add_field(
            name="📅 Created",
            value=discord.utils.format_dt(
                guild.created_at,
                style="F"
            ),
            inline=False
        )
    
        # MEMBER STATISTICS
    
        embed.add_field(
            name="👥 Members",
            value=str(total_members),
            inline=True
        )
    
        embed.add_field(
            name="👤 Humans",
            value=str(human_count),
            inline=True
        )
    
        embed.add_field(
            name="🤖 Bots",
            value=str(bot_count),
            inline=True
        )
    
        # CHANNEL STATISTICS
    
        embed.add_field(
            name="📁 Channels",
            value=str(len(guild.channels)),
            inline=True
        )
    
        embed.add_field(
            name="💬 Text",
            value=str(text_channels),
            inline=True
        )
    
        embed.add_field(
            name="🔊 Voice",
            value=str(voice_channels),
            inline=True
        )
    
        embed.add_field(
            name="🗂️ Categories",
            value=str(categories),
            inline=True
        )
    
        # SERVER RESOURCES
    
        embed.add_field(
            name="🎭 Roles",
            value=str(role_count),
            inline=True
        )
    
        embed.add_field(
            name="😀 Emojis",
            value=str(emoji_count),
            inline=True
        )
    
        embed.add_field(
            name="🚀 Boosts",
            value=str(boost_count),
            inline=True
        )
    
        embed.add_field(
            name="⭐ Boost Level",
            value=str(boost_level),
            inline=True
        )
    
        # SERVER BANNER
    
        if guild.banner:
    
            embed.set_image(
                url=guild.banner.url
            )
    
        await interaction.response.send_message(
            embed=embed
        )

    @discord.app_commands.command(
        name="userinfo",
        description="Show detailed information about a server member."
    )
    async def userinfo(
        self,
        interaction: discord.Interaction,
        member: discord.Member
    ):
    
        roles = member.roles[1:]
    
        if roles:
            role_text = " ".join(
                role.mention
                for role in roles[-10:]
            )
        else:
            role_text = "No additional roles"
    
        embed = create_embed(
            title="👤 Member Information",
            description=(
                f"Information about **{member.display_name}**."
            ),
            color=RED,
            banner_url=USERINFO_BANNER,
            thumbnail_url=member.display_avatar.url,
            footer_text=f"Straw Hat • {member.display_name}",
        )
    
        embed.add_field(
            name="📛 Username",
            value=str(member),
            inline=True
        )
    
        embed.add_field(
            name="🆔 User ID",
            value=str(member.id),
            inline=True
        )
    
        embed.add_field(
            name="🤖 Bot",
            value="Yes" if member.bot else "No",
            inline=True
        )
    
        embed.add_field(
            name="📅 Joined Server",
            value=(
                discord.utils.format_dt(
                    member.joined_at,
                    style="F"
                )
                if member.joined_at
                else "Unknown"
            ),
            inline=False
        )
    
        embed.add_field(
            name="🎂 Account Created",
            value=discord.utils.format_dt(
                member.created_at,
                style="F"
            ),
            inline=False
        )
    
        embed.add_field(
            name=f"🎭 Roles ({len(roles)})",
            value=role_text,
            inline=False
        )
    
        await interaction.response.send_message(
            embed=embed
        )

    @discord.app_commands.command(
        name="avatar",
        description="Show a member's avatar."
    )
    async def avatar(
        self,
        interaction: discord.Interaction,
        member: discord.Member
    ):

        embed = discord.Embed(
            title=f"🖼️ {member.display_name}'s Avatar"
        )

        embed.set_image(
            url=member.display_avatar.url
        )

        await interaction.response.send_message(
            embed=embed
        )

    @discord.app_commands.command(
        name="servericon",
        description="Show the server icon."
    )
    async def servericon(
        self,
        interaction: discord.Interaction
    ):

        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message(
                "This command can only be used inside a server.",
                ephemeral=True
            )
            return

        if guild.icon is None:
            await interaction.response.send_message(
                "This server does not have a server icon.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"🏴‍☠️ {guild.name} — Server Icon"
        )

        embed.set_image(
            url=guild.icon.url
        )

        await interaction.response.send_message(
            embed=embed
        )

    @discord.app_commands.command(
        name="roleinfo",
        description="Show information about a role."
    )
    async def roleinfo(
        self,
        interaction: discord.Interaction,
        role: discord.Role
    ):

        embed = discord.Embed(
            title=f"🎭 {role.name}",
            description="Role information"
        )

        embed.add_field(
            name="Role ID",
            value=str(role.id),
            inline=True
        )

        embed.add_field(
            name="Position",
            value=str(role.position),
            inline=True
        )

        embed.add_field(
            name="Members",
            value=str(len(role.members)),
            inline=True
        )

        embed.add_field(
            name="Mention",
            value=role.mention,
            inline=False
        )

        await interaction.response.send_message(
            embed=embed
        )

    @discord.app_commands.command(
        name="channelinfo",
        description="Show information about a text channel."
    )
    async def channelinfo(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):

        embed = discord.Embed(
            title=f"📁 #{channel.name}",
            description="Channel information"
        )

        embed.add_field(
            name="Channel ID",
            value=str(channel.id),
            inline=True
        )

        embed.add_field(
            name="Category",
            value=(
                channel.category.name
                if channel.category
                else "None"
            ),
            inline=True
        )

        embed.add_field(
            name="Position",
            value=str(channel.position),
            inline=True
        )

        embed.add_field(
            name="Created",
            value=discord.utils.format_dt(
                channel.created_at,
                style="F"
            ),
            inline=False
        )

        await interaction.response.send_message(
            embed=embed
        )

    @discord.app_commands.command(
        name="help",
        description="Open the Straw Hat command center."
    )
    async def help(
        self,
        interaction: discord.Interaction
    ):
    
        description = (
            "Welcome to the **Straw Hat command center**.\n\n"
            "Here you can explore the different command "
            "categories available to you.\n\n"
    
            f"> {emojis.GENERAL} **General** :\n"
            "> Basic commands for interacting with Straw Hat.\n\n"
        
            f"> {emojis.UTILITY} **Utility** :\n"
            "> Useful tools for servers, members, channels, and more.\n\n"
        
            f"> 🛡️ **Moderation** :\n"
            "> Commands for managing and protecting the server.\n\n"
        
            f"> ⭐ **Leveling** :\n"
            "> XP, levels, ranks, and achievements.\n\n"
    
            "Use the dropdown menu below to explore "
            "the commands in each category."
        )
    
        embed = create_embed(
            title="🏴‍☠️ Straw Hat Help",
            description=description,
            color=RED,
            banner_url=HELP_BANNER,
            footer_text="Straw Hat • Command Center",
        )
    
        await interaction.response.send_message(
            embed=embed,
            view=HelpView()
        )

async def setup(bot):
    await bot.add_cog(Utility(bot))