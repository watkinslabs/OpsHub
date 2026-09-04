---
id: T082
type: task
status: planned
parent_epic: E005
parent_feature: F021
parent_story: S041
depends_on: [T081]
owned_paths: [crates/domain/src/reports/**, crates/persistence/src/reports/**, services/worker/src/reports/**, testing/features/F021/api/**]
feature_flag: F021_FEATURE
branch: t082-permission-aware-query
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 4, 7
- Capability contract: `docs/capability-contracts.md` row F021

# T082 — Permission-aware query

## Identity

- Parent story: `S041` Source selection
- Owner: platform
- Branch: `t082-permission-aware-query`
- Decision references: `docs/architecture-decisions.md` sections 2, 4, 7; `docs/capability-contracts.md` row F021

## Objective

Implement the query compiler, the worker refresh job that materializes snapshots, and the viewer-scope filter that drops restricted rows and hidden columns at read time.

## Specification

- Owned paths: `crates/domain/src/reports/{compiler.rs, scope.rs, calc.rs, service.rs}`, `crates/persistence/src/reports/{report_repository.rs, report_snapshot_repository.rs}`, `services/worker/src/reports/{mod.rs, refresh_job.rs, scheduler.rs}`
- Contract/input: `ValidatedDefinition` from T081; `RefreshJob { tenant_id, report_id, run_id, requested_by, correlation_id }` on JetStream subject `reports.refresh`; `ViewerScope::build(authz, actor, sheet_ids) -> ViewerScope { readable_sheets, hidden_columns, scope_key }` using F003 `authz::filter_readable(actor, ResourceKind::Sheet, ids)` and F007 column visibility plus F003 field-level ACL.
- Output/behavior: `compile(def) -> CompiledQuery` produces a per-source read plan (sheet, projected columns from `report_source_columns`, predicates from `report_filters`) and the join graph from `report_joins` — it contains no SQL string, `sqlx::query*` call, or connection; the `rows`/`cells` reads run through the F008 repositories under that plan, `execute(def, reader)` streams the root source and hash-joins children by `link` raw value or normalized scalar and caps intermediate rows at 1,000,000 with `error = "join_fanout_exceeded"`; `calc.rs` evaluates calculated fields per row through `formulas::evaluate` with a 2 s per-report budget and writes `#BUDGET` display on overrun; `refresh_job.rs` claims the run with `ReportRepository::claim_refresh(report_id, run_id)` (which sets the snapshot `running` and serializes concurrent refreshes of one report), hands rows and their `report_snapshot_row_sources` entries to `ReportSnapshotRepository` in batches of 5,000, records `row_count`, `duration_ms`, `computed_at` and one `report_snapshot_sources` row per source sheet, marks `succeeded|failed`, calls `prune_snapshots(report_id, 3)`, publishes `report.refreshed.v1`, retries 3 times with backoff and dead-letters on the fourth failure, and is idempotent by `run_id`; `scheduler.rs` selects due interval reports with `page_reports` over `refresh_mode`/`refresh_interval_minutes`, enqueues each at most once per interval and never while `find_active_run` returns a run, and holds no SQL; `read_rows(snapshot, scope, cursor, limit)` composes a `ViewerScope`-aware query executed by `ReportSnapshotRepository::page_snapshot_rows`, dropping inner-join rows whose `report_snapshot_row_sources` entries point at unreadable sheets, nulling left-join sides, stripping hidden columns, and filling `meta.restricted_sources`, `meta.hidden_columns`, and `meta.stale` by comparing `report_snapshot_sources.sheet_version` against current sheet versions.
- Dependencies: T081 model, tables and repositories; F008 `rows`/`cells` read access through the F008 repositories; F003 engine; F004 worker consumer registry and outbox writer.
- Feature flag: `F021_FEATURE` gates the consumer registration in `services/worker/src/consumers.rs`.

## TDD

- Failing test first: `testing/features/F021/api/query_tests.rs::compile_plan_names_one_read_per_source`, `::join_by_link_column_matches_row_id`, `::join_fanout_cap_fails_run`, `::refresh_job_writes_snapshot_and_event`, `::refresh_job_idempotent_by_run_id`, `::refresh_job_dead_letters_after_four_failures`, `::report_rows_drop_restricted_sheet`, `::report_rows_strip_hidden_columns`, `::stale_flag_set_when_sheet_version_advances`
- Targeted command: `cargo xtask test-feature F021`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/reports.rs` three-sheet fixture; in-memory JetStream stub with failure injection; real F003 engine bindings for editor, viewer, restricted viewer; tests reach the tables only through `ReportRepository` and `ReportSnapshotRepository` and hold no SQL string, `sqlx::query*` call, or connection

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Refresh consumer registered behind the flag; retry and dead-letter paths verified
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S041
- [ ] `finished_at` recorded
