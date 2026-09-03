# F009 — Hierarchy and links harness

Feature-gated tests for `F009`. Keep test code in this directory.

- Gate: `F009_FEATURE`
- Targeted: `cargo xtask test-feature F009`
- Full: `cargo xtask test-all`
- Fixture: `testing/fixtures/links.rs` (tenant A `Plan` 3-level tree with `Cost`, `Status`, `Effort`, `Vendor` link column; `Vendors` sheet; tenant B `Foreign`)
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
