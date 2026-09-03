# F055 — Calendar App harness

Feature-gated tests for `F055`. Keep test code in this directory.

- Gate: `F055_FEATURE`
- Targeted: `cargo xtask test-feature F055`
- Full: `cargo xtask test-all`
- Fixtures: `testing/fixtures/calendar_app.rs` (tenants A and B, a calendar-editor, a read-only viewer, a user denied on one source, workspace `Delivery`, two source sheets and one F013 view with date and datetime columns, a 100,000-row generator across 20 sources, publications in active, revoked, and expired states, fixed clock `2026-09-03T00:00:00Z`).
- Timezone fixtures: `api/fixtures/dst/` covering the Europe/London spring gap, the America/New_York autumn overlap, and a zone with a non-hour offset.
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
