import discord

from database import giveaway_db
from services.giveaway_service import add_entry


class GiveawayView(discord.ui.View):
    def __init__(self, giveaway_id: int):
        super().__init__(timeout=None)

        self.giveaway_id = giveaway_id

        button = discord.ui.Button(
            label="Enter Giveaway",
            emoji="🎉",
            style=discord.ButtonStyle.danger,
            custom_id=f"strawhat:giveaway_enter:{giveaway_id}",
        )

        button.callback = self.enter_callback

        self.add_item(button)

    async def enter_callback(
        self,
        interaction: discord.Interaction,
    ):
        giveaway = giveaway_db.get_active_giveaway(
            self.giveaway_id
        )

        if not giveaway:
            embed = discord.Embed(
                title="⏰ GIVEAWAY ENDED",
                description=(
                    "This giveaway is no longer accepting entries.\n\n"
                    "> 🏆 The treasure has already been claimed."
                ),
                color=discord.Color.from_rgb(
                    220,
                    38,
                    38,
                ),
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True,
            )

            return

        added = add_entry(
            self.giveaway_id,
            interaction.user.id,
        )

        if not added:
            embed = discord.Embed(
                title="ℹ️ ALREADY ENTERED",
                description=(
                    "You're already part of this giveaway!\n\n"
                    "> 🎉 One entry is enough, pirate.\n"
                    "> Now sit back and wait for the treasure! 🏴‍☠️"
                ),
                color=discord.Color.from_rgb(
                    220,
                    38,
                    38,
                ),
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True,
            )

            return

        embed = discord.Embed(
            title="🎉 GIVEAWAY ENTRY",
            description=(
                "You have successfully entered!\n\n"
                "> 🏴‍☠️ Your name has been added to the "
                "crew of contestants."
            ),
            color=discord.Color.from_rgb(
                220,
                38,
                38,
            ),
        )

        embed.add_field(
            name="🎁 Prize",
            value=giveaway[4],
            inline=False,
        )

        embed.add_field(
            name="🏆 Winners",
            value=str(giveaway[6]),
            inline=True,
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
        )

class DisabledGiveawayView(discord.ui.View):
    def __init__(self, label: str):
        super().__init__(timeout=None)

        button = discord.ui.Button(
            label=label,
            emoji="🏆",
            style=discord.ButtonStyle.secondary,
            disabled=True,
            custom_id=f"strawhat:giveaway_disabled:{label}",
        )

        self.add_item(button)

