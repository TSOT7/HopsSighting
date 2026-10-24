# HopsSighting

A map-based app for logging and scoring hops sightings.

## Structure

```
HopsSighting/
  backend/
    app/              # FastAPI routes, scoring, species modules
      main.py         # hello-world API (health + sightings)
    data/             # cached layers (gitignored)
    requirements.txt
    .venv/            # local Python env (gitignored)
  frontend/
    src/              # map, side panel, report view
      index.html      # hello-world page that calls the backend
    deno.json         # dev task
  docs/
    api-contract.md   # shared JSON contract between front/back
  .gitignore
  README.md
```

## Prerequisites

- Python 3.11+ (tested on 3.14)
- [Deno](https://deno.com/) 2.x (used to serve the frontend; no Node required)

> Node/npm aren't installed in this environment, so the frontend is a static
> page served by Deno. To switch to a React/Vite setup later, install Node and
> replace `frontend/` with a Vite project — the API contract stays the same.

## Run it (two terminals)

### 1. Backend — FastAPI on :8080

```bash
cd backend
python3 -m venv .venv            # first time only
.venv/bin/pip install -r requirements.txt   # first time only
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
```

Check it:

```bash
curl http://localhost:8080/api/health
curl http://localhost:8080/api/sightings
```

### 2. Frontend — static page on :8000

```bash
cd frontend
deno task dev
```

Open http://localhost:8000 — you should see the backend status and one sample
sighting rendered from live JSON.

## API contract

See [docs/api-contract.md](docs/api-contract.md). Two endpoints for now:
`GET /api/health` and `GET /api/sightings`.
