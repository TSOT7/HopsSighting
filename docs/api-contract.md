# HopsSighting API Contract (v0.1.0)

The shared agreement between backend (FastAPI) and frontend. Hour 1 scope:
two endpoints, one JSON shape.

Base URL (dev): `http://localhost:8080`

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

## Conventions

- All timestamps are UTC, ISO 8601.
- Coordinates are WGS84 decimal degrees.
- `confidence` is a float in `[0, 1]`.
- Breaking changes bump the `version` field and this doc.
