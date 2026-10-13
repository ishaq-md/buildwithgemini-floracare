"""Live weather and microclimate tool for FloraCare using Open-Meteo API."""

import json
import os
import urllib.parse
import urllib.request
from typing import Any, Dict

WMO_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
}


def get_live_weather(location: str) -> Dict[str, Any]:
    """Fetches real-time weather, temperature, humidity, and plant advisory for a location using Open-Meteo API.

    Args:
        location: City or region name (e.g. 'San Francisco', 'New York', 'Miami', 'London').

    Returns:
        Dictionary containing real temperature in Fahrenheit, relative humidity percentage,
        forecast high/low, conditions, and plant environmental guidance.
    """
    api_key = os.getenv("WEATHER_API_KEY", "")

    # 1. Geocode location
    geo_query = urllib.parse.urlencode({"name": location.strip(), "count": 1})
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?{geo_query}"

    req = urllib.request.Request(geo_url, headers={"User-Agent": "FloraCare/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            geo_data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": f"Failed to geocode location '{location}': {e}"}

    results = geo_data.get("results")
    if not results:
        return {"error": f"Location '{location}' not found."}

    loc_info = results[0]
    lat = loc_info["latitude"]
    lon = loc_info["longitude"]
    loc_name = loc_info.get("name", location)
    admin1 = loc_info.get("admin1", "")
    country = loc_info.get("country", "")

    # 2. Fetch live forecast
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min",
        "temperature_unit": "fahrenheit",
        "timezone": "auto",
    }
    if api_key:
        params["apikey"] = api_key

    forecast_url = (
        f"https://api.open-meteo.com/v1/forecast?{urllib.parse.urlencode(params)}"
    )
    req = urllib.request.Request(
        forecast_url, headers={"User-Agent": "FloraCare/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": f"Failed to fetch live weather for '{location}': {e}"}

    current = data.get("current", {})
    temp = current.get("temperature_2m")
    humidity = current.get("relative_humidity_2m")
    wmo = current.get("weather_code", 0)
    conditions = WMO_CODES.get(wmo, "Clear")

    daily = data.get("daily", {})
    highs = daily.get("temperature_2m_max", [])
    lows = daily.get("temperature_2m_min", [])
    today_high = highs[0] if highs else None
    today_low = lows[0] if lows else None

    advisory = []
    if today_low is not None and today_low < 50:
        advisory.append(
            f"Cold warning: Overnight low of {today_low}°F. Bring delicate houseplants inside."
        )
    if humidity is not None and humidity < 40:
        advisory.append(
            f"Low humidity ({humidity}%): Consider misting or grouping plants to maintain humidity."
        )
    elif humidity is not None and humidity > 70:
        advisory.append(
            f"High humidity ({humidity}%): Excellent for tropicals; ensure adequate air flow."
        )

    formatted_loc = ", ".join(
        [part for part in [loc_name, admin1, country] if part]
    )

    return {
        "location": formatted_loc,
        "temperature_f": temp,
        "humidity_percent": humidity,
        "conditions": conditions,
        "today_high_f": today_high,
        "today_low_f": today_low,
        "plant_advisory": (
            " ".join(advisory)
            if advisory
            else "Conditions are pleasant and suitable for houseplants."
        ),
    }
