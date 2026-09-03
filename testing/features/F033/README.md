# F033 — Resources/capacity harness

Feature-gated tests for `F033`. Keep test code in this directory.

- Gate: `F033_FEATURE`
- Targeted: `cargo xtask test-feature F033`
- Full: `cargo xtask test-all`
- Fixture: `testing/fixtures/resources.rs` seeds tenant A (resource-admin, resource-viewer, a linked user), tenant B, a Mon–Fri 8 h working calendar with a holiday on `2026-10-12`, resources "Ana" (FTE 0.5) and "Ben" (FTE 1.0) with skills, a leave week `2026-10-05` to `2026-10-09`, cost rates, a project sheet with rows, and generators for 200 allocations over 52 weeks and 5,000 resources.
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
