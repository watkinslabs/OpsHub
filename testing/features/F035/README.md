# F035 — Formula engine harness

Feature-gated tests for `F035`. Keep test code in this directory.

- Gate: `F035_FEATURE`
- Targeted: `cargo xtask test-feature F035`
- Full: `cargo xtask test-all`
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
- Fixtures: `testing/fixtures/formulas.rs` builds sheets `Plan` (200 rows, 3-level hierarchy) and `Rates` (20 rows), formula columns `Total`, `Weighted`, `RateLookup`, and a fixed clock `2026-09-03T00:00:00Z` injected into `TODAY`/`NOW`.
