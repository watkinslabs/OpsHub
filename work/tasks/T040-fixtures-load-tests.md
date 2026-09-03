---
id: T040
type: task
status: planned
parent_epic: E002
parent_feature: F010
parent_story: S020
depends_on: [T039]
owned_paths: [crates/domain/src/dataio/**, testing/features/F010/performance/**, testing/features/F010/requirements/**, testing/features/F010/e2e/**]
feature_flag: F010_FEATURE
branch: t040-fixtures-load-tests
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 7, 9
- Capability contract: `docs/capability-contracts.md` row F010

# T040 — Fixtures/load tests

## Identity

- Parent story: `S020` CSV/XLSX jobs
- Owner: platform
- Branch: `t040-fixtures-load-tests`
- Decision references: `docs/architecture-decisions.md` sections 7, 9; `docs/capability-contracts.md` row F010

## Objective

Build the deterministic large-scale fixture generators and the load, resume, and traceability suites that prove the F010 performance and reliability targets at 1,000,000 documents and 100,000 rows.

## Specification

- Owned paths: `crates/domain/src/dataio/fixtures.rs`, `testing/features/F010/performance/{search_bench.rs, index_lag_bench.rs, import_bench.rs, export_bench.rs}`, `testing/features/F010/requirements/cases.md`, `testing/features/F010/e2e/dataio_recovery.spec.ts`
- Contract/input: `fixtures::seed_search_documents(tenant, count: 1_000_000, seed)`, `fixtures::generate_csv(rows: 100_000, columns: 8, invalid_ratio: 0.02, seed) -> PathBuf`, `fixtures::generate_xlsx(rows, columns, seed)`, `fixtures::seed_sheet_rows(sheet, rows: 100_000, seed)`; the worker harness `kill_after_chunk(n)` and `restart_worker()` from `testing/harness/worker.rs`.
- Output/behavior: `search_bench` runs 500 queries drawn from a fixed term list against 1,000,000 documents and asserts p95 under 500 ms with the GIN index in the plan; `index_lag_bench` publishes 1,000 row events and asserts document visibility lag p95 under 5 s; `import_bench` commits the 100,000-row CSV and asserts completion under 10 minutes, `processed_rows = 100_000`, and `error_count = 2_000`; `import_bench::resume_after_kill` kills the worker after chunk 37 and asserts the sheet ends with exactly 98,000 new rows and no duplicate `target_row_id`; `export_bench` exports 100,000 rows to CSV under 60 s, XLSX under 120 s, and PDF under 300 s with checksum recorded; the requirements table maps every FR-F010 and NFR-F010 to a lane and case; the recovery E2E spec drives cancel and dead-letter states through the UI.
- Dependencies: T039 export path and UI; F004 job runs and dead-letter tables; MinIO per-worker prefix.
- Feature flag: `F010_FEATURE`; performance lane runs only in `cargo xtask test-all` and nightly.

## TDD

- Failing test first: `testing/features/F010/performance/search_bench.rs::search_1m_documents_p95`, `testing/features/F010/performance/index_lag_bench.rs::index_lag_p95_under_5s`, `testing/features/F010/performance/import_bench.rs::import_100k_rows_under_10_minutes`, `::resume_after_kill_no_duplicates`, `testing/features/F010/performance/export_bench.rs::export_100k_csv_under_60s`, `::export_100k_pdf_paginates_with_header_repeat`, `testing/features/F010/e2e/dataio_recovery.spec.ts::cancel_import_keeps_written_rows`, `::dead_lettered_import_shows_failure_reason`
- Targeted command: `cargo xtask test-feature F010`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: fixed seed `0xF010`, fixed clock `2026-09-03T00:00:00Z`; generators write files under the per-worker scratch directory; k6 summaries and criterion output stored under `testing/evidence/F010/performance/`

## Exit criteria

- [ ] Tests written before the generators and observed failing
- [ ] Every NFR-F010 target met and evidence recorded under `testing/evidence/F010/`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S020
- [ ] `finished_at` recorded
