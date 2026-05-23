"""
weather_fetcher.py
------------------
Fetches weather data from Pirate Weather for flight delay modeling.
 
Supports:
  - Historical (time machine) lookups for BTS training data
  - Forecast lookups for live 72-hour predictions
  - SQLite cache to avoid redundant API calls
 
Usage:
    from weather_fetcher import WeatherFetcher
 
    fetcher = WeatherFetcher(api_key="your_key_here")
 
    # Single historical lookup
    wx = fetcher.get_historical("SFO", datetime(2024, 6, 15, 17, 0))
 
    # Bulk backfill from BTS dataframe
    wx_df = fetcher.backfill_from_bts(bts_df, airports=["SFO", "JFK", "ORD"])
 
    # Forecast for next 72 hours
    wx = fetcher.get_forecast("JFK")
"""

import os
import time
import sqlite3
import logging
import requests
import pandas as pd
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Airport reference — lat/lon + local timezone
# Add more airports here as needed
# ---------------------------------------------------------------------------
AIRPORTS = {
    "ORD": {"lat": 41.9742, "lon": -87.9073, "tz": "America/Chicago",    "name": "Chicago O'Hare"},
    "JFK": {"lat": 40.6413, "lon": -73.7781, "tz": "America/New_York",   "name": "New York JFK"},
    "SFO": {"lat": 37.6213, "lon": -122.379, "tz": "America/Los_Angeles", "name": "San Francisco"},
    "DEN": {"lat": 39.8561, "lon": -104.674, "tz": "America/Denver",     "name": "Denver"},
    "ATL": {"lat": 33.6407, "lon": -84.4277, "tz": "America/New_York",   "name": "Atlanta"},
    "SEA": {"lat": 47.4502, "lon": -122.309, "tz": "America/Los_Angeles", "name": "Seattle"},
    "MIA": {"lat": 25.7959, "lon": -80.2870, "tz": "America/New_York",   "name": "Miami"},
    "LAX": {"lat": 33.9425, "lon": -118.408, "tz": "America/Los_Angeles", "name": "Los Angeles"},
    "BOS": {"lat": 42.3656, "lon": -71.0096, "tz": "America/New_York",   "name": "Boston"},
    "LGA": {"lat": 40.7772, "lon": -73.8726, "tz": "America/New_York",   "name": "New York LaGuardia"},
}

class PirateWeatherFetcher: 

    BASE_URL = "https://api.pirateweather.net/forecast"

    def __init__(self, api_key: str, cache_path: str = "weather_cache.db", rate_limit_delay: float = 0.25):
        """
        Args:
            api_key:          Your Pirate Weather API key
            cache_path:       Path to SQLite cache file (created if missing)
            rate_limit_delay: Seconds to wait between API calls (default 0.25 = 4 req/sec)
        """
        self.api_key = api_key
        self.rate_limit_delay = rate_limit_delay
        self._init_cache(cache_path)
        self._spc_cache: dict = {}


    ## -- Lookup historical data -- ##
    def get_historical_data(
        self,
        airport: str,
        dt: datetime
    ) -> dict | None:

        if airport not in AIRPORTS:
            raise ValueError(f"Unknown airport: '{airport}'.  Added information for this airport in the AIRPORTS dictionary.")

        info = AIRPORTS[airport]

        # Normalize to UTC timestamp
        if dt.tzinfo is None:
            local_tz = ZoneInfo(info["tz"])
            dt = dt.replace(tzinfo=local_tz)
            unix_ts = int(dt.astimezone(timezone.utc).timestamp())

        # Round to the nearest hour for cache key
        hour_ts = (unix_ts // 3600) * 3600
        cache_key = f"{airport}_{hour_ts}"

        cached = self._cache_get(cache_key)
        if cached:
            return cached
        
        url = f"{self.BASE_URL}/{self.api_key}/{info['lat']},{info['lon']},{hour_ts}"
        params = {"units": "us", "exclude": "minutely,daily,alerts"}

        data = self._fetch(url, params)
        if not data:
            return None

        result = data._parse_hourly(data, hour_ts)
        if result:
            self._cache_set(cache_key, result)

        return result
