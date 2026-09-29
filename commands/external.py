import os
import time
import discord
from discord import app_commands
from discord.ext import commands

from services.api_client import APIClient, APIError
from services.search_service import search_wikipedia
from services.media_service import jikan_search, tmdb_search, rawg_search
from services.weather_service import get_weather, WEATHER_CODES
from services.sports_service import search_team, team_events, sport_news
from services.embed_service import create_embed, create_warning_embed
from config.settings import TMDB_API_KEY, RAWG_API_KEY


def clean(value, limit=900):
    if not value:
        return "Not available"
    return str(value).replace("@", "@\u200b")[:limit]


class External(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = APIClient()
        self.cooldowns = {}

    async def cog_unload(self):
        await self.api.close()

    async def send_error(self, interaction, error):
        embed = create_warning_embed("⚠️ External service", str(error))
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)

    async def before_call(self, interaction):
        user_id = interaction.user.id
        current_time = time.monotonic()
    
        last_used = self.cooldowns.get(user_id)
    
        if last_used is not None:
            elapsed = current_time - last_used
    
            if elapsed < 4:
                remaining = 4 - elapsed
    
                await self.send_error(
                    interaction,
                    APIError(
                        f"Please wait {remaining:.1f} seconds "
                        "before using another external command."
                    )
                )
                return False
    
        self.cooldowns[user_id] = current_time
    
        await interaction.response.defer(
            thinking=True,
            ephemeral=True
        )
    
        return True

    async def finish(self, interaction, embed):
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="search", description="Search Wikipedia for a topic")
    @app_commands.describe(query="What would you like to search for?")
    async def search(self, interaction: discord.Interaction, query: str):
        if not await self.before_call(interaction): return
        try:
            rows = await search_wikipedia(self.api, query[:150])
            embed = create_embed("🔎 Wikipedia Search", f"Results for **{clean(query, 150)}**")
            for row in rows[:5]:
                title = clean(row.get("title"), 200)
                url = "https://en.wikipedia.org/?curid=" + str(row.get("pageid", ""))
                snippet = clean(row.get("snippet", "").replace("<span class=\"searchmatch\">", "").replace("</span>", ""), 500)
                embed.add_field(name=f"📚 {title}", value=f"{snippet}\n[Read article]({url})", inline=False)
            await self.finish(interaction, embed)
        except APIError as e: await self.send_error(interaction, e)

    @app_commands.command(name="anime", description="Search for anime")
    async def anime(self, interaction: discord.Interaction, query: str):
        if not await self.before_call(interaction): return
        try:
            rows = await jikan_search(self.api, "anime", query[:100])
            row = rows[0]
            title = row.get("title") or "Anime"
            url = row.get("url")
            embed = create_embed(f"🍥 {clean(title, 250)}", clean(row.get("synopsis"), 900),
                                 thumbnail_url=(row.get("images", {}).get("jpg", {}).get("image_url")))
            embed.add_field(name="📺 Episodes", value=str(row.get("episodes") or "Unknown"))
            embed.add_field(name="⭐ Score", value=str(row.get("score") or "Not rated"))
            embed.add_field(name="📅 Status", value=clean(row.get("status")))
            if url: embed.add_field(name="🔗 More information", value=f"[MyAnimeList]({url})", inline=False)
            await self.finish(interaction, embed)
        except APIError as e: await self.send_error(interaction, e)

    @app_commands.command(name="manga", description="Search for manga")
    async def manga(self, interaction: discord.Interaction, query: str):
        if not await self.before_call(interaction): return
        try:
            rows = await jikan_search(self.api, "manga", query[:100])
            row = rows[0]
            embed = create_embed(f"📖 {clean(row.get('title'), 250)}", clean(row.get("synopsis"), 900),
                                 thumbnail_url=row.get("images", {}).get("jpg", {}).get("image_url"))
            embed.add_field(name="📚 Chapters", value=str(row.get("chapters") or "Unknown"))
            embed.add_field(name="📦 Volumes", value=str(row.get("volumes") or "Unknown"))
            embed.add_field(name="⭐ Score", value=str(row.get("score") or "Not rated"))
            if row.get("url"): embed.add_field(name="🔗 More information", value=f"[MyAnimeList]({row['url']})", inline=False)
            await self.finish(interaction, embed)
        except APIError as e: await self.send_error(interaction, e)

    @app_commands.command(name="character", description="Search for an anime or manga character")
    async def character(self, interaction: discord.Interaction, query: str):
        if not await self.before_call(interaction): return
        try:
            rows = await jikan_search(self.api, "characters", query[:100])
            row = rows[0]
            about = row.get("about") or "No character biography is available."
            embed = create_embed(f"🧑 {clean(row.get('name'), 250)}", clean(about, 1500),
                                 thumbnail_url=row.get("images", {}).get("jpg", {}).get("image_url"))
            if row.get("url"): embed.add_field(name="🔗 More information", value=f"[MyAnimeList]({row['url']})")
            await self.finish(interaction, embed)
        except APIError as e: await self.send_error(interaction, e)

    @app_commands.command(name="movie", description="Search for a movie")
    async def movie(self, interaction: discord.Interaction, query: str):
        if not await self.before_call(interaction): return
        try:
            rows = await tmdb_search(self.api, "movie", query[:100], TMDB_API_KEY)
            row = rows[0]
            title = row.get("title") or "Movie"
            poster = row.get("poster_path")
            embed = create_embed(f"🎬 {clean(title, 250)}", clean(row.get("overview"), 900),
                                 thumbnail_url=f"https://image.tmdb.org/t/p/w500{poster}" if poster else None)
            embed.add_field(name="📅 Release date", value=clean(row.get("release_date")))
            embed.add_field(name="⭐ Rating", value=str(row.get("vote_average") or "Not rated"))
            embed.add_field(name="🔗 TMDB", value=f"[Open movie](https://www.themoviedb.org/movie/{row['id']})", inline=False)
            await self.finish(interaction, embed)
        except APIError as e: await self.send_error(interaction, e)

    @app_commands.command(name="series", description="Search for a TV series")
    async def series(self, interaction: discord.Interaction, query: str):
        if not await self.before_call(interaction): return
        try:
            rows = await tmdb_search(self.api, "tv", query[:100], TMDB_API_KEY)
            row = rows[0]
            title = row.get("name") or "Series"
            poster = row.get("poster_path")
            embed = create_embed(f"📺 {clean(title, 250)}", clean(row.get("overview"), 900),
                                 thumbnail_url=f"https://image.tmdb.org/t/p/w500{poster}" if poster else None)
            embed.add_field(name="📅 First aired", value=clean(row.get("first_air_date")))
            embed.add_field(name="⭐ Rating", value=str(row.get("vote_average") or "Not rated"))
            embed.add_field(name="🔗 TMDB", value=f"[Open series](https://www.themoviedb.org/tv/{row['id']})", inline=False)
            await self.finish(interaction, embed)
        except APIError as e: await self.send_error(interaction, e)

    @app_commands.command(name="game", description="Search for a video game")
    async def game(self, interaction: discord.Interaction, query: str):
        if not await self.before_call(interaction): return
        try:
            rows = await rawg_search(self.api, query[:100], RAWG_API_KEY)
            row = rows[0]
            embed = create_embed(f"🎮 {clean(row.get('name'), 250)}",
                                 f"Released: {clean(row.get('released'))}\nRating: {row.get('rating', 'Not rated')}",
                                 thumbnail_url=row.get("background_image"))
            embed.add_field(name="🔗 RAWG", value=f"[View game](https://rawg.io/games/{row.get('slug')})", inline=False)
            await self.finish(interaction, embed)
        except APIError as e: await self.send_error(interaction, e)

    @app_commands.command(name="weather", description="Get current weather for a city")
    async def weather(self, interaction: discord.Interaction, city: str):
        if not await self.before_call(interaction): return
        try:
            loc, current = await get_weather(self.api, city[:100])
            code = current.get("weather_code")
            desc = WEATHER_CODES.get(code, "Weather conditions unavailable")
            embed = create_embed(f"🌤️ Weather in {clean(loc.get('name'))}",
                f"**{desc}**\n\n🌡️ Temperature: **{current.get('temperature_2m', 'N/A')}°C**\n"
                f"🤗 Feels like: **{current.get('apparent_temperature', 'N/A')}°C**\n"
                f"💧 Humidity: **{current.get('relative_humidity_2m', 'N/A')}%**\n"
                f"💨 Wind: **{current.get('wind_speed_10m', 'N/A')} km/h**\n"
                f"🌧️ Precipitation: **{current.get('precipitation', 'N/A')} mm**")
            embed.set_footer(text=f"Straw Hat • Weather • {clean(loc.get('country'))}")
            await self.finish(interaction, embed)
        except APIError as e: await self.send_error(interaction, e)

    @app_commands.command(name="sport", description="Find a sports team")
    async def sport(self, interaction: discord.Interaction, team: str):
        if not await self.before_call(interaction): return
        try:
            rows = await search_team(self.api, team[:100])
            embed = create_embed(f"🏟️ Teams matching {clean(team, 100)}")
            for row in rows:
                embed.add_field(name=clean(row.get("strTeam"), 200),
                    value=f"Sport: {clean(row.get('strSport'))}\nLeague: {clean(row.get('strLeague'))}\n"
                          f"[Team details](https://www.thesportsdb.com/team/{row.get('idTeam')})",
                    inline=False)
            await self.finish(interaction, embed)
        except APIError as e: await self.send_error(interaction, e)

    @app_commands.command(name="sportsnews", description="Get sports headlines")
    @app_commands.describe(sport="football, soccer, basketball, tennis, cricket, or baseball")
    async def sportsnews(self, interaction: discord.Interaction, sport: str):
        if not await self.before_call(interaction): return
        try:
            rows = await sport_news(self.api, sport[:30])
            embed = create_embed(f"📰 {clean(sport.title(), 50)} Sports News")
            for row in rows:
                title = clean(row["title"], 250)
                value = clean(row["description"], 400)
                if row["link"]: value += f"\n[Read more]({row['link']})"
                embed.add_field(name=f"🏆 {title}", value=value or "Open the article for details.", inline=False)
            await self.finish(interaction, embed)
        except APIError as e: await self.send_error(interaction, e)

    async def _events_command(self, interaction, team, upcoming):
        if not await self.before_call(interaction): return
        try:
            teams = await search_team(self.api, team[:100])
            events = await team_events(self.api, teams[0]["idTeam"], upcoming)
            label = "Upcoming Fixtures" if upcoming else "Recent Results"
            embed = create_embed(f"🏟️ {label}: {clean(teams[0].get('strTeam'), 150)}")
            for event in events:
                home = event.get("strHomeTeam") or "TBD"
                away = event.get("strAwayTeam") or "TBD"
                score = ""
                if not upcoming and (event.get("intHomeScore") is not None or event.get("intAwayScore") is not None):
                    score = f"\n**Score:** {event.get('intHomeScore', '?')} – {event.get('intAwayScore', '?')}"
                embed.add_field(name=f"⚽ {clean(home, 100)} vs {clean(away, 100)}",
                    value=f"📅 {clean(event.get('dateEvent'))} {clean(event.get('strTime'))}{score}",
                    inline=False)
            await self.finish(interaction, embed)
        except APIError as e: await self.send_error(interaction, e)

    @app_commands.command(name="scores", description="Show recent results for a team")
    async def scores(self, interaction: discord.Interaction, team: str):
        await self._events_command(interaction, team, False)

    @app_commands.command(name="fixtures", description="Show upcoming fixtures for a team")
    async def fixtures(self, interaction: discord.Interaction, team: str):
        await self._events_command(interaction, team, True)


async def setup(bot):
    await bot.add_cog(External(bot))
