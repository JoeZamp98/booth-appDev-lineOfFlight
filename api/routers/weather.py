import requests
import time
from fastapi import APIRouter
from pydantic import BaseModel
import os

router = APIRouter(prefix="/weather", tags=["weather"])

# In-memory cache so we hit Pirate Weather at most once per airport per TTL.
# Keeps us well under the free-tier rate limit (429s) and lets us serve the
# last good reading if the upstream is throttled or briefly unavailable.
CACHE_TTL = 600  # seconds
_cache = {}      # airport -> (fetched_at, payload)

AIRPORTS = {
    "SFO": {"lat": 37.6213, "lon": -122.379},
    "JFK": {"lat": 40.6413, "lon": -73.7781},
    "ORD": {"lat": 41.9742, "lon": -87.9073},
    "LAX": {"lat": 33.9425, "lon": -118.408},
    "BOS": {"lat": 42.3656, "lon": -71.0096},
    "ATL": {"lat": 33.6407, "lon": -84.4277},
    "DEN": {"lat": 39.8561, "lon": -104.6737},
    "SEA": {"lat": 47.4502, "lon": -122.3088},
}

FALLBACK = {
    "temp_f":    62,
    "condition": "Scattered clouds",
    "wind":      "12 kt",
    "vis":       "10 mi",
    "precip":    0,
    "cloud":     0.3,
    "source":    "dummy"
}


class WeatherResponse(BaseModel):
    airport:   str
    temp_f:    int | None
    condition: str
    wind:      str
    vis:       str
    precip:    float
    cloud:     float
    source:    str


@router.get("/{airport}", response_model=WeatherResponse)
def get_weather(airport: str):
    airport = airport.upper()
    coords  = AIRPORTS.get(airport)

    if not coords:
        return {**FALLBACK, "airport": airport}

    # Serve a fresh cached reading if we have one.
    cached = _cache.get(airport)
    if cached and (time.time() - cached[0]) < CACHE_TTL:
        return cached[1]

    api_key = os.environ.get("PIRATE_WEATHER_API_KEY")
    if not api_key:
        return {**FALLBACK, "airport": airport}

    try:
        url = f"https://api.pirateweather.net/forecast/{api_key}/{coords['lat']},{coords['lon']}"
        resp = requests.get(url, params={
            "units": "us",
            "exclude": "minutely,hourly,daily,alerts"
        }, timeout=10)
        resp.raise_for_status()
        data = resp.json().get("currently", {})

        result = {
            "airport":   airport,
            "temp_f":    round(data.get("temperature", 62)),
            "condition": data.get("summary", "Unknown"),
            "wind":      f"{round(data.get('windSpeed', 0))} kt",
            "vis":       f"{min(round(data.get('visibility', 10)), 10)} mi",
            "precip":    float(data.get("precipProbability", 0)),
            "cloud":     float(data.get("cloudCover", 0)),
            "source":    "api"
        }
        _cache[airport] = (time.time(), result)
        return result

    except Exception as e:
        print(f"Weather fetch failed: {e}")
        # Prefer the last good reading (even if stale) over a flat dummy.
        if cached:
            return cached[1]
        return {**FALLBACK, "airport": airport}