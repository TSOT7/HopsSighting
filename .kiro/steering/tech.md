# Tech & Conventions

## Stack

- Backend: Python 3.11+ with FastAPI + Uvicorn. Pydantic models for all
  request/response shapes.
- Frontend: static HTML/JS served during dev by `frontend/serve.py` (Python
  stdlib). No Node or Deno required so every teammate can run it. We'll move to
  a framework (React/Vite) only when the UI justifies it; the API contract
  stays stable across that change.
- No database yet. Sightings are hard-coded until we add persistence.

## Running locally

- Backend: `cd backend && .venv/bin/uvicorn app.main:app --port 8080 --reload`
- Frontend: `cd frontend && python3 serve.py` then open http://localhost:8000

## Conventions

- All API routes live under `/api/...`. The root `/` is intentionally not a
  route on the backend.
- Timestamps are ISO 8601 UTC. Coordinates are WGS84 decimal degrees.
- `confidence` is a float in `[0, 1]`.
- The shared request/response contract lives in `docs/api-contract.md` and is
  the source of truth for both sides. Update it in the same change as any API
  change.
- Keep CORS scoped to known dev origins; widen only deliberately.

## API contract reference

#[[file:docs/api-contract.md]]
