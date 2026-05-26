from .classes import FlightRequest, PredictionResponse
from .dummy_data import DUMMY_PREDICTIONS
from fastapi import APIRouter

router = APIRouter(prefix="/predictions", tags=["predictions"])

@router.post("/predict", response_model=PredictionResponse)
def predict(req: FlightRequest):

    key = f"{req.carrier}-{req.flight_number}"

    result = DUMMY_PREDICTIONS.get(key, DUMMY_PREDICTIONS["DL-1221"])

    return result

@router.get("/flights")
def get_flights(origin: str = "SFO", dest: str = "JFK"):
    """Returns flight options for a route — will pull from BTS data later."""
    return [
        {"flight": "UA 1549", "carrier": "UA", "dep": "07:00", "delay_prob": 0.23},
        {"flight": "B6 624",  "carrier": "B6", "dep": "10:25", "delay_prob": 0.18},
        {"flight": "AA 24",   "carrier": "AA", "dep": "13:45", "delay_prob": 0.31},
        {"flight": "DL 1221", "carrier": "DL", "dep": "17:10", "delay_prob": 0.64},
    ]
