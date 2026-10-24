"""HopsSighting backend - Hour 1 hello world.

Serves a health check and a sample sighting that matches the shared
JSON contract in docs/api-contract.md.
"""
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="HopsSighting API", version="0.1.0")

# Allow the local frontend (served by Deno on :8000) to call us during dev.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Sighting(BaseModel):
    """One hops sighting. This is the shared contract the frontend renders."""

    id: str
    species: str
    lat: float
    lon: float
    observed_at: str  # ISO 8601 UTC timestamp
    confidence: float  # 0.0 - 1.0


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "hopssighting-api", "version": "0.1.0"}


@app.get("/api/sightings", response_model=list[Sighting])
def list_sightings() -> list[Sighting]:
    """Hour 1: return a single hard-coded sighting to prove the pipe works."""
    return [
        Sighting(
            id="sighting-0001",
            species="Humulus lupulus",
            lat=47.6062,
            lon=-122.3321,
            observed_at=datetime.now(timezone.utc).isoformat(),
            confidence=0.92,
        )
    ]
