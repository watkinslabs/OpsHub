# F013 — Views harness

Feature-gated tests for `F013`. Keep test code in this directory.

- Gate: `F013_FEATURE`
- Targeted: `cargo xtask test-feature F013`
- Full: `cargo xtask test-all`
- Fixture: `testing/fixtures/views.rs` seeds a sheet with `Status` select, `Due` date, `Start`/`End` datetime columns, 200 rows (one restricted group, one weekly recurrence), an owner, editor, viewer, group of two, foreign tenant, and one saved view per kind; clock fixed at `2026-09-03T00:00:00Z`, sheet timezone `America/New_York`.
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
