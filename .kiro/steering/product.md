# Product

HopsSighting is a map-based web app for logging, verifying, and scoring
sightings of hops (Humulus lupulus) and related plant species in the wild.

## Why it matters

Wild hops and the plants around them are indicators of local ecosystem health
and land-use change. Crowd-sourced sightings, scored for confidence and mapped
over time, give researchers and community members a living picture of where
species are spreading, declining, or being displaced.

## Hackathon context

- Event: Hackachusetts
- Challenge track: Climate Tech & Clean Energy (biodiversity / ecosystem
  monitoring angle). Revisit if we pivot toward Civic Action.
- The project must demonstrably be built with Kiro. The `.kiro/` directory is
  part of the submission and must stay out of `.gitignore`.

## Core user journeys

1. A contributor drops a sighting on the map with species, location, and time.
2. The backend scores the sighting's confidence.
3. Anyone can browse sightings on the map and open a report view for detail.

## Current state (Hour 1)

- Backend: FastAPI hello-world with `/api/health` and `/api/sightings`.
- Frontend: static page served by Python stdlib that renders live JSON.
- Shared JSON contract agreed in `docs/api-contract.md`.
