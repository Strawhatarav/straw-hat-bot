"""TheSportsDB and RSS sports headlines."""
import xml.etree.ElementTree as ET
from services.api_client import APIError

SPORTSDB = "https://www.thesportsdb.com/api/v1/json/3"


async def search_team(client, query):
    data = await client.get_json(
        f"{SPORTSDB}/searchteams.php", params={"t": query}, cache_ttl=900
    )
    teams = data.get("teams") or []
    if not teams:
        raise APIError("No matching team was found.")
    return teams[:5]


async def team_events(client, team_id, upcoming=False):
    endpoint = "eventsnext.php" if upcoming else "eventslast.php"
    data = await client.get_json(
        f"{SPORTSDB}/{endpoint}", params={"id": team_id}, cache_ttl=300
    )
    events = data.get("events") or []
    if not events:
        raise APIError("No fixtures or recent results were available for that team.")
    return events[:5]


async def sport_news(client, sport):
    # ESPN RSS endpoints are public feeds; availability can vary by sport.
    feeds = {
        "football": "https://www.espn.com/espn/rss/soccer/news",
        "soccer": "https://www.espn.com/espn/rss/soccer/news",
        "basketball": "https://www.espn.com/espn/rss/nba/news",
        "tennis": "https://www.espn.com/espn/rss/tennis/news",
        "cricket": "https://www.espn.com/espn/rss/cricket/news",
        "baseball": "https://www.espn.com/espn/rss/mlb/news",
    }
    url = feeds.get(sport.lower())
    if not url:
        raise APIError("Supported sports: football, soccer, basketball, tennis, cricket, baseball.")
    await client.start()
    try:
        async with client.session.get(url) as response:
            if response.status >= 400:
                raise APIError("The sports news feed is temporarily unavailable.")
            body = await response.text()
        root = ET.fromstring(body)
        items = root.findall(".//item")[:5]
        results = []
        for item in items:
            results.append({
                "title": item.findtext("title", default="Sports headline"),
                "link": item.findtext("link", default=""),
                "description": item.findtext("description", default="")
            })
        if not results:
            raise APIError("No headlines were available right now.")
        return results
    except APIError:
        raise
    except Exception:
        raise APIError("I couldn't read the sports news feed right now.")
