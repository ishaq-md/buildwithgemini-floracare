"""Google Maps Platform tools for Geocoding and Places API (New)."""

import json
import os
import urllib.parse
import urllib.request
from typing import Any, Dict, List


def get_maps_api_key() -> str:
    """Retrieves Google Maps API key from environment."""
    return os.getenv("GOOGLE_MAPS_API_KEY", "").strip()


def geocode_address(address: str) -> Dict[str, Any]:
    """Uses the Google Maps Geocoding API to turn an address or city into latitude and longitude coordinates.

    Args:
        address: The street address, city, or postal code to geocode (e.g. '1600 Amphitheatre Pkwy, Mountain View, CA' or 'Seattle, WA').

    Returns:
        A dictionary containing the formatted address, latitude, and longitude, or an error message.
    """
    api_key = get_maps_api_key()
    if not api_key or api_key == "PASTE_KEY_HERE":
        return {
            "error": "GOOGLE_MAPS_API_KEY is not configured or still set to 'PASTE_KEY_HERE'. Please update GOOGLE_MAPS_API_KEY in .env."
        }

    params = urllib.parse.urlencode({
        "address": address.strip(),
        "key": api_key,
    })
    url = f"https://maps.googleapis.com/maps/api/geocode/json?{params}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "FloraCare/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": f"Geocoding request failed: {e}"}

    status = data.get("status")
    if status != "OK" or not data.get("results"):
        return {
            "error": f"Geocoding error: {status}",
            "details": data.get("error_message", "No results found"),
        }

    result = data["results"][0]
    loc = result.get("geometry", {}).get("location", {})
    return {
        "formatted_address": result.get("formatted_address"),
        "latitude": loc.get("lat"),
        "longitude": loc.get("lng"),
        "place_id": result.get("place_id"),
    }


def find_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "florist",
    radius_meters: float = 5000.0,
    max_results: int = 5,
) -> Dict[str, Any]:
    """Uses Google Places API (New) to search for nearby places (like florists, plant nurseries, parks, or garden centers).

    Args:
        latitude: Center latitude coordinate.
        longitude: Center longitude coordinate.
        place_type: Type of place to search for (e.g. 'florist', 'park', 'store').
        radius_meters: Search radius in meters (default 5000.0, max 50000.0).
        max_results: Maximum number of places to return (default 5, max 20).

    Returns:
        A dictionary containing a list of nearby places with their name, address, and location.
    """
    api_key = get_maps_api_key()
    if not api_key or api_key == "PASTE_KEY_HERE":
        return {
            "error": "GOOGLE_MAPS_API_KEY is not configured or still set to 'PASTE_KEY_HERE'. Please update GOOGLE_MAPS_API_KEY in .env."
        }

    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location",
        "User-Agent": "FloraCare/1.0",
    }
    payload = {
        "includedTypes": [place_type],
        "maxResultCount": min(max(1, max_results), 20),
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                },
                "radius": float(radius_meters),
            }
        },
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        return {
            "error": f"Places API HTTP error {e.code}",
            "details": error_body,
        }
    except Exception as e:
        return {"error": f"Places API request failed: {e}"}

    raw_places = data.get("places", [])
    extracted_places = []
    for p in raw_places:
        extracted_places.append({
            "name": p.get("displayName", {}).get("text", "Unknown"),
            "address": p.get("formattedAddress", "Unknown Address"),
            "location": p.get("location", {}),
        })

    return {
        "count": len(extracted_places),
        "place_type": place_type,
        "places": extracted_places,
    }
