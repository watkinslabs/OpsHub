# F010 — Search/import/export harness

Feature-gated tests for `F010`. Keep test code in this directory.

- Gate: `F010_FEATURE`
- Targeted: `cargo xtask test-feature F010`
- Full: `cargo xtask test-all`
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
- Shared fixtures: `testing/fixtures/dataio.rs` (tenants A and B, `Plan` and restricted `Payroll` sheets, `plan.csv`, `plan.xlsx`, 100,000-row and 1,000,000-document generators); worker kill switch from `testing/harness/worker.rs`; MinIO prefix per worker.
