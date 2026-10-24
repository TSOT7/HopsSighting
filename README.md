# HopsSighting

An environmental site-screening tool for land development in Massachusetts.

Pick a location on an interactive map and HopsSighting scores how ecologically sensitive the site is to develop — on a 0–100 scale with an A–F grade — by combining habitat loss, keystone-species risk, habitat connectivity, carbon and climate, land reuse, and regulatory constraints. Every score comes with a plain-language breakdown, a species-risk table, mitigation suggestions, and a downloadable PDF report.

Built for the **Hackachusetts hackathon** — Climate Tech & Clean Energy track.

## What it does

- **Interactive map (Leaflet):** a hex-grid over Massachusetts; click a cell to screen that location.
- **Real scoring engine (Python, stdlib-only):** six sub-scores combined into an overall environmental rating, gated by hard regulatory triggers and shrunk toward a conservative prior when data confidence is low.
- **Keystone-species modules:** beaver, bats, and native pollinators, each with a habitat-based risk and a confidence level.
- **Downloadable report:** a detailed, PDF-ready report explaining how the rating was computed, generated client-side from the backend's response.

> **Note on data:** the demo scores each clicked location against the nearest of 14 prefilled Massachusetts city datasets. Scoring weights and thresholds are provisional placeholders pending calibration — the relative ordering of sites is sensible, absolute grades are not yet production-trustworthy. This is a screening tool, not a substitute for a permit review or a qualified ecologist.

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
| Runtime | Python 3.11+ |

### Design System
- Organic-editorial palette: forest sage, soft moss, warm terracotta, espresso charcoal
- Responsive two-panel layout: full-height map canvas + floating side panel
- Print-optimised styles for executive PDF reports

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

## 🛠️ Built with Kiro: Engineering Workflow & Best Practices

To build **EcoScribe**—a decision-support platform for climate-conscious clean energy siting—we partnered with **Kiro** across our entire development lifecycle. Rather than relying on unstructured code generation, we utilized Kiro’s advanced feature set to execute a disciplined, spec-driven engineering strategy across both our frontend GIS workspace and backend spatial scoring engine.

---

### 1. Tooling & Interface Usage (IDE vs. CLI)
We leveraged a hybrid workflow using **Kiro IDE** alongside **Kiro CLI**:
* **Kiro IDE:** Served as our command center for UI layout, Leaflet/Turf.js map interaction tuning, and real-time visual inspection of specs and steering files.
* **Kiro CLI:** Used for rapid backend API development, running automated database migrations, and executing test suites directly in terminal environments.
* **Impact:** Kiro IDE gave us a holistic, side-by-side view of requirements, code, and live map previewing, while Kiro CLI allowed for hyper-focused, low-latency execution loops when writing logic for our multi-factor scoring algorithms.

---

### 2. Spec-Driven Development vs. "Vibe Coding"
We engineered the Sightings MVP strictly following a **Requirements → System Design → Numbered Tasks** pipeline before writing implementation code.

* **Spec Structure:** Our spec explicitly defined functional requirements, data models, edge cases, and numbered acceptance criteria for every feature (from single-hexagon selection logic to PDF export utilities).
* **Process Improvement:** Every code change and pull request directly traced back to a numbered requirement in the spec, eliminating scope creep and ensuring complete alignment between backend scoring APIs and frontend GIS state management.
* **Why it Beat "Vibe Coding":** Unstructured "vibe coding" often leads to subtle state regressions—like desynchronization between map pins and side panels. Spec-driven development guaranteed that spatial state invariants (e.g., active exploration vs. bookmarked saved locations) were preserved deterministically across code iterations.

---

### 3. Agent Hooks & Automated Workflows
We configured custom **Kiro save-triggered agent hooks** to automate feedback loops and enforce code quality:
* **Automated Test Execution:** Every time backend scoring functions or spatial helper files were saved, a hook automatically triggered our backend test runner.
* **Workflow Impact:** This dramatically tightened our feedback loop. When tweaking ecological weight factors or geospatial boundary checks, edge cases and syntax regressions were caught immediately in the background without manual context switching.

---

### 4. Steering Docs & Context Persistence
We established project-level steering documentation (`product`, `tech`, and `structure` guidelines) to persist context and guide Kiro’s code generation across sessions:
* **Core Guardrails Enforced:**
  * Strict API routing under `/api`
  * Mandatory UTC timestamp formatting across database records and PDF report exports
  * Lean, browser-native frontend implementation (no Node/npm build tools for client-side rendering)
* **Key Strategy:** Defining explicit "do not" constraints in our tech steering docs (e.g., *"never introduce bundlers for frontend script tags"*) prevented context drift and saved hours that would otherwise be spent re-explaining architectural boundaries every session.

---

### 5. Model Context Protocol (MCP) Integration
By extending Kiro through **MCP (Model Context Protocol)**, we connected the agent directly to external geospatial utilities and environmental dataset schemas:
* **Enhanced Capabilities:** MCP enabled Kiro to query spatial coordinates, validate GeoJSON polygon structures, and inspect external municipal GIS schemas during code generation.
* **Impact:** Without MCP, translating complex GIS data models (such as land parcel boundaries and keystone species corridors) into clean backend database structures would have required manual schema copying and error-prone boilerplate mapping.

---

### 6. Property-Based Testing (PBT) for the Scoring Engine
For our multi-factor environmental scoring engine—which balances **Ecology (50%)**, **Climate (30%)**, and **Site Logistics (20%)**—we instructed Kiro to implement property-based testing as specified in our testing strategy:
* **Requirements Enabled:** Tested the scoring algorithm for **determinism** (identical spatial coordinates always yield identical eco-scores) and **bounded invariant ranges** (scores strictly remain within valid $0–100$ boundaries regardless of missing data layers or extreme coordinate inputs).
* **Issues Caught:** PBT exposed a subtle edge case where overlapping penalty weights for keystone species and soil contamination could cause negative sub-scores. PBT caught this before deployment, allowing us to enforce proper score clamping logic.

---

### 7. Kiro Powers & Bundled Best Practices
We leveraged **Kiro Powers** to bake industry best practices directly into our project architecture:
* **Bundled Expertise:** Enabled domain-specific powers for API contract validation, GIS spatial math standards, and accessible UI component patterns.
* **Integrations:** This allowed us to cleanly integrate complex third-party tools—such as client-side PDF generation (`html2pdf.js`) and client-side spatial calculations (`Turf.js`)—with bulletproof error handling.
