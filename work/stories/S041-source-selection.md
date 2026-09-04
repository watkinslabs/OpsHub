---
id: S041
type: story
status: planned
parent_epic: E005
parent_feature: F021
depends_on: [F008, F035, F003]
owned_paths: [crates/domain/src/reports/**, crates/persistence/src/reports/**, services/api/src/reports/**, services/worker/src/reports/**, services/api/migrations/*_reports_*.sql, testing/features/F021/**]
feature_flag: F021_FEATURE
branch: s041-source-selection
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 7
- Capability contract: `docs/capability-contracts.md` row F021

# S041 — Source selection

## Identity

- Parent feature: `F021` Cross-source reports
- Owner: platform
- Branch: `s041-source-selection`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 7; `docs/capability-contracts.md` row F021

## Vertical slice

As a report editor, I want to create a report that selects one or more sheets and their columns, save it with a refresh policy, and refresh it into a cached snapshot whose rows are filtered by my permissions, so that a governed result exists before joins, filters, and grouping are layered on.

## Requirements

- **SR-S041-01:** `POST /api/v1/reports` with `{ name, workspace_id, folder_id?, description?, definition: { sources[] }, refresh_policy }` validates aliases, sheet ownership, and column membership, then decomposes the definition into `report_sources` and `report_source_columns` rows through `ReportRepository::replace_definition` and returns `ReportResponse` with the same nested `definition`, `version` 1, and `snapshot: null` (FR-F021-01, FR-F021-02).
- **SR-S041-02:** `refresh_policy` accepts `manual` or `interval` with `interval_minutes` 5..1440 and an IANA `timezone` and persists as the typed `reports.refresh_mode`, `refresh_interval_minutes`, `refresh_timezone` columns; other values return `400 invalid` with the field path, and the `interval`-without-interval combination is rejected by both the validator and the table check (FR-F021-08).
- **SR-S041-03:** `POST /api/v1/reports/{id}/refresh` inserts a `queued` snapshot through `ReportSnapshotRepository`, publishes the `reports.refresh` job, returns `202 { run_id, status }` under 2 seconds, and returns `409 conflict` with the active `run_id` from `find_active_run` while a run is active (FR-F021-07).
- **SR-S041-04:** The worker refresh job claims the run with `ReportRepository::claim_refresh`, reads each source through the compiled read plan, hands `report_snapshot_rows` and their `report_snapshot_row_sources` entries to `ReportSnapshotRepository` in batches of 5,000, records `row_count`, `duration_ms`, `computed_at` and one `report_snapshot_sources` row per source sheet, keeps the last 3 succeeded snapshots via `prune_snapshots`, and publishes `report.refreshed.v1` (FR-F021-07, NFR-F021-04).
- **SR-S041-05:** `GET /api/v1/reports/{id}/rows` returns snapshot rows from `page_snapshot_rows` filtered by the viewer's `ViewerScope`: rows whose `report_snapshot_row_sources` entries point at unreadable sheets are dropped, hidden columns removed, and `meta` carries `stale` (from `report_snapshot_sources` against current sheet versions), `restricted_sources`, `hidden_columns` (FR-F021-09, FR-F021-10).
- **SR-S041-06:** `GET /api/v1/reports`, `GET /api/v1/reports/{id}`, `PATCH`, and `DELETE` behave per FR-F021-12 and FR-F021-13, including `If-Match` conflicts and `mark_snapshots_stale` running in the same `UnitOfWork` as `replace_definition` on a definition change.
- **SR-S041-07:** Every mutation requires `Idempotency-Key`, writes an audit event, and emits `report.created.v1`, `report.updated.v1`, or `report.deleted.v1`; foreign-tenant actors get `404 not_found` (FR-F021-13, FR-F021-14).

## Surfaces

- Infrastructure/container: JetStream subject `reports.refresh` declared in `services/worker/src/reports/scheduler.rs`; no new compose services
- Rust service/API: `crates/domain/src/reports/{mod.rs, report.rs, definition.rs, validate.rs, snapshot.rs, scope.rs, compiler.rs, errors.rs, service.rs}` (repository traits only, no SQL); `crates/persistence/src/reports/{mod.rs, report_repository.rs, report_snapshot_repository.rs}` holding every SQL statement for this feature; `services/api/src/reports/{mod.rs, routes.rs, handlers_report.rs, handlers_rows.rs, dto.rs}`; `services/worker/src/reports/{mod.rs, refresh_job.rs, scheduler.rs}`
- Data/migration: `services/api/migrations/<ts>_reports_create_tables.sql` creating `reports`, `report_sources`, `report_source_columns`, `report_joins`, `report_filters`, `report_group_by`, `report_aggregates`, `report_calculated_fields`, `report_snapshots`, `report_snapshot_sources`, `report_snapshot_rows`, `report_snapshot_row_sources` with the constraints and indexes from ticket section 4
- React/UI: none in this story (S042 covers the editor and viewer)
- Mocks/fixtures: `testing/fixtures/reports.rs` tenants A and B, editor, viewer, restricted viewer, sheets "Projects", "Risks", "Budget"; in-memory outbox recorder; in-memory JetStream stub

## TDD harness

- Test path: `testing/features/F021/api/` and `testing/features/F021/database/`
- Feature flag: `F021_FEATURE`
- Targeted command: `cargo xtask test-feature F021`
- Full command: `cargo xtask test-all`
- First failing tests: `report_create_returns_version_one`, `report_source_alias_invalid`, `report_refresh_acknowledged_under_two_seconds`, `report_refresh_active_conflicts`, `report_rows_drop_restricted_sheet`, `report_cross_tenant_not_found`, `report_definition_round_trips_through_repository`

## Exit criteria

- [ ] Requirement tests SR-S041-01 through SR-S041-07 written first and failing
- [ ] Tasks T081 and T082 complete and wired through `services/api` router and the worker consumer registry
- [ ] Unit, API, database, permission, and worker tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/reports/routes.rs` mounted in `services/api/src/router.rs`; `services/worker/src/reports/refresh_job.rs` registered in `services/worker/src/consumers.rs`
- [ ] Handoff evidence recorded in the F021 ticket
