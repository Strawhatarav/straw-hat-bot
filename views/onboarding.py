import discord


class OnboardingView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🚀 Start Onboarding",
        style=discord.ButtonStyle.primary,
        custom_id="strawhat:start_onboarding"
    )
    async def start_onboarding(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        embed = discord.Embed(
            title="🏴‍☠️ Welcome to the Straw Hat Crew!",
            description=(
                "Before you begin your journey, there are a few "
                "things we'd recommend doing first.\n\n"

                "📜 **1. Read the Rules**\n"
                "Make sure you understand the rules that keep "
                "our crew friendly and enjoyable.\n\n"

                "🎭 **2. Choose Your Roles**\n"
                "Select the games, anime, manga, music and other "
                "interests you're interested in.\n\n"

                "👋 **3. Introduce Yourself**\n"
                "Tell the crew a little about yourself in the "
                "introduction channel.\n\n"

                "🗺️ **4. Explore the Server**\n"
                "Take a look around and discover everything "
                "the Straw Hat crew has to offer.\n\n"

                "Once you're done, you're ready to set sail! "
                "🏴‍☠️"
            )
        )

        embed.set_footer(
            text="Straw Hat • Your journey starts here"
        )

        view = discord.ui.View(timeout=180)

        rules_button = discord.ui.Button(
            label="📜 Rules",
            style=discord.ButtonStyle.link,
            url="https://discord.com/channels/1537110229081133197/1542190944265306163"
        )

        roles_button = discord.ui.Button(
            label="🎭 Roles",
            style=discord.ButtonStyle.link,
            url="https://discord.com/channels/1537110229081133197/1542191043829563414"
        )

        introduction_button = discord.ui.Button(
            label="👋 Introductions",
            style=discord.ButtonStyle.link,
            url="https://discord.com/channels/1537110229081133197/1548966911511891968"
        )

        guide_button = discord.ui.Button(
            label="🗺️ Server Guide",
            style=discord.ButtonStyle.link,
            url="https://discord.com/channels/1537110229081133197/1548967022300233829"
        )

        view.add_item(rules_button)
        view.add_item(roles_button)
        view.add_item(introduction_button)
        view.add_item(guide_button)

        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True
        )

