# F025 — Export/drill-through harness

Feature-gated tests for `F025`. Keep test code in this directory.

- Gate: `F025_FEATURE`
- Targeted: `cargo xtask test-feature F025`
- Full: `cargo xtask test-all`
- Fixtures: `testing/fixtures/report_exports.rs` (tenants A and B; actors `exporter` with report-viewer plus resource-exporter, `viewer`, `restricted` without read on sheet "Risks", `tenant-admin`, and a share-link guest; report "Portfolio status" with a 100,000-row snapshot, hidden column `Budget.margin`, and an `aggregate_policy: owner` variant; a 250,000-row generator; dashboard "Weekly review" with 12 widgets including one the viewer cannot read; fixed clock `2026-09-03T00:00:00Z`, timezone `America/New_York`, seed `0x0F25`).
- Stubs: JetStream stub for `report-exports.render`; MinIO prefix per worker with an injectable failing sink; deterministic PDF and PNG renderer asserting the internal print route URL and the service token bound to `scope_key`.
- Lanes: `requirements/` (traceability for FR-F025-01..13 and NFR-F025-01..04), `api/` (drill, export, render, download, permission, byte-level scope), `database/` (migration and constraints on `report_exports`), `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
