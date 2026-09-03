# F014 — Forms harness

Feature-gated tests for `F014`. Keep test code in this directory.

- Gate: `F014_FEATURE`
- Targeted: `cargo xtask test-feature F014`
- Full: `cargo xtask test-all`
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
- Shared fixtures: `testing/fixtures/forms.rs` (tenant, 12-column sheet, form admin, submitter, foreign tenant, published 8-field form) and `testing/fixtures/forms/conditions.json` (64 evaluator cases run by both Rust and TypeScript).
- Public routes are exercised without a session; rate-limit buckets and the verification adapter stub are namespaced per test.
