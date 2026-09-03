# F031 — Portfolio rollups harness

Feature-gated tests for `F031`. Keep test code in this directory.

- Gate: `F031_FEATURE`
- Targeted: `cargo xtask test-feature F031`
- Full: `cargo xtask test-all`
- Fixture: `testing/fixtures/portfolios.rs` seeds tenant A (portfolio-admin, portfolio-viewer with an explicit deny on project "Merger"), tenant B, three F015-provisioned projects with baselines, and a 500-project generator for the performance lane.
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
