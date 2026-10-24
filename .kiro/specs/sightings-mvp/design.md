# Design: Sightings MVP

## Overview

Extend the Hour 1 hello-world into a working create/read/map loop while keeping
the stack dependency-light (Python + static frontend). We add a POST endpoint,
a deterministic scoring function, file-based persistence, and a Leaflet map on
the frontend. No database and no frontend framework yet — both are deliberate
deferrals recorded in the tech steering.

## Architecture

```
Browser (Leaflet map + report view)
        │  GET /api/sightings, POST /api/sightings
        ▼
FastAPI (app/main.py)
   ├── routes        -> validate via Pydantic, call scoring + store
   ├── scoring.py    -> confidence(sighting) -> float in [0,1]
   └── store.py      -> JSON-file backed repository
        │
        ▼
backend/data/sightings.json   (gitignored cache/state)
```

## Components

### Backend

- `app/models.py` — Pydantic models. `SightingIn` (client submits, no id/score)
  and `Sighting` (stored/returned, includes `id`, `confidence`). Validation
  bounds for lat/lon live here.
- `app/scoring.py` — pure function `score(sighting_in) -> float`. Deterministic:
  starts from a base, adds weight for species specificity and a plausible
  timestamp. Pure and side-effect free so it is trivially unit- and
  property-testable.
- `app/store.py` — a small repository over `backend/data/sightings.json`:
  `list_all()`, `add(sighting)`. Reads/writes the whole file for now (fine at
  MVP scale); the interface hides this so we can swap in SQLite later without
  touching routes.
- `app/main.py` — wires routes to store + scoring. `GET /api/sightings`,
  `POST /api/sightings`, existing `GET /api/health`.

### Frontend

- Add Leaflet via CDN `<link>`/`<script>` (no build step, consistent with the
  no-Node stance).
- Render one marker per sighting; clicking opens the existing report panel.
- A simple form (species + lat/lon + optional time) POSTs a new sighting, then
  refreshes markers.

## Data flow: creating a sighting

1. User submits the form; frontend POSTs `SightingIn` JSON to `/api/sightings`.
2. FastAPI validates into `SightingIn` (422 on bad lat/lon or empty species).
3. `scoring.score()` computes confidence; a new id is minted.
4. `store.add()` appends to `sightings.json`.
5. The created `Sighting` is returned; the map adds a marker.

## Scoring (initial, deterministic)

`confidence = clamp(base + species_bonus + recency_bonus, 0, 1)` where base is a
constant, `species_bonus` rewards a recognized/specific species string, and
`recency_bonus` rewards a timestamp that is in the past and recent. Pure
function — same input always yields the same score, which supports Requirement
2.3 (no silent re-scoring) and property-based testing.

## Error handling

- Validation errors surface as FastAPI 422 with field detail.
- Store read tolerates a missing/empty file by treating it as an empty list.
- Frontend wraps fetches in try/catch and shows a non-fatal banner.

## Testing strategy

- Unit tests for `scoring.score()` boundary behavior and clamping.
- Property-based tests (Hypothesis) for scoring: output always in [0, 1] for
  arbitrary valid inputs; determinism (same input -> same output). This maps
  directly to the hackathon's property-based-testing criterion.
- Store round-trip test: add then list returns the item; survives a reload.
- One API test per endpoint via FastAPI's TestClient.

## Deliberate deferrals

- No auth/users yet (MVP is open contribution on a trusted demo).
- JSON file instead of a database; the `store` interface isolates this.
- Static frontend; a framework comes only when the UI complexity demands it.
