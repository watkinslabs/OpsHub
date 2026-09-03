# F032 — Project health/governance harness

Feature-gated tests for `F032`. Keep test code in this directory.

- Gate: `F032_FEATURE`
- Targeted: `cargo xtask test-feature F032`
- Full: `cargo xtask test-all`
- Fixture: `testing/fixtures/governance.rs` seeds tenant A (portfolio-admin, approver, sheet-editor, sheet-viewer), tenant B, a provisioned project with a baseline 15 days behind, 10 percent budget overrun and two open risk rows, a template version with three gates, a tenant-default health model (weights 40/30/10/10/10), a `project_intake` approval policy, and a 1,000-project generator for the nightly benchmark.
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
