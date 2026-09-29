"""Jikan, TMDB and RAWG lookups."""
from services.api_client import APIError

JIKAN = "https://api.jikan.moe/v4"
TMDB = "https://api.themoviedb.org/3"
RAWG = "https://api.rawg.io/api"


async def jikan_search(client, kind, query):
    data = await client.get_json(
        f"{JIKAN}/{kind}", params={"q": query, "limit": 5},
        cache_ttl=600
    )
    results = data.get("data", [])
    if not results:
        raise APIError("No matching results were found.")
    return results


async def tmdb_search(client, kind, query, api_key):
    if not api_key:
        raise APIError("TMDB_API_KEY is not configured in your .env file.")
    data = await client.get_json(
        f"{TMDB}/search/{kind}",
        params={"api_key": api_key, "query": query, "include_adult": "false"},
        cache_ttl=600
    )
    results = data.get("results", [])
    if not results:
        raise APIError("No matching results were found.")
    return results


async def rawg_search(client, query, api_key):
    if not api_key:
        raise APIError("RAWG_API_KEY is not configured in your .env file.")
    data = await client.get_json(
        f"{RAWG}/games",
        params={"key": api_key, "search": query, "page_size": 5},
        cache_ttl=600
    )
    results = data.get("results", [])
    if not results:
        raise APIError("No matching games were found.")
    return results
