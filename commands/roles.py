import discord
from discord import app_commands
from discord.ext import commands
from config.banners import ROLE_BANNER
from services.role_service import (
    add_role,
    remove_role
)
from services.role_views import RolePanelView


class Roles(
    commands.GroupCog,
    group_name="role",
    group_description="Manage your self-assignable roles."
):

    @app_commands.command(
        name="add",
        description="Add a self-assignable role."
    )
    async def add(
        self,
        interaction: discord.Interaction,
        role: discord.Role
    ):

        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True
            )
            return

        member = interaction.user

        if not isinstance(member, discord.Member):
            await interaction.response.send_message(
                "Could not identify you as a server member.",
                ephemeral=True
            )
            return

        success, message = await add_role(
            member,
            role
        )

        await interaction.response.send_message(
            (
                f"✅ {message}"
                if success
                else f"❌ {message}"
            ),
            ephemeral=True
        )

    @app_commands.command(
        name="remove",
        description="Remove a self-assignable role."
    )
    async def remove(
        self,
        interaction: discord.Interaction,
        role: discord.Role
    ):

        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True
            )
            return

        member = interaction.user

        if not isinstance(member, discord.Member):
            await interaction.response.send_message(
                "Could not identify you as a server member.",
                ephemeral=True
            )
            return

        success, message = await remove_role(
            member,
            role
        )

        await interaction.response.send_message(
            (
                f"✅ {message}"
                if success
                else f"❌ {message}"
            ),
            ephemeral=True
        )

    @app_commands.command(
        name="toggle",
        description="Toggle a self-assignable role."
    )
    async def toggle(
        self,
        interaction: discord.Interaction,
        role: discord.Role
    ):

        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True
            )
            return

        member = interaction.user

        if not isinstance(member, discord.Member):
            await interaction.response.send_message(
                "Could not identify you as a server member.",
                ephemeral=True
            )
            return

        if role in member.roles:
            success, message = await remove_role(
                member,
                role
            )
        else:
            success, message = await add_role(
                member,
                role
            )

        await interaction.response.send_message(
            (
                f"✅ {message}"
                if success
                else f"❌ {message}"
            ),
            ephemeral=True
        )

class RolePanel(
    commands.GroupCog,
    group_name="rolepanel",
    group_description="Manage the Straw Hat role panel."
):

    @app_commands.command(
        name="create",
        description="Create the permanent role selection panel."
    )
    @app_commands.checks.has_permissions(
        manage_guild=True
    )
    async def create(
        self,
        interaction: discord.Interaction
    ):

        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🏴‍☠️ GRAND FLEET — ROLE CENTER",
            description=(
                "Welcome to the **Grand Fleet Role Center**!\n\n"
                "Choose the roles that represent your "
                "games, interests and notification preferences.\n\n"
                "Click a category below to open your "
                "private role selector."
            ),
            color=discord.Color.from_rgb(
                190, 35, 45
            )
        )

        embed.set_image(
            url=ROLE_BANNER
        )

        embed.set_footer(
            text="Straw Hat • Grand Fleet"
        )

        await interaction.channel.send(
            embed=embed,
            view=RolePanelView()
        )

        await interaction.response.send_message(
            "✅ The permanent role panel has been created.",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Roles(bot))
    await bot.add_cog(RolePanel(bot))