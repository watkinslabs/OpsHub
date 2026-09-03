# F008 — Grid editing harness

Feature-gated tests for `F008`. Keep test code in this directory.

- Gate: `F008_FEATURE`
- Targeted: `cargo xtask test-feature F008`
- Full: `cargo xtask test-all`
- Fixture: `testing/fixtures/grid.rs` (tenant, 12-column sheet, 500 rows, editor A, editor B, commenter, viewer, foreign tenant; 100,000-row generator for performance)
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
