# F003 — Authorization and audit harness

Feature-gated tests for `F003`. Keep test code in this directory. The negative matrix in `api/negative_matrix.rs` is imported by every later feature harness.

- Gate: `F003_FEATURE`
- Targeted: `cargo xtask test-feature F003`
- Full: `cargo xtask test-all`
- Fixture: `AuthzFixture::seed(db)` layers a synthetic `tenant → workspace → folder → sheet` ancestry resolver, role `Reviewer`, bindings for every system role, a guest principal, and 1,000 audit rows across two partitions over the F002 and F038 fixtures; clock fixed at `2026-09-03T00:00:00Z`.
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
