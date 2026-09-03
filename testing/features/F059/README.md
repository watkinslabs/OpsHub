# F059 — Publishing/embedding harness

Feature-gated tests for `F059`. Keep test code in this directory.

- Gate: `F059_FEATURE`
- Targeted: `cargo xtask test-feature F059`
- Full: `cargo xtask test-all`
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
- Fixtures: `testing/fixtures/publishing.rs` (publisher, non-publisher, foreign tenant, view with hidden columns over 10,000 rows, report, 12-widget dashboard), fixed token RNG seed and client-hash salt, Playwright origins `https://host.test` and `https://evil.test`.
