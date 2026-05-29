from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import predictions, weather, flights

app = FastAPI(title="Line of Flight API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predictions.router)
app.include_router(weather.router)
app.include_router(flights.router)

@app.get("/health")
def health():
    return {"status": "ok"}
    