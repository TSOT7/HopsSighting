# HopsSighting API Contract (v0.3.0)

The shared agreement between backend (FastAPI) and frontend.

Base URL (dev): `http://localhost:8080`. The frontend is served on
`http://localhost:8000`; the backend allows that origin via CORS.

## GET /api/health

Liveness check.

```json
{
  "status": "ok",
  "service": "hopssighting-api",
  "version": "0.1.0"
}
```

## GET /api/sightings

Returns an array of `Sighting` objects.

### Sighting object

| Field         | Type   | Notes                                  |
| ------------- | ------ | -------------------------------------- |
| `id`          | string | Stable unique id, e.g. `sighting-0001` |
| `species`     | string | Scientific or common name              |
| `lat`         | number | Latitude, decimal degrees (WGS84)      |
| `lon`         | number | Longitude, decimal degrees (WGS84)     |
| `observed_at` | string | ISO 8601 UTC timestamp                 |
| `confidence`  | number | 0.0 – 1.0 scoring confidence           |

### Example

```json
[
  {
    "id": "sighting-0001",
    "species": "Humulus lupulus",
    "lat": 47.6062,
    "lon": -122.3321,
    "observed_at": "2026-10-24T18:00:00+00:00",
    "confidence": 0.92
  }
]
```

## POST /api/score

Scores a clicked map location. Request: `{ "lat": number, "lon": number }`
(WGS84). For the demo the click is resolved to the nearest of the MA city
datasets and scored against it; the clicked coordinates are stamped onto
the result and `label` names the matched site.

Response (abridged):

```json
{
  "location": { "lat": 42.33, "lon": -71.1 },
  "site_score": 39,
  "e_final": 38.5,
  "grade": "F",
  "grade_label": "Not recommended",
  "confidence_band": 13.3,
  "data_confidence": 33.7,
  "subscores": { "S_H": 70.5, "S_K": 40.4, "S_C": 88.0, "S_Cb": 0.0, "S_L": 0.9, "S_G": 40.0 },
  "categories": { "E_eco": 63.1, "E_climate": 0.0, "E_site": 20.5 },
  "species": [ { "species": "beaver", "risk": 0.676, "reason": "...", "confidence": "medium", "applicable": true } ],
  "flags": [],
  "mitigation": ["..."],
  "coverage": "national+MA",
  "data_sources": ["NLCD", "..."]
}
```

The frontend reads `site_score`, `grade`, `grade_label`, `data_confidence`,
and `confidence_band` for the side panel.

## POST /api/report

Returns a detailed, scientific Markdown report for a location, which the
frontend renders into a downloadable PDF. Request: `{ "lat": number, "lon": number }`.

```json
{
  "location": { "lat": 42.33, "lon": -71.1 },
  "markdown": "# Environmental Impact Report\n\n..."
}
```

## Conventions

- All timestamps are UTC, ISO 8601.
- Coordinates are WGS84 decimal degrees.
- A sighting's `confidence` is a float in `[0, 1]`; the site-level
  `data_confidence` (Q) is a separate `0–100` measure.
- Breaking changes bump the `version` field and this doc.
