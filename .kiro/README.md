# .kiro — How HopsSighting uses Kiro

This directory is part of the Hackachusetts submission and documents how the
project was built with Kiro. It is intentionally committed (not gitignored).

## Contents

- `steering/` — always-on context Kiro reads on every interaction:
  - `product.md` — what HopsSighting is, the challenge track, user journeys.
  - `tech.md` — stack, conventions, run commands, and a reference to the shared
    API contract via `#[[file:docs/api-contract.md]]`.
  - `structure.md` — where code and new features belong.
- `specs/sightings-mvp/` — spec-driven development for the next feature:
  `requirements.md` (EARS-style acceptance criteria), `design.md`
  (architecture, scoring, testing strategy), and `tasks.md` (an ordered,
  requirement-linked implementation plan).
- `hooks/` — automated workflows:
  - `backend-test-on-save.json` — runs the backend test suite when a backend
    Python file is saved.

## How Kiro was used (notes for the write-up)

- Spec-driven development: the Sightings MVP was planned as requirements →
  design → tasks before implementation, so each code change traces back to a
  numbered acceptance criterion rather than ad-hoc vibe coding.
- Steering: product/tech/structure docs keep Kiro aligned with our conventions
  (routes under `/api`, UTC timestamps, no-Node frontend) without re-explaining
  them each session.
- Hooks: a save-triggered test run tightens the feedback loop on the backend.
- Property-based testing is called out in the spec's testing strategy for the
  scoring function (range + determinism).
