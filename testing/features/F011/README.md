# F011 — Dates and schedules harness

Feature-gated tests for `F011`. Keep test code in this directory.

- Gate: `F011_FEATURE`
- Targeted: `cargo xtask test-feature F011`
- Full: `cargo xtask test-all`
- Fixture: `testing/fixtures/schedules.rs` (tenants A and B, `Standard` and `Berlin` calendars with 12 holidays, a sheet with start/end/duration/milestone columns and 50 rows, fixed clock `2026-09-03T00:00:00Z`)
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
