# F015 — Templates and baselines harness

Feature-gated tests for `F015`. Keep test code in this directory.

- Gate: `F015_FEATURE`
- Targeted: `cargo xtask test-feature F015`
- Full: `cargo xtask test-all`
- Fixture: `testing/fixtures/templates.rs` (tenants A and B, portfolio admin, editor, viewer, workspace `Ops`, a custom 120-row/34-dependency manifest, a 500-row load manifest, a failing-dependency manifest, a sheet with 50 scheduled rows and effort/cost columns, fixed clock `2026-09-03T00:00:00Z`)
- Worker: provisioning jobs run in-process through `testing/harness/worker.rs` with an in-memory JetStream recorder
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
