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
from constants import AIRPORTS

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Airport reference — lat/lon + local timezone
# Add more airports here as needed
# ---------------------------------------------------------------------------

class PirateWeatherFetcher: 

    BASE_HISTORICAL_URL = "https://timemachine.pirateweather.net/forecast"
    BASE_FORECAST_URL = "https://api.pirateweather.net/forecast"

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
        
        url = f"{self.BASE_HISTORICAL_URL}/{self.api_key}/{info['lat']},{info['lon']},{hour_ts}"
        params = {"units": "us", "exclude": "minutely,daily,alerts"}

        data = self._fetch(url, params)
        if not data:
            return None

        result = self._parse_hourly(data, hour_ts)

        if result:
            self._cache_set(cache_key, result)

        return result


    def get_forecast_data(
        self,
        airport: str,
    ) -> list[dict]:
        """
        Fetch hourly forecast for the next 48 hours for an airport.
 
        Returns:
            List of dicts, one per hour, with weather fields + unix timestamp
        """

        if airport not in AIRPORTS: 

            raise ValueError(f"Unknown airport: ")

        info = AIRPORTS[airport]

        url = f"{self.BASE_FORECAST_URL}/{self.api_key}/{info['lat']},{info['lon']}"
        params = {"units": "us", "exclude": "minutely,daily"}

        data = self._fetch(url, params)

        print(data)

        if not data: 

            return []

        hours = data.get("hourly", {}).get("data", [])

        results = []

        for hour in hours: 

            results.append(self._extract_fields(hour))

        return results

    ## -- Retrieve data for BTS backfill -- ##
    def backfill_from_bts(
        self, 
        bts_df: pd.DataFrame,
        airports: list[str],
        origin_col: str = "ORIGIN",
        date_col: str = "FL_DATE",
        dep_time_col: str = "CRS_DEP_TIME",
        arr_time_col: str = "CRS_ARR_TIME",
        dest_col: str = "DEST",    
    ) -> pd.DataFrame:
        """
        Fetch weather for all unique (airport, date, hour) combos in a BTS dataframe
        and return a weather dataframe ready to join back.
 
        Fetches weather for both origin (at departure hour) and dest (at arrival hour).
 
        Args:
            bts_df:   DataFrame loaded from BTS CSV
            airports: List of IATA codes to process (filters the dataframe)
 
        Returns:
            DataFrame with columns: airport, fl_date, hour, + weather fields
            Join back to bts_df on origin=airport + dep_hour, or dest=airport + arr_hour
        """

        mask = bts_df[origin_col].isin(airports) | bts_df[dest_col].isin(airports)
        df = bts_df[mask].copy()
        log.info(f"Processing {len(df):,} flights across {len(airports)} airports")

        # Build set of unique (airport, date, hour) combos - origin/departures

        combos = set()

        for _, row in df.iterrows():

            try:

                date_str = str(row[date_col]).split()[0]

                dep_hour = row[dep_time_col].zfill(4)[:2]
                arr_hour = row[arr_time_col].zfill(4)[:2]

                orig = row[origin_col]
                dest = row[dest_col]

                if orig in airports: 
                    combos.add((orig, date_str, dep_hour))

                if dest in airports:
                    combos.add((dest, date_str, arr_hour))

            except Exception:

                continue

        log.info(f"Found {len(combos):,} unique (airport, date, hour) combos")

        records = []

        for i, (airport, date, hour) in enumerate(sorted(combos)):

            if i % 50 == 0:

                log.info(f"Progress: {i}/{len(combos)}")

            try: 

                dt = datetime.strptime(f"{date_str} {hour:02d}:00", "%m/%d/%Y %H:%M")

                wx = self.get_historical_data(airport, dt)

                if wx:
                    wx["airport"] = airport
                    wx["fl_date"] = date_str
                    wx["hour"] = hour
                    
                    records.append(wx)
             
            except Exception as e:

                log.warning()


        results_df = pd.DataFrame(records)

        log.info(f"Fetched {len(results_df):,} weather records")

        return results_df

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

            if curr:
                return self._extract_fields(curr)
            
            return None

        closest = min(hours, key=lambda h: abs(h.get("time", 0) - target_ts))

        return self._extract_fields(closest)


    def _extract_fields(
        self,
        hour: dict
    ) -> dict:

        return {
            "unix_time":        hour.get("time"),
            "precip_prob":      hour.get("precipProbability", 0),
            "precip_intensity": hour.get("precipIntensity", 0),
            "wind_speed":       hour.get("windSpeed", 0),
            "wind_gust":        hour.get("windGust", 0),
            "wind_bearing":     hour.get("windBearing", 0),
            "visibility":       min(hour.get("visibility", 10), 10),
            "cloud_cover":      hour.get("cloudCover", 0),
            "temperature":      hour.get("temperature"),
            "summary":          hour.get("summary", ""),
        }

if __name__ == "__main__":

    import os
    from dotenv import load_dotenv

    load_dotenv('.env')

    API_KEY = os.environ.get("PIRATE_WEATHER_API_KEY", None)

    fetcher = PirateWeatherFetcher(API_KEY)

    bts_df = None

    ## -- Single Historical Lookup -- ##
    print("\n--- TEST: Historical lookup: SFO, June 15 2024 17:00 local ---")

    wx = fetcher.get_historical_data("SFO", datetime(2024, 6, 15, 17, 0))

    forecast = fetcher.get_forecast_data("ORD")

    bts_backfill_data = fetcher.backfill_from_bts(bts_df, airports=list(AIRPORTS.keys()))

    print(forecast)

    print(wx)