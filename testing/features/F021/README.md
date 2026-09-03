# F021 — Cross-source reports harness

Feature-gated tests for `F021`. Keep test code in this directory.

- Gate: `F021_FEATURE`
- Targeted: `cargo xtask test-feature F021`
- Full: `cargo xtask test-all`
- Fixture: `testing/fixtures/reports.rs` (tenants A and B; editor, viewer, restricted viewer; sheets "Projects", "Risks", "Budget"; saved report "Portfolio status")
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
