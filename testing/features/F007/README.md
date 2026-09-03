# F007 — Typed columns harness

Feature-gated tests for `F007`. Keep test code in this directory.

- Gate: `F007_FEATURE`
- Targeted: `cargo xtask test-feature F007`
- Full: `cargo xtask test-all`
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
- Fixture: `testing/fixtures/columns.rs` seeds one column per type, 20 select options, and 500 rows with mixed valid and invalid values; the performance lane adds a 500-column sheet and a 100,000-row sheet.
