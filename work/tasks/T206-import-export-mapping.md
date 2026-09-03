---
id: T206
type: task
status: planned
parent_epic: E008
parent_feature: F052
parent_story: S103
depends_on: [T205]
owned_paths: [crates/domain/src/data-shuttle/**, services/worker/src/data-shuttle/**, testing/features/F052/api/**, testing/features/F052/requirements/**, testing/features/F052/performance/**]
feature_flag: F052_FEATURE
branch: t206-import-export-mapping
started_at: null
finished_at: null
---

# T206 — Import/export mapping

## Identity

- Parent story: `S103` Scheduled file flows
- Owner: platform
- Branch: `t206-import-export-mapping`
- Decision references: `docs/architecture-decisions.md` sections 2, 5, 7; `docs/capability-contracts.md` row F052

## Objective

Implement mapping validation, the worker run consumer that fetches, validates, imports or exports, applies the duplicate strategy, archives the file, publishes run events, and the nightly archive purge.

## Specification

- Owned paths: `crates/domain/src/data-shuttle/{mapping.rs, validation.rs, archive.rs, counts.rs}`, `services/worker/src/data-shuttle/{consumer.rs, fetcher.rs, importer.rs, exporter.rs, archiver.rs, purge.rs}`
- Contract/input: job payload `{ tenant_id, flow_id, run_id, trigger, correlation_id }` on subject `data-shuttle.run`; `Mapping { columns: Vec<ColumnMap { source_column, column_id, coerce }>, key_column_ids, duplicate_strategy }` validated by `validate_mapping(sheet_columns, mapping)` (foreign column, coerce mismatch, missing keys for `update|replace|skip`); `ValidationPolicy { required_column_ids, max_errors, on_error }`; entitlement limits `max_file_mb`, `max_rows_per_run`; `FileLocation` variants `attachment` (F017 download), `inbox` (S3 prefix, newest object), `connector` (F030 adapter `download`).
- Output/behavior: consumer claims the run (`queued → running`, publishes `shuttle-run.started.v1`), fetches the file, computes SHA-256, fails fast with `file_too_large` or `too_many_rows`, short-circuits `duplicate_file` on a checksum already succeeded, streams rows through coercion and validation into an F010 `import_jobs` record (or reads sheet rows into an `export_jobs` file for `export`), applies `append|update|replace|skip` by key columns, records counts, writes the validation report as an F017 file, archives the file under `shuttle/{tenant_id}/{flow_id}/{run_id}` with `retain_until`, finishes `succeeded|partial|failed` and publishes `shuttle-run.completed.v1` or `shuttle-run.failed.v1`; rows are written as the flow owner with `source = data_shuttle`, and a missing `sheet-editor` grant fails the run with `sheet_denied`; transient storage errors retry three times with backoff, timeout 30 minutes, then dead-letter with the reason on the run; `purge.rs` deletes archives past `retain_until` nightly and marks runs `archive_purged`.
- Dependencies: T205 tables, routes, and job publication; F010 parser and job APIs; F017 file service; F030 connector adapter; F004 JetStream consumer with quotas and dead letters.
- Feature flag: `F052_FEATURE`; the consumer acknowledges and parks jobs without processing when off.

## TDD

- Failing test first: `testing/features/F052/api/worker_tests.rs::worker_run_applies_update_strategy`, `::worker_append_strategy_inserts_all`, `::worker_duplicate_checksum_skips`, `::worker_abort_writes_nothing`, `::worker_partial_commits_valid_rows`, `::worker_file_too_large_fails_fast`, `::worker_sheet_denied_when_owner_lost_access`, `::worker_archives_with_retain_until`, `::worker_publishes_started_and_completed`, `::worker_dead_letters_after_three_retries`, `::purge_marks_run_archive_purged`; `testing/features/F052/performance/import_bench.rs::import_100k_rows_under_10_minutes`
- Targeted command: `cargo xtask test-feature F052`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: MinIO bucket prefix per test; recorded connector `download` stub; failing storage stub for retry tests; `Budget` sheet with 100 existing rows keyed by cost center; 100,000-row generated CSV for the benchmark

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Consumer registered in `services/worker/src/main.rs`; run events visible in `outbox_events`; metrics exported
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S103
- [ ] `finished_at` recorded
