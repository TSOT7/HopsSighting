"""HopsSighting backend - FastAPI server.

Serves the frontend. The scoring engine has three CLI parts that this
server also exposes over HTTP:
  - app/fetch.py  (Part 1) builds a site-data JSON dataset
  - app/score.py  (Part 2) scores a dataset
  - app/report.py (Part 3) renders a detailed report

Endpoints:
  GET  /api/health          liveness
  GET  /api/sightings       sample sightings feed (legacy)
  POST /api/score           {lat, lon} -> full score payload
  POST /api/report          {lat, lon} -> {markdown} detailed report

For the demo, every clicked location is scored against a single
prefilled datasheet (DEMO_DATASET). Swapping to per-location data later
means changing only `_load_site()`.
"""
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.fetch import load_prefilled
from app.report import build_report
from app.schema import SiteData
from app.score import result_to_dict, score

API_VERSION = "0.3.0"

# The single datasheet every click is scored against (for now).
DEMO_DATASET = "forested"

app = FastAPI(title="HopsSighting API", version=API_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
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


class LocationRequest(BaseModel):
    """A clicked location. WGS84 decimal degrees."""

    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)


def _load_site(req: LocationRequest) -> SiteData:
    """Resolve a clicked location to a SiteData.

    For the demo this always loads the single prefilled datasheet, but
    stamps the clicked coordinates onto it so the response reflects where
    the user actually clicked. Replace this with per-location data (live
    fetch or nearest-dataset) when ready.
    """
    site = load_prefilled(DEMO_DATASET)
    site.lat = req.lat
    site.lon = req.lon
    return site


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


@app.post("/api/score")
def score_location(req: LocationRequest) -> dict:
    """Score a clicked location and return the full rating payload."""
    site = _load_site(req)
    result = score(site)
    return result_to_dict(site, result)


@app.post("/api/report")
def report_location(req: LocationRequest) -> dict:
    """Return a detailed, scientific Markdown report for a location."""
    site = _load_site(req)
    markdown = build_report(site)
    return {
        "location": {"lat": req.lat, "lon": req.lon},
        "markdown": markdown,
    }
