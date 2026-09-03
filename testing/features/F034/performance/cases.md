# F034 performance cases

File: `testing/features/F034/performance/{workload_read_bench.rs,conflict_latency_bench.rs,time_entry_write_bench.rs,import_bench.rs,summary_lag_bench.rs,job_reliability_test.rs}` with budgets in `budgets.toml`. Seed: `testing/fixtures/workload.rs::large_tenant` — 1,000 resources, 12 weeks of capacity and allocations, 40,000 native entries over 500 rows, 120 open conflicts, a 2,000-entry import of which 300 collide. 200 measured iterations after 20 warmups on CI PostgreSQL 18. Flag `F034_FEATURE`.

- `workload_1000_resources_12_weeks_under_500ms_p95` — NFR-F034-01, FR-F034-01: the workload read for 1,000 resources over 12 weeks stays under 500 ms p95 served from `effort_summaries`.
- `workload_read_uses_effort_summaries_index` — NFR-F034-01: `EXPLAIN` shows `effort_summaries(scope, scope_id, period_start)` and no sequential scan of `time_entries`.
- `conflicts_list_with_suggestions_under_500ms_p95` — NFR-F034-01, FR-F034-03: a 120-conflict page with float and reassign lookups stays under 500 ms p95.
- `conflict_detected_within_30s_of_capacity_event` — NFR-F034-01, FR-F034-02: the open conflict and `workload-conflict.detected.v1` appear within 30 s of `capacity.computed.v1`; `conflict_detection_ms` p95 recorded.
- `time_entry_create_under_800ms_p95` — NFR-F034-01, FR-F034-04: native create including cost snapshot, audit, and outbox stays under 800 ms p95.
- `import_2000_entries_under_5s` — NFR-F034-01, FR-F034-06: a 2,000-entry import with 300 collisions completes in under 5 s wall clock and reports the pending set.
- `failed_import_leaves_no_rows` — NFR-F034-04, FR-F034-06: a failure at entry 1,500 rolls the request back completely.
- `summaries_refresh_within_60s_of_recorded_event` — NFR-F034-01, FR-F034-10: `row`, `project`, and `resource_period` summaries refresh within 60 s of `time-entry.recorded.v1` and `time-entry.reconciled.v1`; `workload_summary_lag_seconds` sampled.
- `summary_lag_stays_under_budget_during_import` — NFR-F034-01, FR-F034-10: during the 2,000-entry import the sampled lag stays under 60 s and reads report `stale: true` rather than stale numbers.
- `replayed_source_version_is_idempotent` — NFR-F034-04: replaying a source event leaves one summary row and publishes no duplicate conflict event.
- `third_failure_dead_letters_with_last_error` — NFR-F034-04: a handler failing three times dead-letters with `last_error` set, and `rebuild_summaries` restores the affected scopes.
- `workload_metrics_are_exported` — NFR-F034-04: the metrics scrape contains `workload_summary_lag_seconds` and `conflict_detection_ms`, and spans carry `tenant_id`, `resource_id`, `row_id`, `time_entry_id`, and `correlation_id`.

Evidence: JSON results with p50, p95, p99, iteration count, and seed under `testing/evidence/F034/performance/`.
