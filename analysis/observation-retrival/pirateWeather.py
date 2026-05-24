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

    BASE_URL = "https://timemachine.pirateweather.net/forecast"

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

        result = self._parse_hourly(data, hour_ts)

        if result:
            self._cache_set(cache_key, result)

        return result

    ## -- Helpers -- ##
    

    def _init_cache(self, path: str):
        self._conn = sqlite3.connect(path)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS weather_cache(
                key TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                ts INTEGER NOT NULL
            )
        """)

        self._conn.commit()
        log.info(f"Cache initialized at {path}")

    def _cache_get(
        self,
        key: str
    ) -> dict | None:
        import json
        row = self._conn.execute(
            """
                SELECT data FROM weather_cache WHERE key = ?
            """, (key,)).fetchone()

        if row: 
            return json.loads(row[0])
        
        return None
    
    def _cache_set(self, key: str, data: dict) -> None:
        import json
        self._conn.execute(
            "INSERT OR REPLACE INTO weather_cache (key, data, ts) VALUES (?, ?, ?)",
            (key, json.dumps(data), int(time.time())),
        )
        self._conn.commit()

    def _fetch(
        self, 
        url: str,
        params: dict
    ) -> dict | None:

        time.sleep(self.rate_limit_delay)

        try: 
            resp = requests.get(url, params=params, timeout=15)

            resp.raise_for_status()

            return resp.json()

        except requests.exceptions.HTTPError as e:
            log.error(f"HTTP error: {e} — URL: {url}")
        except requests.exceptions.Timeout:
            log.error(f"Timeout fetching: {url}")
        except Exception as e:
            log.error(f"Unexpected error: {e}")
        return None  

    def _parse_hourly(
        self,
        data: dict,
        target_ts: int
    ) -> dict | None:
        """
            Extract the hourly record closest to the target timestamp for a Pirate Weather API response.
        """

        hours = data.get("hourly", {}).get("data", [])

        if not hours: 
            
            curr = data.get("currently", {})

            # if curr:
            #     return self._extract_fields(curr)
            
            return None

        closest = min(hours, key=lambda h: abs(h.get("time", 0) - target_ts))

        return closest

if __name__ == "__main__":

    import os
    from dotenv import load_dotenv

    load_dotenv('.env')

    API_KEY = os.environ.get("PIRATE_WEATHER_API_KEY", None)

    fetcher = PirateWeatherFetcher(API_KEY)

    ## -- Single Historical Lookup -- ##
    print("\n--- TEST: Historical lookup: SFO, June 15 2024 17:00 local ---")

    wx = fetcher.get_historical_data("SFO", datetime(2024, 6, 15, 17, 0))

    print(wx)

