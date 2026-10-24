# Project Structure

```
HopsSighting/
  .kiro/
    steering/         # always-on project context (this folder)
    specs/            # structured feature specs (requirements/design/tasks)
    hooks/            # automated agent workflows
  backend/
    app/
      main.py         # FastAPI app: routes, models
    data/             # cached layers (gitignored)
    requirements.txt
  frontend/
    src/index.html    # the web app UI
    serve.py          # Python stdlib static server
  docs/
    api-contract.md   # shared JSON contract
  README.md
```

## Where things go

- New API endpoints: `backend/app/` as focused modules, imported into `main.py`.
- New frontend views (map, side panel, report view): under `frontend/src/`.
- Any change to the API shape: update `docs/api-contract.md` in the same change.
- New multi-step features: author a spec under `.kiro/specs/` before building.
