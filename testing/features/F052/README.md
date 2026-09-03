# F052 — Data Shuttle harness

Feature-gated tests for `F052`. Keep test code in this directory.

- Gate: `F052_FEATURE`
- Targeted: `cargo xtask test-feature F052`
- Full: `cargo xtask test-all`
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
- Fixture: `testing/fixtures/data_shuttle.rs` (tenant A data-admin/editor/viewer, tenant B without entitlement, `data-shuttle` entitlement with `max_flows 3`, `max_rows_per_run 200000`, `max_file_mb 50`, `Budget` sheet, sample CSV/XLSX in MinIO, one flow with historical runs).
- External services: MinIO bucket prefix per test, JetStream subject `data-shuttle.run`, recorded connector `download` stub.
