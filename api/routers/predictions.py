import os
import json
import pickle
import numpy as np
import pandas as pd
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/predictions", tags=["predictions"])

# ── Load model artifacts at startup ───────────────────────────────────

BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "model")

def load_artifact(filename):
    path = os.path.join(BASE_DIR, filename)
    if not os.path.exists(path):
        print(f"WARNING: {filename} not found at {path}")
        return None
    return path

# Load model
_model = None
_encoders = None
_features = None
_route_stats = None
_carrier_route_stats = None
_hour_stats = None

def get_model():
    global _model, _encoders, _features
    global _route_stats, _carrier_route_stats, _hour_stats

    if _model is None:
        try:
            with open(os.path.join(BASE_DIR, "delay_model.pkl"), "rb") as f:
                _model = pickle.load(f)

            with open(os.path.join(BASE_DIR, "label_encoders.json")) as f:
                _encoders = json.load(f)

            with open(os.path.join(BASE_DIR, "feature_list.json")) as f:
                _features = json.load(f)

            _route_stats = pd.read_csv(
                os.path.join(BASE_DIR, "route_stats.csv"))
            _carrier_route_stats = pd.read_csv(
                os.path.join(BASE_DIR, "carrier_route_stats.csv"))
            _hour_stats = pd.read_csv(
                os.path.join(BASE_DIR, "hour_stats.csv"))

            print("Model and artifacts loaded successfully")
        except Exception as e:
            print(f"Failed to load model: {e}")

    return _model, _encoders, _features, _route_stats, _carrier_route_stats, _hour_stats


# ── Request / Response models ──────────────────────────────────────────

class FlightRequest(BaseModel):
    carrier: str
    flight_number: str
    origin: str
    dest: str
    date: str
    dep_hour: int | None = None
    distance: float | None = None
    prev_arr_delay: float | None = None
    origin_weather: dict | None = None
    dest_weather: dict | None = None


class DelayDriver(BaseModel):
    label: str
    delta: str
    severity: str
    detail: str


class PredictionResponse(BaseModel):
    flight: str
    carrier: str
    origin: str
    dest: str
    delay_prob: float
    likely_delay: int
    drivers: list[DelayDriver]
    model_used: bool

# ── Feature builder ────────────────────────────────────────────────────

def build_features(req: FlightRequest, encoders, features,
                   route_stats, carrier_route_stats, hour_stats) -> dict:
    """Build the feature vector matching the training schema exactly."""

    from datetime import datetime
    dt = datetime.strptime(req.date, "%Y-%m-%d")

    dep_hour = req.dep_hour if req.dep_hour is not None else 12

    # Look up route stats
    route_row = route_stats[
        (route_stats["ORIGIN"] == req.origin) &
        (route_stats["DEST"]   == req.dest)
    ]
    route_ontime  = float(route_row["route_ontime_rate"].iloc[0]) \
                    if len(route_row) else 0.75
    route_med_del = float(route_row["route_median_delay"].iloc[0]) \
                    if len(route_row) else 10.0

    # Look up carrier route stats
    cr_row = carrier_route_stats[
        (carrier_route_stats["MKT_CARRIER"] == req.carrier) &
        (carrier_route_stats["ORIGIN"]      == req.origin) &
        (carrier_route_stats["DEST"]        == req.dest)
    ]
    carrier_route_ontime = float(cr_row["carrier_route_ontime_rate"].iloc[0]) \
                           if len(cr_row) else 0.75

    # Look up hour stats
    hr_row = hour_stats[hour_stats["DEP_HOUR"] == dep_hour]
    hour_ontime = float(hr_row["hour_ontime_rate"].iloc[0]) \
                  if len(hr_row) else 0.75

    # Encode categoricals — unknown airports/carriers get index 0
    def safe_encode(encoder_list, value):
        return encoder_list.index(value) if value in encoder_list else 0

    origin_enc  = safe_encode(encoders["origin"],  req.origin)
    dest_enc    = safe_encode(encoders["dest"],    req.dest)
    carrier_enc = safe_encode(encoders["carrier"], req.carrier)

    # Weather features
    ox = req.origin_weather or {}
    dx = req.dest_weather   or {}

    feature_vector = {
        "MONTH":                      dt.month,
        "DAY_OF_WEEK":                dt.weekday() + 1,
        "DEP_HOUR":                   dep_hour,
        "ORIGIN":                     origin_enc,
        "DEST":                       dest_enc,
        "MKT_CARRIER":                carrier_enc,
        "route_ontime_rate":          route_ontime,
        "carrier_route_ontime_rate":  carrier_route_ontime,
        "hour_ontime_rate":           hour_ontime,
        "route_median_delay":         route_med_del,
        "prev_arr_delay":             req.prev_arr_delay or 0.0,
        "DISTANCE":                   float(req.distance) if req.distance is not None else 0.0,
        "origin_precip_prob":         ox.get("precip_prob", 0),
        "origin_wind_speed":          ox.get("wind_speed", 0),
        "origin_wind_gust":           ox.get("wind_gust", 0),
        "origin_visibility":          ox.get("visibility", 10),
        "origin_cloud_cover":         ox.get("cloud_cover", 0),
        "origin_temperature":         ox.get("temperature", 65),
        "dest_precip_prob":           dx.get("precip_prob", 0),
        "dest_wind_speed":            dx.get("wind_speed", 0),
        "dest_visibility":            dx.get("visibility", 10),
        "dest_cloud_cover":           dx.get("cloud_cover", 0),
    }

    # Return in exact feature order from training
    return [feature_vector[f] for f in features]


# ── Delay drivers builder ──────────────────────────────────────────────

def build_drivers(req, delay_prob, route_ontime,
                  carrier_route_ontime, prev_arr_delay,
                  origin_weather, dest_weather) -> list[dict]:
    """
    Generate human-readable delay drivers from feature values.
    Ordered by estimated impact on delay probability.
    """
    drivers = []

    # Route history
    if route_ontime < 0.65:
        drivers.append({
            "label":    f"{req.origin}→{req.dest} route history",
            "delta":    f"+{round((0.75 - route_ontime) * 100)}%",
            "severity": "high",
            "detail":   f"This route is on-time only {round(route_ontime*100)}% "
                        f"of the time — below the 75% baseline."
        })
    elif route_ontime > 0.85:
        drivers.append({
            "label":    f"{req.origin}→{req.dest} route history",
            "delta":    f"-{round((route_ontime - 0.75) * 100)}%",
            "severity": "positive",
            "detail":   f"Strong route — on-time {round(route_ontime*100)}% historically."
        })

    # Carrier performance on this route
    if carrier_route_ontime < 0.65:
        drivers.append({
            "label":    f"{req.carrier} performance on this route",
            "delta":    f"+{round((0.75 - carrier_route_ontime) * 100)}%",
            "severity": "high",
            "detail":   f"{req.carrier} is on-time {round(carrier_route_ontime*100)}% "
                        f"on this specific route."
        })

    # Inbound aircraft delay
    if prev_arr_delay and prev_arr_delay > 15:
        severity = "high" if prev_arr_delay > 45 else "medium"
        drivers.append({
            "label":    "Inbound aircraft delay",
            "delta":    f"+{min(round(prev_arr_delay * 0.6), 35)}%",
            "severity": severity,
            "detail":   f"Inbound aircraft is running {round(prev_arr_delay)} min late — "
                        f"tight turn increases delay risk."
        })

    # Origin weather
    if origin_weather:
        if origin_weather.get("precip_prob", 0) > 0.4:
            drivers.append({
                "label":    f"{req.origin} precipitation",
                "delta":    f"+{round(origin_weather['precip_prob'] * 30)}%",
                "severity": "medium",
                "detail":   f"{round(origin_weather['precip_prob']*100)}% chance of "
                            f"precipitation at departure."
            })
        if origin_weather.get("wind_speed", 0) > 25:
            drivers.append({
                "label":    f"{req.origin} wind",
                "delta":    "+12%",
                "severity": "medium",
                "detail":   f"Winds at {round(origin_weather['wind_speed'])} kt — "
                            f"may affect departure sequencing."
            })
        if origin_weather.get("visibility", 10) < 3:
            drivers.append({
                "label":    f"{req.origin} low visibility",
                "delta":    "+18%",
                "severity": "high",
                "detail":   f"Visibility at {origin_weather['visibility']} mi — "
                            f"IFR conditions likely slow departures."
            })

    # Dest weather
    if dest_weather:
        if dest_weather.get("wind_speed", 0) > 25:
            drivers.append({
                "label":    f"{req.dest} arrival winds",
                "delta":    "+10%",
                "severity": "medium",
                "detail":   f"Destination winds at {round(dest_weather['wind_speed'])} kt."
            })

    # Fallback if no strong drivers found
    if not drivers:
        drivers.append({
            "label":    "Historical pattern",
            "delta":    f"+{round(delay_prob * 100)}%",
            "severity": "low",
            "detail":   f"Based on historical patterns for this route, "
                        f"carrier, and time of day."
        })

    return drivers[:5]   # cap at 5 drivers


# ── Endpoints ──────────────────────────────────────────────────────────

@router.post("/predict", response_model=PredictionResponse)
def predict(req: FlightRequest):
    model, encoders, features, route_stats, carrier_route_stats, hour_stats = get_model()

    if model is None:
        # Model not loaded — return dummy
        return {
            "flight":      f"{req.carrier} {req.flight_number}",
            "carrier":     req.carrier,
            "origin":      req.origin,
            "dest":        req.dest,
            "delay_prob":  0.35,
            "likely_delay": 20,
            "drivers":     [],
            "model_used":  False
        }

    # Build feature vector
    fv = build_features(
        req, encoders, features,
        route_stats, carrier_route_stats, hour_stats
    )

    # Predict
    X = np.array(fv).reshape(1, -1)
    delay_prob = float(model.predict_proba(X)[0][1])
    likely_delay = max(5, round(delay_prob * 60))

    # Look up stats for drivers
    route_row = route_stats[
        (route_stats["ORIGIN"] == req.origin) &
        (route_stats["DEST"]   == req.dest)
    ]
    route_ontime         = float(route_row["route_ontime_rate"].iloc[0]) \
                           if len(route_row) else 0.75
    cr_row = carrier_route_stats[
        (carrier_route_stats["MKT_CARRIER"] == req.carrier) &
        (carrier_route_stats["ORIGIN"]      == req.origin) &
        (carrier_route_stats["DEST"]        == req.dest)
    ]
    carrier_route_ontime = float(cr_row["carrier_route_ontime_rate"].iloc[0]) \
                           if len(cr_row) else 0.75

    drivers = build_drivers(
        req, delay_prob,
        route_ontime, carrier_route_ontime,
        req.prev_arr_delay or 0,
        req.origin_weather,
        req.dest_weather
    )

    return {
        "flight":       f"{req.carrier} {req.flight_number}",
        "carrier":      req.carrier,
        "origin":       req.origin,
        "dest":         req.dest,
        "delay_prob":   round(delay_prob, 4),
        "likely_delay": likely_delay,
        "drivers":      drivers,
        "model_used":   True
    }


@router.get("/route_stats")
def route_stats(origin: str, dest: str):
    """Historical on-time rate / median delay for a route, from route_stats.csv."""
    _, _, _, rstats, _, _ = get_model()
    if rstats is None:
        return {"available": False}

    row = rstats[
        (rstats["ORIGIN"] == origin.upper()) &
        (rstats["DEST"]   == dest.upper())
    ]
    if row.empty:
        return {"available": False}

    r = row.iloc[0]
    return {
        "available":    True,
        "ontime_rate":  float(r["route_ontime_rate"]),
        "median_delay": float(r["route_median_delay"]),
        "flights":      int(r["route_flights"]),
    }


@router.get("/flights")
def get_flights(origin: str = "SFO", dest: str = "JFK"):
    return [
        {"flight": "UA 1549", "carrier": "UA", "dep": "07:00", "delay_prob": 0.23},
        {"flight": "B6 624",  "carrier": "B6", "dep": "10:25", "delay_prob": 0.18},
        {"flight": "AA 24",   "carrier": "AA", "dep": "13:45", "delay_prob": 0.31},
        {"flight": "DL 1221", "carrier": "DL", "dep": "17:10", "delay_prob": 0.64},
    ]