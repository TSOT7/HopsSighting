# Requirements: Sightings MVP

## Introduction

Hour 1 proved the frontend/backend pipe with a single hard-coded sighting. The
Sightings MVP turns HopsSighting into something usable: contributors can submit
a real sighting, it gets scored and persisted, and everyone sees all sightings
on an interactive map with a detail view. This is the first end-to-end user
journey described in the product steering.

## Requirements

### Requirement 1: Submit a sighting

**User story:** As a contributor, I want to record a hops sighting with its
species, location, and time, so that it becomes part of the shared map.

#### Acceptance criteria

1. WHEN a contributor submits species, latitude, longitude, and observed time
   THEN the system SHALL create a sighting that conforms to the `Sighting`
   shape in the API contract.
2. WHEN latitude is outside [-90, 90] or longitude outside [-180, 180] THEN the
   system SHALL reject the submission with a 422 and a clear message.
3. WHEN species is empty or missing THEN the system SHALL reject the submission
   with a 422.
4. WHEN observed time is missing THEN the system SHALL default it to the
   current UTC time.
5. WHEN a sighting is created THEN the system SHALL assign it a stable unique
   id and return the created object.

### Requirement 2: Score a sighting's confidence

**User story:** As a researcher, I want each sighting to carry a confidence
score, so that I can weigh reports by how reliable they are.

#### Acceptance criteria

1. WHEN a sighting is created THEN the system SHALL compute a confidence value
   in [0, 1].
2. WHEN required detail is sparse THEN the score SHALL be lower than when
   detail is rich (scoring is deterministic for the same input).
3. WHEN the scoring rules change THEN existing stored sightings SHALL keep the
   score assigned at creation time (no silent re-scoring).

### Requirement 3: Persist sightings

**User story:** As any user, I want sightings to survive a server restart, so
that the map is not wiped every time the backend restarts.

#### Acceptance criteria

1. WHEN a sighting is created THEN it SHALL be written to durable local storage.
2. WHEN the backend restarts THEN previously created sightings SHALL still be
   returned by the list endpoint.
3. WHEN storage is empty THEN the list endpoint SHALL return an empty array,
   not an error.

### Requirement 4: Browse sightings on a map

**User story:** As any user, I want to see all sightings as markers on a map,
so that I can understand where species are being reported.

#### Acceptance criteria

1. WHEN the app loads THEN it SHALL fetch all sightings and render each as a map
   marker at its coordinates.
2. WHEN a user selects a marker THEN the app SHALL open a report view showing
   species, time, coordinates, and confidence.
3. WHEN the backend is unreachable THEN the app SHALL show a clear, non-fatal
   error state rather than a blank page.

### Requirement 5: Keep the contract honest

**User story:** As a developer, I want the API contract to always match the
code, so that the two halves of the team never drift.

#### Acceptance criteria

1. WHEN an endpoint or the `Sighting` shape changes THEN `docs/api-contract.md`
   SHALL be updated in the same change.
2. WHEN a new endpoint is added THEN it SHALL live under `/api/...`.
