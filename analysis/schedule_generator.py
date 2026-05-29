"""
generate_schedule.py
--------------------
Generates a realistic 72-hour flight schedule from BTS historical data.
Dates are always relative to now so the schedule stays current.

Run from the analysis/ directory:
    python generate_schedule.py

Outputs: ../api/schedule.json
"""

import pandas as pd
import numpy as np
import json
import pickle
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────

TARGET_AIRPORTS = ["SFO", "JFK", "ORD", "LAX", "ATL", "BOS", "DEN", "SEA"]
TARGET_CARRIERS = ["DL", "UA", "AA", "B6", "WN", "AS"]
FLIGHTS_PER_HOUR_WINDOW = 3   # how many flights to sample per origin/hour bucket
MODEL_DIR   = Path("../api/model")        # where the trained model + stats live
OUTPUT_PATH = Path("../api/schedule.json") # where the API actually reads the schedule

# ── Load BTS data ─────────────────────────────────────────────────────

def load_bts(data_dir="./data"):
    csv_files = list(Path(data_dir).glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError("No BTS CSV files found in current directory")

    KEEP_COLS = [
        "MONTH", "DAY_OF_WEEK", "MKT_CARRIER", "TAIL_NUM",
        "ORIGIN", "DEST", "CRS_DEP_TIME", "CRS_ARR_TIME",
        "DEP_DELAY", "ARR_DELAY", "DEP_DEL15", "DISTANCE",
        "CANCELLED", "DIVERTED"
    ]

    dfs = []
    for f in csv_files:
        df = pd.read_csv(f, usecols=lambda c: c in KEEP_COLS, low_memory=False)
        dfs.append(df)

    raw = pd.concat(dfs, ignore_index=True)

    # Filter to target airports/carriers, no cancellations
    mask = (
        raw["ORIGIN"].isin(TARGET_AIRPORTS) &
        raw["DEST"].isin(TARGET_AIRPORTS) &
        raw["MKT_CARRIER"].isin(TARGET_CARRIERS) &
        (raw["CANCELLED"] == 0)
    )
    return raw[mask].copy()


# ── Load model artifacts ──────────────────────────────────────────────

def load_model():
    model_path = MODEL_DIR / "delay_model.pkl"
    if not model_path.exists():
        print("WARNING: No model found — using random probabilities")
        return None, None, None, None, None, None

    with open(model_path, "rb") as f:
        model = pickle.load(f)
    with open(MODEL_DIR / "label_encoders.json") as f:
        encoders = json.load(f)
    with open(MODEL_DIR / "feature_list.json") as f:
        features = json.load(f)

    route_stats        = pd.read_csv(MODEL_DIR / "route_stats.csv")
    carrier_route_stats = pd.read_csv(MODEL_DIR / "carrier_route_stats.csv")
    hour_stats         = pd.read_csv(MODEL_DIR / "hour_stats.csv")

    return model, encoders, features, route_stats, carrier_route_stats, hour_stats


# ── Feature builder ───────────────────────────────────────────────────

def build_feature_vector(row, dt, encoders, features,
                          route_stats, carrier_route_stats, hour_stats):
    dep_hour = int(str(int(row["CRS_DEP_TIME"])).zfill(4)[:2])

    route_row = route_stats[
        (route_stats["ORIGIN"] == row["ORIGIN"]) &
        (route_stats["DEST"]   == row["DEST"])
    ]
    route_ontime  = float(route_row["route_ontime_rate"].iloc[0]) \
                    if len(route_row) else 0.75
    route_med_del = float(route_row["route_median_delay"].iloc[0]) \
                    if len(route_row) else 10.0

    cr_row = carrier_route_stats[
        (carrier_route_stats["MKT_CARRIER"] == row["MKT_CARRIER"]) &
        (carrier_route_stats["ORIGIN"]      == row["ORIGIN"]) &
        (carrier_route_stats["DEST"]        == row["DEST"])
    ]
    carrier_route_ontime = float(cr_row["carrier_route_ontime_rate"].iloc[0]) \
                           if len(cr_row) else 0.75

    hr_row = hour_stats[hour_stats["DEP_HOUR"] == dep_hour]
    hour_ontime = float(hr_row["hour_ontime_rate"].iloc[0]) \
                  if len(hr_row) else 0.75

    def safe_encode(encoder_list, value):
        return encoder_list.index(value) if value in encoder_list else 0

    fv = {
        "MONTH":                     dt.month,
        "DAY_OF_WEEK":               dt.weekday() + 1,
        "DEP_HOUR":                  dep_hour,
        "ORIGIN":                    safe_encode(encoders["origin"],  row["ORIGIN"]),
        "DEST":                      safe_encode(encoders["dest"],    row["DEST"]),
        "MKT_CARRIER":               safe_encode(encoders["carrier"], row["MKT_CARRIER"]),
        "route_ontime_rate":         route_ontime,
        "carrier_route_ontime_rate": carrier_route_ontime,
        "hour_ontime_rate":          hour_ontime,
        "route_median_delay":        route_med_del,
        "prev_arr_delay":            0.0,
        "DISTANCE":                  float(row.get("DISTANCE", 0) or 0),
        "origin_precip_prob":        0,
        "origin_wind_speed":         0,
        "origin_wind_gust":          0,
        "origin_visibility":         10,
        "origin_cloud_cover":        0,
        "origin_temperature":        65,
        "dest_precip_prob":          0,
        "dest_wind_speed":           0,
        "dest_visibility":           10,
        "dest_cloud_cover":          0,
    }

    return [fv[f] for f in features]


# ── Status label ──────────────────────────────────────────────────────

def delay_status(prob):
    if prob < 0.25:   return "Low risk"
    elif prob < 0.50: return "Moderate risk"
    else:             return "High risk"


# ── Main schedule builder ─────────────────────────────────────────────

def generate_schedule(df, model, encoders, features,
                       route_stats, carrier_route_stats, hour_stats):

    now       = datetime.now()
    end_time  = now + timedelta(hours=72)
    schedule  = []

    # Sample flights for each 6-hour window across the 72-hour period
    current = now.replace(minute=0, second=0, microsecond=0)

    while current < end_time:
        window_end = current + timedelta(hours=6)
        dep_hour   = current.hour

        # Find BTS flights that historically depart in this hour window
        # Match on day of week and hour to keep patterns realistic
        dow = current.weekday() + 1   # BTS uses 1=Mon

        window_flights = df[
            (df["DAY_OF_WEEK"] == dow) &
            (df["CRS_DEP_TIME"].astype(str).str.zfill(4).str[:2].astype(int)
             .between(dep_hour, dep_hour + 5))
        ]

        if len(window_flights) == 0:
            current = window_end
            continue

        # Sample a representative set
        sample_size = min(FLIGHTS_PER_HOUR_WINDOW * 4, len(window_flights))
        sampled     = window_flights.sample(sample_size, random_state=dep_hour)

        for _, row in sampled.iterrows():
            # Build realistic departure datetime
            raw_time = str(int(row["CRS_DEP_TIME"])).zfill(4)
            dep_dt   = current.replace(
                hour=int(raw_time[:2]),
                minute=int(raw_time[2:]),
                second=0
            )

            # Skip if outside our window
            if dep_dt < now or dep_dt > end_time:
                continue

            # Score with the model — the single source of truth for delay
            # probabilities. Flights we can't score are skipped rather than
            # given a fake number, so the board never shows random data.
            try:
                fv   = build_feature_vector(
                            row, dep_dt, encoders, features,
                            route_stats, carrier_route_stats, hour_stats)
                prob = float(model.predict_proba(
                            np.array(fv).reshape(1, -1))[0][1])
            except Exception as e:
                print(f"Skipping {row['MKT_CARRIER']} "
                      f"{row['ORIGIN']}->{row['DEST']}: {e}")
                continue

            # Build flight number from carrier + random realistic number
            fl_num = f"{row['MKT_CARRIER']} {int(row.get('OP_CARRIER_FL_NUM', np.random.randint(100,9999)))}" \
                     if "OP_CARRIER_FL_NUM" in row.index \
                     else f"{row['MKT_CARRIER']} {np.random.randint(100, 9999)}"

            schedule.append({
                "flight":        fl_num,
                "carrier":       row["MKT_CARRIER"],
                "origin":        row["ORIGIN"],
                "dest":          row["DEST"],
                "dep_time":      dep_dt.strftime("%Y-%m-%d %H:%M"),
                "dep_time_disp": dep_dt.strftime("%b %-d · %H:%M"),
                "dep_hour":      dep_dt.hour,
                "distance":      int(row.get("DISTANCE", 0) or 0),
                "delay_prob":    round(prob, 4),
                "status":        delay_status(prob),
                "generated_at":  now.isoformat(),
            })

        current = window_end

    # Sort by departure time
    schedule.sort(key=lambda x: x["dep_time"])

    # Deduplicate — keep one flight per origin/dest/carrier/hour
    seen    = set()
    deduped = []
    for f in schedule:
        key = (f["origin"], f["dest"], f["carrier"], f["dep_time"][:13])
        if key not in seen:
            seen.add(key)
            deduped.append(f)

    return deduped


# ── Run ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Loading BTS data...")
    df = load_bts()
    print(f"BTS rows available: {len(df):,}")

    print("Loading model...")
    model, encoders, features, route_stats, carrier_route_stats, hour_stats = load_model()
    if model is None:
        sys.exit(
            f"ERROR: no model at {MODEL_DIR / 'delay_model.pkl'}. Refusing to "
            "generate a schedule with random probabilities — the board and the "
            "prediction page must share the same model. Train/copy the model first."
        )

    print("Generating schedule...")
    schedule = generate_schedule(
        df, model, encoders, features,
        route_stats, carrier_route_stats, hour_stats
    )

    output_path = OUTPUT_PATH
    with open(output_path, "w") as f:
        json.dump({
            "generated_at":   datetime.now().isoformat(),
            "flight_count":   len(schedule),
            "flights":        schedule
        }, f, indent=2)

    print(f"\nGenerated {len(schedule):,} flights → {output_path}")
    print(f"Time window: now → +72 hours")
    print(f"Sample:")
    for f in schedule[:3]:
        print(f"  {f['dep_time_disp']}  {f['flight']}  "
              f"{f['origin']}→{f['dest']}  {f['delay_prob']:.0%}")

