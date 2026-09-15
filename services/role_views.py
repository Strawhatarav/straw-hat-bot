import discord

from database.database import get_self_roles
from services.role_service import (
    add_role,
    remove_role
)


CATEGORY_INFO = {
    "games": {
        "name": "🎮 Game Roles",
        "description": "Select the games you play.",
        "emoji": "🎮",
    },
    "interests": {
        "name": "🎵 Interest Roles",
        "description": "Select the interests you enjoy.",
        "emoji": "🎵",
    },
    "notifications": {
        "name": "🔔 Notification Roles",
        "description": "Choose the notifications you want.",
        "emoji": "🔔",
    },
}


class RoleCategoryButton(discord.ui.Button):

    def __init__(
        self,
        category: str
    ):
        info = CATEGORY_INFO[category]

        super().__init__(
            label=info["name"],
            emoji=info["emoji"],
            style=discord.ButtonStyle.secondary,
            custom_id=f"strawhat:role_category:{category}"
        )

        self.category = category

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        if interaction.guild is None:
            await interaction.response.send_message(
                "This can only be used inside a server.",
                ephemeral=True
            )
            return

        role_data = get_self_roles(
            interaction.guild.id,
            self.category
        )

        roles = []

        for role_id, category in role_data:

            role = interaction.guild.get_role(role_id)

            if role is not None:
                roles.append(role)

        if not roles:
            await interaction.response.send_message(
                "No roles have been configured in this category yet.",
                ephemeral=True
            )
            return

        info = CATEGORY_INFO[self.category]

        embed = discord.Embed(
            title=info["name"],
            description=(
                f"{info['description']}\n\n"
                "Select a role below to toggle it."
            ),
            color=discord.Color.from_rgb(
                190, 35, 45
            )
        )

        await interaction.response.send_message(
            embed=embed,
            view=RoleSelectionView(
                roles,
                self.category
            ),
            ephemeral=True
        )

class RolePanelView(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=None
        )

        categories = [
            "games",
            "interests",
            "notifications"
        ]

        for category in categories:

            self.add_item(
                RoleCategoryButton(category)
            )

class RoleSelect(discord.ui.Select):

    def __init__(
        self,
        roles: list[discord.Role],
        category: str
    ):

        options = []

        for role in roles[:25]:

            options.append(
                discord.SelectOption(
                    label=role.name[:100],
                    value=str(role.id),
                    description=(
                        f"Toggle the {role.name} role."
                    )[:100]
                )
            )

        super().__init__(
            placeholder="Select roles...",
            min_values=1,
            max_values=len(options),
            options=options,
            custom_id=f"strawhat:role_select:{category}"
        )

        self.category = category

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        if interaction.guild is None:
            await interaction.response.send_message(
                "This can only be used inside a server.",
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

        results = []

        for value in self.values:

            role = interaction.guild.get_role(
                int(value)
            )

            if role is None:
                results.append(
                    "❌ A configured role no longer exists."
                )
                continue

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

            if success:
                results.append(
                    f"✅ {message}"
                )
            else:
                results.append(
                    f"❌ {message}"
                )

        await interaction.response.send_message(
            "\n".join(results),
            ephemeral=True
        )

class RoleSelectionView(discord.ui.View):

    def __init__(
        self,
        roles: list[discord.Role],
        category: str
    ):

        super().__init__(
            timeout=900
        )

        self.add_item(
            RoleSelect(
                roles,
                category
            )
        )