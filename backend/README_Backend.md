# HopsSighting Backend

Three decoupled parts, joined by a JSON file on disk:

1. **Fetcher** (`app/fetch.py`) — pulls data for a location and writes a
   site-data JSON file.
2. **Scorer** (`app/score.py`) — reads a site-data JSON file and produces
   the environmental rating, grade, sub-scores, species breakdown, flags,
   and mitigation.
3. **Reporter** (`app/report.py`) — reads a site-data JSON file and
   produces a detailed, professional Markdown report that walks through
   the raw arithmetic behind every factor of the rating. The UI turns
   this Markdown into a downloadable PDF.

The file is the only coupling between them, so each can be built, run,
and debugged on its own. The scorer and reporter need nothing but the
standard library; only the fetcher's live mode uses the network.

The scoring math itself is documented in `../docs/scoring-model.md`.

## Setup

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Part 1 — fetch

Prefilled (what the demo runs on — no network):

```bash
.venv/bin/python -m app.fetch --prefilled forested -o datasets/forested.json
```

Live (hits GBIF + iNaturalist for sightings; GIS layers not fetched yet,
so confidence is low and honestly flagged):

```bash
.venv/bin/python -m app.fetch --live --lat 42.376 --lon -71.06 -o out.json
```

Available prefilled datasets: `forested`, `suburban`, `developed`
(all under `datasets/`).

## Part 2 — score

```bash
.venv/bin/python -m app.score datasets/forested.json          # human summary
.venv/bin/python -m app.score datasets/forested.json --json   # full JSON
.venv/bin/python -m app.score datasets/forested.json -o result.json
```

## Part 3 — detailed report

Generate the professional, PDF-ready Markdown report that explains the
rating with full plugged-in arithmetic for every factor:

```bash
.venv/bin/python -m app.report datasets/forested.json              # to stdout
.venv/bin/python -m app.report datasets/forested.json -o report.md # to a file
```

The report numbers are anchored to the same values the scorer computes,
so the shown arithmetic always matches the calculated result.

## The dataset schema

Defined in `app/schema.py` (`SiteData`). One JSON object per location
holding every "data input" from the scoring model (habitat fractions,
canopy area, transit distance, regulatory triggers, species sighting
counts, survey effort, data-layer availability, etc.) plus provenance
(label, coverage, sources, whether it was a live fetch).

`app/config.py` holds every tunable weight and parameter. All are
labelled `PLACEHOLDER` — relative ordering is sensible, absolute grades
need calibration.

## Tests

```bash
.venv/bin/python -m pytest
```

## Notes / limits (hackathon)

- Demo runs off the three prefilled datasets. Live mode currently
  fetches sightings only; the GIS raster pipeline (NLCD / NWI / NHD) is
  not wired in, so live-fetched sites score at low confidence by design.
- The FastAPI app (`app/main.py`) still serves `/api/health` and
  `/api/sightings`. Wiring the scorer behind an HTTP endpoint is a later
  step; for now scoring is CLI-only.
- All config numbers are placeholders pending calibration.
