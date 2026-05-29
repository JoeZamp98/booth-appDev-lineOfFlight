import json
import os
from fastapi import APIRouter, Query
from datetime import datetime, timedelta, date

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


def get_current_schedule():
    """Schedule rebased so its 72-hour window always starts today.

    schedule.json is a static snapshot covering the 72 hours after it was
    generated, and the deployed API can't regenerate it (the BTS source data
    and route/hour stats aren't shipped). Left alone, the board empties once
    that frozen window slips into the past. Shifting every departure by whole
    days anchors the window to the current date while preserving each flight's
    time-of-day and day-of-week pattern.
    """
    flights = get_schedule()
    if not flights:
        return []

    base_date   = datetime.strptime(flights[0]["dep_time"], "%Y-%m-%d %H:%M").date()
    offset_days = (date.today() - base_date).days
    if offset_days == 0:
        return flights

    shift   = timedelta(days=offset_days)
    rebased = []
    for f in flights:
        dt = datetime.strptime(f["dep_time"], "%Y-%m-%d %H:%M") + shift
        g  = dict(f)
        g["dep_time"]      = dt.strftime("%Y-%m-%d %H:%M")
        g["dep_time_disp"] = dt.strftime("%b %-d · %H:%M")
        g["dep_hour"]      = dt.hour
        rebased.append(g)
    return rebased


@router.get("/board")
def flight_board(
    origin:      str | None = Query(None),
    dest:        str | None = Query(None),
    carrier:     str | None = Query(None),
    risk:        str | None = Query(None),   # low | moderate | high
    hours_ahead: int        = Query(72),
):
    flights = get_current_schedule()

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
    flights = get_current_schedule()
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