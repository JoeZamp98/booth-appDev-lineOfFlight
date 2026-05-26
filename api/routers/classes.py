from pydantic import BaseModel

class FlightRequest(BaseModel):
    carrier: str
    flight_number: str
    origin: str
    dest: str
    date: str

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
    dep_time: str
    arr_time: str
    arr_plus_day: bool
    aircraft: str
    seat: str | None
    status: str
    delay_prob: float
    likely_delay: int
    drivers: list[DelayDriver]
