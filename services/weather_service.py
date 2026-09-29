"""Open-Meteo geocoding and current weather."""
from services.api_client import APIError

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog", 51: "Light drizzle",
    53: "Moderate drizzle", 55: "Dense drizzle", 61: "Slight rain",
    63: "Moderate rain", 65: "Heavy rain", 71: "Slight snow",
    73: "Moderate snow", 75: "Heavy snow", 80: "Rain showers",
    81: "Moderate rain showers", 82: "Violent rain showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with hail"
}


async def get_weather(client, place):
    geo = await client.get_json(
        GEO_URL, params={"name": place, "count": 1, "language": "en", "format": "json"},
        cache_ttl=3600
    )
    locations = geo.get("results", [])
    if not locations:
        raise APIError("I couldn't find that location. Try a city name.")
    loc = locations[0]
    weather = await client.get_json(
        WEATHER_URL,
        params={
            "latitude": loc["latitude"], "longitude": loc["longitude"],
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,wind_speed_10m",
            "timezone": "auto"
        },
        cache_ttl=300
    )
    return loc, weather.get("current", {})
