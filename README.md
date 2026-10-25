# HopsSighting

**HopsSighting is a climate-tech platform that uses interactive GIS mapping, biodiversity risk assessment, and environmental impact scoring to help identify sustainable locations for clean energy projects — solar farms, wind installations, and community microgrids — while minimizing ecological harm.**

CClean energy development faces a “green vs. green” dilemma: projects designed to fight climate change can unintentionally harm the ecosystems they're meant to protect. When ecological conflicts are discovered late, projects can face costly delays, redesigns, or cancellations.

HopsSighting (EcoScribe) tackles this problem early, helping developers, planners, and communities assess potential clean energy sites before the permitting stage. With a single map click, users receive a 0–100 environmental impact score, an A–F grade, biodiversity risk insights, and a detailed site assessment report.

Built for the **Hackachusetts hackathon** — Climate Tech & Clean Energy track.

## 🎥 Demo Video

[![Watch the HopsSighting Demo](https://img.youtube.com/vi/7c3X2uZRYbA/maxresdefault.jpg)](https://www.youtube.com/watch?v=7c3X2uZRYbA)

---

## Features & Functionality

### Interactive GIS Map
A Leaflet map centred on Massachusetts with the MassGIS 2016 land cover layer overlaid — showing forested, suburban, and developed land in real colour. Click any location to draw a hexagonal siting zone and instantly screen it for clean energy development suitability. Named city markers with hover tooltips provide geographic orientation. Zoom in for street-level detail, zoom out for regional comparison.

### Environmental Impact Scoring Engine
A pure-Python engine computes six ecological sub-scores for the selected clean energy site and combines them into an overall 0–100 rating with an A–F grade:

| Factor | What it measures |
|---|---|
| **Habitat integrity** | Quality and intactness of native habitat — canopy cover, wetlands, invasive species absence |
| **Keystone species risk** | Observed or modelled presence of beaver, bats, and native pollinators whose loss cascades through the ecosystem |
| **Connectivity** | How well the zone connects to adjacent habitat patches, enabling wildlife movement and genetic exchange |
| **Carbon & climate** | Carbon sequestration potential of existing vegetation, soil, and wetland cover at the proposed clean energy site |
| **Land reuse** | How much previously disturbed or developed land is available — rewards siting clean energy on brownfields over untouched habitat |
| **Regulatory** | Proximity to protected areas, conservation restrictions, and regulatory buffer zones that could affect clean energy permitting |

The score is gated by hard regulatory triggers and shrunk toward a conservative prior when data confidence is low — so missing data never produces a falsely favourable score for a clean energy project.

### Plain-Language Results
Every score comes with a readable breakdown, a species-risk table with individual confidence levels, active regulatory flags, and concrete mitigation suggestions (buffer zones, seasonal construction windows, acoustic monitoring).

### Inline Help System
Every metric and factor has a `?` icon that explains what it means in plain language on hover — no GIS background required to interpret the clean energy siting results.

### Downloadable PDF Report
A detailed executive report explaining how the rating was computed — including the factor breakdown, species risk table, spatial metrics, and mitigation recommendations — generated client-side and exported as a PDF for sharing with stakeholders and permitting bodies.

### Live Land Cover Overlay
MassGIS Land Use 2016 WMS layer rendered directly on the map, showing where forested, suburban, and developed land sits relative to a proposed clean energy site — at any zoom level.

### Location Saving & Comparison
Save and bookmark multiple siting zones with beaver-marker pins. Revisit and compare saved locations from the side panel to find the optimal clean energy site across a region.

> **Note on data:** The demo scores each location against the nearest of 14 prefilled Massachusetts city datasets. A live mode pulls species and survey data from public APIs (GBIF, iNaturalist). Scoring weights are provisional and pending calibration — this is a screening tool, not a substitute for a permit review or a qualified ecologist.

---

## How Kiro was used

This project was built entirely inside the Kiro IDE using Autopilot mode throughout.

### Spec-driven development
The Sightings MVP feature was planned using Kiro's Spec workflow before a single line was written: `requirements.md` captured EARS-style acceptance criteria, `design.md` covered architecture and the scoring algorithm, and `tasks.md` produced an ordered, requirement-linked implementation plan. Each code change traces back to a numbered criterion rather than emerging from ad-hoc vibe coding. The spec forced early decisions about the API contract (`docs/api-contract.md`) that kept the frontend and backend in sync without rework.

### Steering docs
Three always-on steering files in `.kiro/steering/` kept Kiro aligned with project conventions across every session — no re-explaining the stack, route structure, or design system:
- `product.md` — what HopsSighting is, the challenge track, and core user journeys.
- `tech.md` — stack, conventions, run commands, and a live reference to the API contract via `#[[file:docs/api-contract.md]]` so Kiro always had the current schema in context.
- `structure.md` — where new code and features belong in the repo.

### Agent hooks
A `PostFileSave` hook in `.kiro/hooks/backend-test-on-save.json` automatically runs the pytest suite whenever a Python file under `backend/` is saved. This tightened the feedback loop significantly — test failures surfaced immediately rather than at the end of a work session.

### Vibe coding for the frontend
The interactive map, hexagon drawing system, city markers, MassGIS WMS integration, PDF export, inline help tooltips, and the organic-editorial design system were all built through iterative conversation with Kiro in Autopilot mode. Kiro read existing code before every edit, matched the project's conventions, and verified changes — closer to pair programming than prompt-and-paste.

### What made the biggest difference
The combination of steering docs + spec was the highest-leverage move. Steering meant Kiro never forgot the project's constraints (no Node, UTC timestamps, `/api` prefix). The spec meant the scoring engine was designed before it was coded, catching edge cases — the conservative prior for low-confidence data, the hard regulatory gate — that would have been painful to retrofit.

---

## Tech Stack

### Frontend
| Layer | Technology |
|---|---|
| Map engine | [Leaflet](https://leafletjs.com/) 1.9.4 |
| Basemap | Esri World Topo (free, no key) |
| Land cover overlay | MassGIS Land Use 2016 WMS |
| State boundary | PublicaMundi US States GeoJSON |
| Geospatial math | [Turf.js](https://turfjs.org/) 6 |
| PDF export | [jsPDF](https://github.com/parallax/jsPDF) 2.5 |
| Fonts | Inter + Playfair Display (Google Fonts) |
| Runtime | Plain HTML/CSS/JS — no build step, no framework |
| Static server | Python stdlib `http.server` via `serve.py` |

### Backend
| Layer | Technology |
|---|---|
| API framework | [FastAPI](https://fastapi.tiangolo.com/) |
| Server | [Uvicorn](https://www.uvicorn.org/) (ASGI) |
| Data validation | [Pydantic](https://docs.pydantic.dev/) v2 |
| Geospatial data | MassGIS datasets (forested, suburban, developed JSON) |
| Species data | GBIF + iNaturalist public APIs |
| Runtime | Python 3.11+ |

### Design System
- Organic-editorial palette: forest sage, soft moss, warm terracotta, espresso charcoal
- Responsive two-panel layout: full-height map canvas + floating side panel
- Print-optimised styles for executive PDF reports

---

## Structure

```
HopsSighting/
  .kiro/
    steering/         # always-on project context
    specs/            # structured feature specs (requirements/design/tasks)
    hooks/            # automated agent workflows
  backend/
    app/              # FastAPI routes, scoring engine, species modules
    datasets/         # prefilled MA city datasets (forested/suburban/developed)
    tests/            # pytest suite
    requirements.txt
  frontend/
    src/index.html    # the full web app (map, side panel, PDF export)
    serve.py          # Python stdlib static server
  docs/
    api-contract.md   # shared JSON contract between front and back
  README.md
```

## Prerequisites

- Python 3.11+ — that's it.

> No Node or Deno required. The frontend is a static page served by Python's built-in HTTP server.

## Run it (two terminals)

### 1. Backend — FastAPI on :8080

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
```

### 2. Frontend — static page on :8000

```bash
cd frontend
python3 serve.py
```

Open http://localhost:8000

## API contract

See [docs/api-contract.md](docs/api-contract.md) — the source of truth for all endpoints. Key routes: `GET /api/health`, `GET /api/sightings`, `POST /api/score`, `POST /api/report`.
