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

# SPC outlook URLs (day 1-3, categorical)
SPC_URLS = {
    1: "https://www.spc.noaa.gov/products/outlook/day1otlk_cat.lyr.geojson",
    2: "https://www.spc.noaa.gov/products/outlook/day2otlk_cat.lyr.geojson",
    3: "https://www.spc.noaa.gov/products/outlook/day3otlk_cat.lyr.geojson",
}
 
# Ordinal encoding for SPC risk categories
SPC_RISK_LEVELS = {
    "TSTM": 1,
    "MRGL": 2,
    "SLGT": 3,
    "ENH":  4,
    "MDT":  5,
    "HIGH": 6,
}