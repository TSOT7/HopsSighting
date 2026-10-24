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

API_VERSION = "0.4.0"

# Demo city datasets. A clicked location is scored against the nearest
# city here. Coordinates match the frontend's MA_CITIES markers so a
# click on a city marker resolves to that city's dataset.
CITY_DATASETS: list[dict] = [
    {"name": "Boston", "dataset": "boston", "lat": 42.3601, "lon": -71.0589},
    {"name": "Lowell", "dataset": "lowell", "lat": 42.6334, "lon": -71.3162},
    {"name": "Salem", "dataset": "salem", "lat": 42.5195, "lon": -70.8967},
    {"name": "Concord", "dataset": "concord", "lat": 42.4604, "lon": -71.3489},
    {"name": "Plymouth", "dataset": "plymouth", "lat": 41.9584, "lon": -70.6673},
    {"name": "Provincetown", "dataset": "provincetown", "lat": 42.0501, "lon": -70.1853},
    {"name": "New Bedford", "dataset": "new_bedford", "lat": 41.6362, "lon": -70.9342},
    {"name": "Worcester", "dataset": "worcester", "lat": 42.2626, "lon": -71.8023},
    {"name": "Northampton", "dataset": "northampton", "lat": 42.3251, "lon": -72.6412},
    {"name": "Springfield", "dataset": "springfield", "lat": 42.1015, "lon": -72.5898},
    {"name": "Pittsfield", "dataset": "pittsfield", "lat": 42.4501, "lon": -73.2454},
    {"name": "Greenfield", "dataset": "greenfield", "lat": 42.5876, "lon": -72.5993},
    {"name": "Gloucester", "dataset": "gloucester", "lat": 42.6159, "lon": -70.6620},
    {"name": "Lawrence", "dataset": "lawrence", "lat": 42.7070, "lon": -71.1631},
]

# Fallback dataset if the city list is somehow empty.
DEMO_DATASET = "forested"


def _nearest_city(lat: float, lon: float) -> dict:
    """Return the CITY_DATASETS entry closest to a point (planar distance,
    fine for intra-Massachusetts separation)."""
    return min(
        CITY_DATASETS,
        key=lambda c: (c["lat"] - lat) ** 2 + (c["lon"] - lon) ** 2,
    )

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
    """Resolve a clicked location to the nearest city's dataset.

    The clicked coordinates are stamped onto the result so the response
    reflects exactly where the user clicked, while the environmental data
    comes from the matched city dataset.
    """
    city = _nearest_city(req.lat, req.lon) if CITY_DATASETS else None
    dataset = city["dataset"] if city else DEMO_DATASET
    site = load_prefilled(dataset)
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
