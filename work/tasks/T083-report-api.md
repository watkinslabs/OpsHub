---
id: T083
type: task
status: planned
parent_epic: E005
parent_feature: F021
parent_story: S042
depends_on: [S042]
owned_paths: [crates/domain/src/reports/**, crates/persistence/src/reports/**, services/api/src/reports/**, apps/web/src/features/reports/**, testing/features/F021/api/**, testing/features/F021/frontend/**]
feature_flag: F021_FEATURE
branch: t083-report-api
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 3, 4, 6
- Capability contract: `docs/capability-contracts.md` row F021

# T083 — Report API

## Identity

- Parent story: `S042` Filters/joins
- Owner: platform
- Branch: `t083-report-api`
- Decision references: `docs/architecture-decisions.md` sections 3, 4, 6; `docs/capability-contracts.md` row F021

## Objective

Expose the seven report routes with authorization, idempotency, optimistic concurrency, audit, and outbox events, add grouping and filter execution to the compiler, and build the report editor and viewer pages on the generated client.

## Specification

- Owned paths: `crates/domain/src/reports/{joins.rs, filters.rs, grouping.rs}`, `crates/persistence/src/reports/{report_repository.rs, report_snapshot_repository.rs}`, `services/api/src/reports/{mod.rs, routes.rs, handlers_report.rs, handlers_rows.rs, dto.rs}`, `apps/web/src/features/reports/{ReportPage.tsx, ReportViewer.tsx, ReportTable.tsx, GroupHeaderRow.tsx, StaleBanner.tsx, RestrictedSourcesBar.tsx, ReportEditor.tsx, SourcePicker.tsx, JoinBuilder.tsx, FilterBuilder.tsx, GroupingPanel.tsx, CalculatedFieldEditor.tsx, RefreshPolicyForm.tsx, NewReportDialog.tsx, api.ts, hooks.ts, routes.ts}`
- Contract/input: `CreateReportRequest { name, workspace_id, folder_id?, description?, definition, refresh_policy, aggregate_policy? }`, `UpdateReportRequest` (same fields optional), list query `{ cursor?, limit? ≤ 100, workspace_id, folder_id?, name_prefix?, deleted?, sort? }`, rows query `{ cursor?, limit? ≤ 500, snapshot_id? }`; headers `Idempotency-Key`, `If-Match`.
- Output/behavior: routes `GET /api/v1/reports`, `POST /api/v1/reports`, `GET /api/v1/reports/{id}`, `PATCH /api/v1/reports/{id}`, `DELETE /api/v1/reports/{id}`, `GET /api/v1/reports/{id}/rows`, `POST /api/v1/reports/{id}/refresh` return `ReportResponse { id, workspace_id, folder_id, name, description, definition, refresh_policy, aggregate_policy, latest_snapshot, version, created_at, updated_at, deleted_at }`, `ReportRowsResponse { rows, meta, next_cursor }`, `RefreshResponse { run_id, status }`, where `definition` is composed by `ReportRepository::load_definition` from the definition tables and decomposed by `replace_definition` on write, so the nested client shape is unchanged and handlers hold no SQL; `filters.rs` resolves relative date tokens in `reports.refresh_timezone`; `grouping.rs` groups visible rows at read time, computes aggregates excluding hidden values unless `aggregate_scope = owner`, and emits header rows; errors map per ticket section 4; events `report.created.v1`, `report.updated.v1`, `report.deleted.v1` enqueued by the repository base contract in the same `UnitOfWork` transaction as the write; the React pages render every state from ticket section 3 and emit telemetry `report_created`, `report_opened`, `report_refresh_requested`, `report_definition_saved`, `report_restricted_sources_shown`.
- Dependencies: T082 compiler and scope; F003 `authz::require(actor, Permission::ReportEdit, workspace)`; F005 workspace shell for the `New report` entry point.
- Feature flag: `F021_FEATURE` gates router mounting and web route registration.

## TDD

- Failing test first: `testing/features/F021/api/report_tests.rs::report_create_returns_version_one`, `::report_duplicate_name_conflicts`, `::report_stale_version_conflicts`, `::report_idempotent_replay_returns_original`, `::report_viewer_mutation_denied`, `::report_cross_tenant_not_found`, `::filter_relative_date_uses_timezone`, `::group_aggregates_exclude_hidden_column`, `::owner_aggregate_policy_requires_tenant_setting`; `testing/features/F021/frontend/ReportEditor.test.tsx::join_builder_keyboard_add_join`, `ReportViewer.test.tsx::shows_stale_banner_and_refresh`
- Targeted command: `cargo xtask test-feature F021`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: three-sheet fixture; MSW handlers replaying `ReportRowsResponse` with `restricted_sources` and `hidden_columns`

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Router mounted in `services/api/src/router.rs` behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S042
- [ ] `finished_at` recorded
