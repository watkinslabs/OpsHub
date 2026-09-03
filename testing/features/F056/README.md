# F056 — Pivot App harness

Feature-gated tests for `F056`. Keep test code in this directory.

- Gate: `F056_FEATURE`
- Targeted: `cargo xtask test-feature F056`
- Full: `cargo xtask test-all`
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
- Fixtures: `testing/fixtures/pivots.rs` (entitled and unentitled tenants, 2,000-row sheet, report hiding 300 rows, 100,000-row generator) and `api/fixtures/golden_pivots.json`.
