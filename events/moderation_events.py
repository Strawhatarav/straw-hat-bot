from collections import defaultdict, deque
from time import monotonic
import re

import discord
from discord.ext import commands

from database.moderation_db import get_config
from config.automod_config import (
    SPAM_MESSAGE_LIMIT,
    SPAM_WINDOW_SECONDS,
    SPAM_TIMEOUT_SECONDS,
    MAX_JOIN_COUNT,
    RAID_WINDOW_SECONDS,
    BLOCKED_WORDS,
    ALLOWED_LINK_DOMAINS,
)
from services.moderation_service import send_log


class ModerationEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.recent_messages = defaultdict(deque)
        self.recent_joins = defaultdict(deque)

    async def automod_notice(self, message, reason):
        try:
            await message.delete()
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            pass

        try:
            await message.channel.send(
                f"⚠️ {message.author.mention}, your message was removed: {reason}",
                delete_after=8,
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except (discord.Forbidden, discord.HTTPException):
            pass

        await send_log(
            message.guild,
            "automod",
            message.author,
            self.bot.user,
            reason,
            automod=True,
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None or message.author.bot:
            return

        config = get_config(message.guild.id)

        if not config["automod_enabled"]:
            return

        # Do not run content filters in the restricted channel.
        if message.channel.id == config["impel_town_channel_id"]:
            return

        # Spam: repeated messages in a short window.
        if config["spam_enabled"]:
            now = monotonic()
            key = (message.guild.id, message.author.id)
            timestamps = self.recent_messages[key]

            while timestamps and now - timestamps[0] > SPAM_WINDOW_SECONDS:
                timestamps.popleft()

            timestamps.append(now)

            if len(timestamps) >= SPAM_MESSAGE_LIMIT:
                timestamps.clear()
                await self.automod_notice(
                    message,
                    "Repeated messages detected.",
                )

                member = message.author
                if isinstance(member, discord.Member):
                    try:
                        await member.timeout(
                            discord.utils.utcnow()
                            + __import__("datetime").timedelta(
                                seconds=SPAM_TIMEOUT_SECONDS
                            ),
                            reason="Automatic spam protection",
                        )
                    except (discord.Forbidden, discord.HTTPException):
                        pass
                return

        # Link filtering.
        if config["links_enabled"]:
            urls = re.findall(
                r"(?:https?://|www\.)[^\s<>]+",
                message.content,
                flags=re.IGNORECASE,
            )

            for url in urls:
                domain = url.lower().split("://")[-1].split("/")[0]
                domain = domain.removeprefix("www.")

                if not any(
                    domain == allowed or domain.endswith("." + allowed)
                    for allowed in ALLOWED_LINK_DOMAINS
                ):
                    await self.automod_notice(
                        message,
                        "Links from this domain are not allowed.",
                    )
                    return

        # Blocked words.
        if config["bad_words_enabled"]:
            content = message.content.casefold()

            if any(
                re.search(
                    r"(?<!\w)" + re.escape(word.casefold()) + r"(?!\w)",
                    content,
                )
                for word in BLOCKED_WORDS
                if word.strip()
            ):
                await self.automod_notice(
                    message,
                    "Your message contains a blocked word.",
                )
                return

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.guild is None or before.author.bot:
            return

        if before.content == after.content:
            return

        config = get_config(before.guild.id)
        channel_id = config["mod_log_channel_id"]

        if not channel_id:
            return

        channel = before.guild.get_channel(channel_id)
        if channel is None:
            return

        embed = discord.Embed(
            title="✏️ Message edited",
            color=discord.Color.from_rgb(220, 38, 38),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(
            name="Member",
            value=f"{before.author.mention} (`{before.author.id}`)",
            inline=False,
        )
        embed.add_field(
            name="Channel",
            value=before.channel.mention,
            inline=False,
        )
        embed.add_field(
            name="Before",
            value=(before.content[:1000] or "[No text]"),
            inline=False,
        )
        embed.add_field(
            name="After",
            value=(after.content[:1000] or "[No text]"),
            inline=False,
        )

        try:
            await channel.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException):
            pass

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.guild is None or message.author.bot:
            return

        config = get_config(message.guild.id)
        channel_id = config["mod_log_channel_id"]

        if not channel_id:
            return

        channel = message.guild.get_channel(channel_id)
        if channel is None:
            return

        embed = discord.Embed(
            title="🗑️ Message deleted",
            color=discord.Color.from_rgb(220, 38, 38),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(
            name="Member",
            value=f"{message.author.mention} (`{message.author.id}`)",
            inline=False,
        )
        embed.add_field(
            name="Channel",
            value=message.channel.mention,
            inline=False,
        )
        embed.add_field(
            name="Content",
            value=message.content[:1000] or "[Content unavailable]",
            inline=False,
        )
        embed.set_footer(
            text="The bot may not know who deleted this message."
        )

        try:
            await channel.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException):
            pass

    @commands.Cog.listener()
    async def on_member_join(self, member):
        config = get_config(member.guild.id)

        if not config["automod_enabled"] or not config["raid_enabled"]:
            return

        now = monotonic()
        joins = self.recent_joins[member.guild.id]

        while joins and now - joins[0] > RAID_WINDOW_SECONDS:
            joins.popleft()

        joins.append(now)

        if len(joins) >= MAX_JOIN_COUNT:
            await send_log(
                member.guild,
                "raid alert",
                member,
                self.bot.user,
                (
                    f"{len(joins)} members joined within "
                    f"{RAID_WINDOW_SECONDS} seconds. "
                    "Review the server manually."
                ),
                automod=True,
            )


async def setup(bot):
    await bot.add_cog(ModerationEvents(bot))

