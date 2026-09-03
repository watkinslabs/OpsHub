# F012 — Dependencies and Gantt harness

Feature-gated tests for `F012`. Keep test code in this directory.

- Gate: `F012_FEATURE`
- Targeted: `cargo xtask test-feature F012`
- Full: `cargo xtask test-all`
- Fixture: `testing/fixtures/dependencies.rs` seeds a sheet with F011 schedule settings (Mon–Fri calendar, one holiday exception), 12 rows including one parent and one milestone, and 9 dependencies covering FS, SS, FF, and SF.
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
