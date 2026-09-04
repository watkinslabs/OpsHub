# F071 — Migration import harness

Feature-gated tests for `F071`. Keep test code in this directory.

- Gate: `F071_FEATURE`
- Targeted: `cargo xtask test-feature F071`
- Full: `cargo xtask test-all`
- Fixtures: `testing/fixtures/migration.rs` (tenants A and B, a sheet-editor, a viewer, a commenter, destination folder `Delivery`, one already-committed migration, and a fixed clock `2026-09-03T00:00:00Z`).
- Generated sources: `testing/harness/workbooks/` builds `q3-delivery.xlsx` (12 tabs, all twelve column shapes, an AutoFilter, a 6-sort state, grouped rows, a resolvable cross-tab reference, a cross-workbook reference, an unsupported formula function, a conditional format, a 30 MB embedded attachment), `smartsheet-export.zip`, `airtable-base.zip`, a 50-tab workbook, a 51-tab workbook, a 120,000-row tab, a zip whose entries expand past 500 MB, and a zip with an entry path escaping the root. Every source is produced by the generator, never downloaded, and no lane opens a socket to Microsoft, Google, Smartsheet, or Airtable.
- Object storage: one MinIO prefix per test worker under `tenant_id/migrations/<migration_id>/`; one schema per worker.
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
