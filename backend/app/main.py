"""HopsSighting backend - FastAPI skeleton.

The scoring engine now lives in two standalone CLI parts:
  - app/fetch.py  (Part 1) writes a site-data JSON dataset
  - app/score.py  (Part 2) reads a dataset and produces a rating

This server keeps the frontend's health + sightings endpoints. Wiring
the scorer behind an HTTP endpoint is a later step.
"""
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

API_VERSION = "0.2.0"

app = FastAPI(title="HopsSighting API", version=API_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Sighting(BaseModel):
    id: str
    species: str
    lat: float
    lon: float
    observed_at: str
    confidence: float


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "hopssighting-api", "version": API_VERSION}


@app.get("/api/sightings", response_model=list[Sighting])
def list_sightings() -> list[Sighting]:
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
