"""Wikipedia search service."""
from services.api_client import APIError

WIKI_API = "https://en.wikipedia.org/w/api.php"


async def search_wikipedia(client, query):
    data = await client.get_json(
        WIKI_API,
        params={
            "action": "query", "list": "search", "srsearch": query,
            "format": "json", "utf8": 1, "srlimit": 5
        },
        cache_ttl=600,
    )
    results = data.get("query", {}).get("search", [])
    if not results:
        raise APIError("No Wikipedia results were found.")
    return results