import discord

from services import poll_service


RED = discord.Color.from_rgb(
    190,
    35,
    45
)


def build_results_embed(
    poll: dict
) -> discord.Embed:

    options = poll["options"]

    counts = poll_service.get_vote_counts(
        poll["id"],
        len(options)
    )

    total_votes = sum(counts)

    embed = discord.Embed(
        title="📊 Poll Results",
        description=f"**{poll['question']}**",
        color=RED
    )

    for index, option in enumerate(options):

        count = counts[index]

        percentage = (
            count / total_votes * 100
            if total_votes > 0
            else 0
        )

        bar_length = 10

        filled = (
            round(
                percentage / 100 * bar_length
            )
            if total_votes > 0
            else 0
        )

        bar = (
            "█" * filled
            + "░" * (bar_length - filled)
        )

        embed.add_field(
            name=option,
            value=(
                f"{bar} "
                f"**{percentage:.1f}%** "
                f"({count} votes)"
            ),
            inline=False
        )

    embed.set_footer(
        text=(
            f"Straw Hat • "
            f"{total_votes} total vote(s)"
        )
    )

    return embed


class PollOptionButton(
    discord.ui.Button
):

    def __init__(
        self,
        poll_id: int,
        option_index: int,
        label: str,
        row: int
    ):

        super().__init__(
            label=label[:80],
            style=discord.ButtonStyle.primary,
            custom_id=(
                f"strawhat:poll:"
                f"{poll_id}:option:"
                f"{option_index}"
            ),
            row=row
        )

        self.poll_id = poll_id
        self.option_index = option_index

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        poll = poll_service.get_poll(
            self.poll_id
        )

        if poll is None:

            await interaction.response.send_message(
                "❌ This poll no longer exists.",
                ephemeral=True
            )

            return

        if poll["closed"]:

            await interaction.response.send_message(
                "🔒 This poll is already closed.",
                ephemeral=True
            )

            return

        if (
            self.option_index
            >= len(poll["options"])
        ):

            await interaction.response.send_message(
                "❌ This poll option is invalid.",
                ephemeral=True
            )

            return

        user_id = interaction.user.id

        current_votes = (
            poll_service.get_user_votes(
                self.poll_id,
                user_id
            )
        )

        if poll["multiple_choice"]:

            if self.option_index in current_votes:

                poll_service.remove_vote(
                    self.poll_id,
                    user_id,
                    self.option_index
                )

                message = (
                    "↩️ Your vote was removed."
                )

            else:

                poll_service.add_vote(
                    self.poll_id,
                    user_id,
                    self.option_index
                )

                message = (
                    "✅ Your vote was recorded."
                )

        else:

            poll_service.clear_user_votes(
                self.poll_id,
                user_id
            )

            poll_service.add_vote(
                self.poll_id,
                user_id,
                self.option_index
            )

            message = (
                "✅ Your vote was recorded."
            )

        await interaction.response.send_message(
            message,
            ephemeral=True
        )


class PollResultsButton(
    discord.ui.Button
):

    def __init__(
        self,
        poll_id: int
    ):

        super().__init__(
            label="Results",
            emoji="📊",
            style=discord.ButtonStyle.secondary,
            custom_id=(
                f"strawhat:poll:"
                f"{poll_id}:results"
            ),
            row=4
        )

        self.poll_id = poll_id

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        poll = poll_service.get_poll(
            self.poll_id
        )

        if poll is None:

            await interaction.response.send_message(
                "❌ Poll not found.",
                ephemeral=True
            )

            return

        embed = build_results_embed(
            poll
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


class PollCloseButton(
    discord.ui.Button
):

    def __init__(
        self,
        poll_id: int
    ):

        super().__init__(
            label="Close",
            emoji="🔒",
            style=discord.ButtonStyle.danger,
            custom_id=(
                f"strawhat:poll:"
                f"{poll_id}:close"
            ),
            row=4
        )

        self.poll_id = poll_id

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        poll = poll_service.get_poll(
            self.poll_id
        )

        if poll is None:

            await interaction.response.send_message(
                "❌ Poll not found.",
                ephemeral=True
            )

            return

        if poll["closed"]:

            await interaction.response.send_message(
                "🔒 This poll is already closed.",
                ephemeral=True
            )

            return

        is_creator = (
            interaction.user.id
            == poll["creator_id"]
        )

        can_manage = (
            interaction.guild is not None
            and interaction.user.guild_permissions.manage_guild
        )

        if not (is_creator or can_manage):

            await interaction.response.send_message(
                "❌ Only the poll creator or a "
                "member with Manage Server permission "
                "can close this poll.",
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            "⚠️ Are you sure you want to close this poll?",
            view=PollCloseConfirmationView(
                self.poll_id
            ),
            ephemeral=True
        )


class PollCloseConfirmationView(
    discord.ui.View
):

    def __init__(
        self,
        poll_id: int
    ):

        super().__init__(
            timeout=30
        )

        self.poll_id = poll_id

    @discord.ui.button(
        label="Close poll",
        emoji="🔒",
        style=discord.ButtonStyle.danger
    )
    async def confirm(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        poll = poll_service.get_poll(
            self.poll_id
        )

        if poll is None:

            await interaction.response.edit_message(
                content="❌ Poll not found.",
                view=None
            )

            return

        is_creator = (
            interaction.user.id
            == poll["creator_id"]
        )

        can_manage = (
            interaction.guild is not None
            and interaction.user.guild_permissions.manage_guild
        )

        if not (is_creator or can_manage):

            await interaction.response.edit_message(
                content="❌ You cannot close this poll.",
                view=None
            )

            return

        poll_service.close_poll(
            self.poll_id
        )

        await interaction.response.edit_message(
            content="✅ The poll has been closed.",
            view=None
        )

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.secondary
    )
    async def cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.edit_message(
            content="↩️ Poll closing cancelled.",
            view=None
        )


class PollSelect(
    discord.ui.Select
):

    def __init__(
        self,
        poll_id: int,
        options: list[str],
        multiple_choice: bool
    ):

        select_options = []

        for index, option in enumerate(options):

            select_options.append(
                discord.SelectOption(
                    label=option[:100],
                    value=str(index),
                    description=(
                        f"Vote for {option}"
                    )[:100]
                )
            )

        super().__init__(
            placeholder="Select your answer...",
            min_values=(
                1
            ),
            max_values=(
                len(select_options)
                if multiple_choice
                else 1
            ),
            options=select_options,
            custom_id=(
                f"strawhat:poll:"
                f"{poll_id}:select"
            ),
            row=3
        )

        self.poll_id = poll_id
        self.multiple_choice = multiple_choice

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        poll = poll_service.get_poll(
            self.poll_id
        )

        if poll is None:

            await interaction.response.send_message(
                "❌ Poll not found.",
                ephemeral=True
            )

            return

        if poll["closed"]:

            await interaction.response.send_message(
                "🔒 This poll is already closed.",
                ephemeral=True
            )

            return

        selected = [
            int(value)
            for value in self.values
        ]

        user_id = interaction.user.id

        if self.multiple_choice:

            current_votes = (
                poll_service.get_user_votes(
                    self.poll_id,
                    user_id
                )
            )

            for option_index in current_votes:

                if option_index not in selected:

                    poll_service.remove_vote(
                        self.poll_id,
                        user_id,
                        option_index
                    )

            for option_index in selected:

                if option_index not in current_votes:

                    poll_service.add_vote(
                        self.poll_id,
                        user_id,
                        option_index
                    )

        else:

            poll_service.clear_user_votes(
                self.poll_id,
                user_id
            )

            poll_service.add_vote(
                self.poll_id,
                user_id,
                selected[0]
            )

        await interaction.response.send_message(
            "✅ Your poll selection has been recorded.",
            ephemeral=True
        )


class PollView(
    discord.ui.View
):

    def __init__(
        self,
        poll_id: int,
        options: list[str],
        multiple_choice: bool
    ):

        super().__init__(
            timeout=None
        )

        for index, option in enumerate(options):

            row = index // 5

            self.add_item(
                PollOptionButton(
                    poll_id,
                    index,
                    option,
                    row
                )
            )

        self.add_item(
            PollSelect(
                poll_id,
                options,
                multiple_choice
            )
        )

        self.add_item(
            PollResultsButton(
                poll_id
            )
        )

        self.add_item(
            PollCloseButton(
                poll_id
            )
        )