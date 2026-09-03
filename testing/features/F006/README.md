# F006 — Sheets/boards/items harness

Feature-gated tests for `F006`. Keep test code in this directory.

- Gate: `F006_FEATURE`
- Targeted: `cargo xtask test-feature F006`
- Full: `cargo xtask test-all`
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
