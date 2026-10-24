# Implementation Plan: Sightings MVP

- [ ] 1. Extract models into `app/models.py`
  - Define `SightingIn` (species, lat, lon, optional observed_at) and `Sighting`
    (adds id, confidence) with lat/lon bounds validation.
  - Update `main.py` to import from the new module.
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ] 2. Implement deterministic scoring in `app/scoring.py`
  - Pure `score(sighting_in) -> float` returning a value clamped to [0, 1].
  - _Requirements: 2.1, 2.2_

- [ ] 3. Implement file-backed store in `app/store.py`
  - `list_all()` and `add(sighting)` over `backend/data/sightings.json`;
    tolerate a missing/empty file as an empty list.
  - _Requirements: 3.1, 3.2, 3.3_

- [ ] 4. Add `POST /api/sightings` and update `GET /api/sightings`
  - POST validates, scores, mints id, persists, returns the created object.
  - GET returns all stored sightings (empty array when none).
  - _Requirements: 1.1, 1.5, 3.2, 3.3, 5.2_

- [ ] 5. Update the API contract
  - Document `POST /api/sightings`, the `SightingIn` shape, and the 422 cases
    in `docs/api-contract.md`.
  - _Requirements: 5.1_

- [ ] 6. Render sightings on a Leaflet map (frontend)
  - Add Leaflet via CDN; one marker per sighting; non-fatal error banner.
  - _Requirements: 4.1, 4.3_

- [ ] 7. Add the report view on marker select
  - Clicking a marker opens a panel with species, time, coords, confidence.
  - _Requirements: 4.2_

- [ ] 8. Add the submit-a-sighting form
  - Form POSTs a new sighting then refreshes markers.
  - _Requirements: 1.1_

- [ ] 9. Tests
  - Unit + property-based tests for scoring (range, determinism); store
    round-trip; one TestClient test per endpoint.
  - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2_
