import json
import os
from fastapi import APIRouter, Query
from datetime import datetime

router = APIRouter(prefix="/flights", tags=["flights"])

BASE_DIR  = os.path.dirname(os.path.dirname(__file__))
SCHEDULE_PATH = os.path.join(BASE_DIR, "schedule.json")

_schedule = None

def get_schedule():
    global _schedule
    if _schedule is None:
        if not os.path.exists(SCHEDULE_PATH):
            return []
        with open(SCHEDULE_PATH) as f:
            data = json.load(f)
            _schedule = data.get("flights", [])
    return _schedule


@router.get("/board")
def flight_board(
    origin:      str | None = Query(None),
    dest:        str | None = Query(None),
    carrier:     str | None = Query(None),
    risk:        str | None = Query(None),   # low | moderate | high
    hours_ahead: int        = Query(72),
):
    flights = get_schedule()

    now     = datetime.now()
    cutoff  = now.strftime("%Y-%m-%d %H:%M")
    max_dt  = (now.replace(hour=0, minute=0) if hours_ahead == 72
               else now).strftime("%Y-%m-%d %H:%M")

    # Filter
    results = []
    for f in flights:
        if f["dep_time"] < cutoff:
            continue
        if origin  and f["origin"]  != origin.upper():
            continue
        if dest    and f["dest"]    != dest.upper():
            continue
        if carrier and f["carrier"] != carrier.upper():
            continue
        if risk:
            if risk == "low"      and f["delay_prob"] >= 0.25: continue
            if risk == "moderate" and not (0.25 <= f["delay_prob"] < 0.50): continue
            if risk == "high"     and f["delay_prob"] < 0.50:  continue
        results.append(f)

    return {
        "count":   len(results),
        "flights": results
    }


@router.get("/meta")
def flight_meta():
    """Returns available filter options for the board."""
    flights  = get_schedule()
    origins  = sorted(set(f["origin"]  for f in flights))
    dests    = sorted(set(f["dest"]    for f in flights))
    carriers = sorted(set(f["carrier"] for f in flights))
    return {
        "origins":  origins,
        "dests":    dests,
        "carriers": carriers,
    }

@router.get("/search")
def search_flights(
    origin: str = Query(...),
    dest:   str = Query(...),
    date:   str | None = Query(None),
):
    flights = get_schedule()
    now     = datetime.now()
    cutoff  = now.strftime("%Y-%m-%d %H:%M")

    results = []
    for f in flights:
        if f["origin"] != origin.upper(): continue
        if f["dest"]   != dest.upper():   continue
        if f["dep_time"] < cutoff:        continue

        # If date specified, filter to that day
        if date and not f["dep_time"].startswith(date):
            continue

        results.append(f)

    results = sorted(results, key=lambda x: x["dep_time"])[:8]
    return {"flights": results}