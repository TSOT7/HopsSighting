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
    serve.py          # tiny static server (Python stdlib, no Node/Deno)
  docs/
    api-contract.md   # shared JSON contract between front/back
  .gitignore
  README.md
```

## Prerequisites

- Python 3.11+ (tested on 3.14) — that's it.

> No Node or Deno required. The frontend is a static page served by Python's
> built-in HTTP server, so anyone who can run the backend can run the frontend.
> When we move to a real UI framework (React/Vite) we'll install Node then; the
> API contract won't change.

## Run it (two terminals)

Each step below is one command per line. Don't paste the `#` comments — the
shell treats `#` as the start of a comment and it can break the line.

### 1. Backend — FastAPI on :8080

First time only (create the env and install deps):

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Every time (start the server):

```bash
cd backend
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
```

Check it in a browser or with curl (note: `/` returns 404, use `/api/...`):

```bash
curl http://localhost:8080/api/health
curl http://localhost:8080/api/sightings
```

### 2. Frontend — static page on :8000

```bash
cd frontend
python3 serve.py
```

Open http://localhost:8000 — you should see the backend status and one sample
sighting rendered from live JSON.

To stop either server, press `Ctrl+C` in its terminal.

## API contract

See [docs/api-contract.md](docs/api-contract.md). Two endpoints for now:
`GET /api/health` and `GET /api/sightings`.
