# F057 — DAM assets harness

Feature-gated tests for `F057`. Keep test code in this directory.

- Gate: `F057_FEATURE`
- Targeted: `cargo xtask test-feature F057`
- Full: `cargo xtask test-all`
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
- Fixtures: `testing/fixtures/assets.rs` (entitled and unentitled tenants, 20 clean files, one quarantined file, 5-field metadata schema, 3-level collection tree, 200,000-asset generator), `RenditionBackend` fake, MinIO bucket prefix per worker.
