---
id: T136
type: task
status: planned
parent_epic: E007
parent_feature: F034
parent_story: S068
depends_on: [S068]
owned_paths: [testing/features/F034/performance/**, testing/features/F034/requirements/**]
feature_flag: F034_FEATURE
branch: t136-performance-tests
started_at: null
finished_at: null
---

# T136 — Workload performance and reliability gates

## Identity

- Parent story: `S068` Time entries and planned versus actual
- Owner: platform
- Branch: `t136-performance-tests`
- Decision references: `docs/architecture-decisions.md` sections 2, 9; `docs/capability-contracts.md` row F034

## Objective

Turn NFR-F034-01 and NFR-F034-04 into executable gates: the four latency budgets (workload read, conflict detection, entry create, bulk import), the summary freshness budget of FR-F034-10, and the job idempotency, retry, dead-letter, and metric assertions — plus the traceability matrix in `testing/features/F034/requirements/cases.md`.

## Specification

- Owned files: `testing/features/F034/performance/{workload_read_bench.rs, conflict_latency_bench.rs, time_entry_write_bench.rs, import_bench.rs, summary_lag_bench.rs, job_reliability_test.rs, budgets.toml}` and `testing/features/F034/requirements/cases.md`.
- Seed: extend `testing/fixtures/workload.rs` with a `large_tenant()` generator — 1,000 resources, 12 weeks of capacity and allocations (about 84,000 allocation-days), 40,000 native time entries across 500 task rows, 120 open conflicts, and a 2,000-entry external payload of which 300 collide with native entries; deterministic UUIDv7 seeds and fixed clock `2026-09-03T00:00:00Z`.
- Budgets asserted from `budgets.toml`, measured over 200 warm iterations after 20 warmup iterations against CI PostgreSQL 18: `GET /api/v1/workload` for 1,000 resources over 12 weeks p95 < 500 ms served from `effort_summaries`; conflict detection completes within 30 s of `capacity.computed.v1` for a resource span, with p95 of `conflict_detection_ms` recorded; `POST /api/v1/time-entries` p95 < 800 ms; `POST /api/v1/time-entries/import` of 2,000 entries < 5 s wall clock; `effort_summaries` for the affected row, project, and resource period refreshed within 60 s of `time-entry.recorded.v1`, `time-entry.reconciled.v1`, `allocation.*.v1`, and `capacity.computed.v1`, with `workload_summary_lag_seconds` sampled.
- Query-plan guards: the workload read and conflicts list must use `effort_summaries(scope, scope_id, period_start)` and `workload_conflicts(tenant_id, status, period_start)`; the bench fails on a sequential scan of `time_entries` for a single-resource range, which must use `time_entries(resource_id, entry_date) where deleted_at is null`.
- Reliability assertions: `summary_builder` and `conflict_detector` are idempotent by `(scope_id, source_version)` — replaying the same event twice leaves one summary row and publishes no second `workload-conflict.detected.v1`; a handler failing three times dead-letters with `last_error` populated and the summary is rebuilt by `rebuild_summaries` afterwards; an import that fails mid-batch leaves zero rows (atomic per request); every span carries `tenant_id`, `resource_id`, `row_id`, `time_entry_id`, `correlation_id`; `workload_summary_lag_seconds` and `conflict_detection_ms` are present in the metrics scrape.
- Traceability: `testing/features/F034/requirements/cases.md` maps FR-F034-01 through FR-F034-14 and NFR-F034-01 through NFR-F034-04 to the lane and test that proves each, and evidence is written to `testing/evidence/F034/performance/` as JSON with p50, p95, p99, iteration count, and seed.
- Dependencies: T133 detector and workload read, T134 entries and summaries, T135 for the E2E seed reuse; F004 job transport for retry and dead-letter semantics.
- Rollback: benches are gated by `F034_FEATURE` and skipped when the flag is off; no production code is owned by this task.

## TDD

- Failing test first: `testing/features/F034/performance/workload_read_bench.rs::workload_1000_resources_12_weeks_under_500ms_p95`, `::workload_read_uses_effort_summaries_index`; `testing/features/F034/performance/conflict_latency_bench.rs::conflict_detected_within_30s_of_capacity_event`; `testing/features/F034/performance/time_entry_write_bench.rs::time_entry_create_under_800ms_p95`; `testing/features/F034/performance/import_bench.rs::import_2000_entries_under_5s`, `::failed_import_leaves_no_rows`; `testing/features/F034/performance/summary_lag_bench.rs::summaries_refresh_within_60s_of_recorded_event`; `testing/features/F034/performance/job_reliability_test.rs::replayed_source_version_is_idempotent`, `::third_failure_dead_letters_with_last_error`, `::workload_metrics_are_exported`
- Fixtures/mocks: `testing/fixtures/workload.rs::large_tenant`; in-process job runner with injectable failure counts; metrics recorder; one schema per test worker
- Targeted command: `cargo xtask test-feature F034`
- Full command: `cargo xtask test-all`

## Exit criteria

- [ ] Benches written and observed failing (or skipped-with-reason) before the implementation tasks land
- [ ] All five budgets pass on CI hardware three consecutive runs; results archived under `testing/evidence/F034/performance/`
- [ ] Idempotency, retry, dead-letter, atomic-import, span-attribute, and metric assertions pass
- [ ] Requirements matrix covers every FR-F034 and NFR-F034 id with a named test
- [ ] Owned-path, 500-line, and lint gates pass
- [ ] Handoff evidence recorded in S068
- [ ] `finished_at` recorded
