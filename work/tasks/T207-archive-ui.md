---
id: T207
type: task
status: planned
parent_epic: E008
parent_feature: F052
parent_story: S104
depends_on: [S104]
owned_paths: [crates/domain/src/data-shuttle/**, services/api/src/data-shuttle/**, services/worker/src/data-shuttle/**, apps/web/src/features/data-shuttle/**, testing/features/F052/api/**, testing/features/F052/frontend/**]
feature_flag: F052_FEATURE
branch: t207-archive-ui
started_at: null
finished_at: null
---

# T207 — Archive UI

## Identity

- Parent story: `S104` Mapping and run history
- Owner: platform
- Branch: `t207-archive-ui`
- Decision references: `docs/architecture-decisions.md` sections 3, 5, 6; `docs/capability-contracts.md` row F052

## Objective

Implement the run history, run detail, download, and replay routes plus the flow list, flow editor with mapping preview, run history page, and run drawer wired to the real API.

## Specification

- Owned paths: `crates/domain/src/data-shuttle/{service_runs.rs, replay.rs}`, `services/api/src/data-shuttle/{handlers_run.rs, handlers_download.rs}`, `services/worker/src/data-shuttle/replay.rs`, `apps/web/src/features/data-shuttle/{FlowListPage.tsx, FlowRow.tsx, FlowEditorPage.tsx, LocationPicker.tsx, MappingTable.tsx, MappingRow.tsx, SamplePreview.tsx, ValidationFields.tsx, ScheduleFields.tsx, ArchiveFields.tsx, RunHistoryPage.tsx, RunRow.tsx, RunDrawer.tsx, RejectedRowsTable.tsx, ReplayConfirmDialog.tsx, api.ts, hooks.ts, routes.ts}`
- Contract/input: list query `{ cursor?, limit? (≤100), status?, since? }`; `GET /api/v1/data-shuttle/runs/{id}` requires sheet read permission for download URLs; `POST /api/v1/data-shuttle/runs/{id}/replay` with `Idempotency-Key`; generated `DataShuttleApi` client; route params `workspaceId`, `flowId`; sample file upload through the F017 upload endpoint for preview.
- Output/behavior: `GET /api/v1/data-shuttle/flows/{id}/runs` pages newest first; `GET /api/v1/data-shuttle/runs/{id}` returns counts, 50 rejected rows with reasons (columns the caller cannot read redacted), and 15-minute signed `archive_url` and `report_url`; replay creates a run with `trigger = replay`, `replay_of_run_id`, and the original `flow_version`, or returns `409 archive purged`; UI renders flow list with `next_run_at` and last status, editor with `SamplePreview` (first 20 rows), `MappingTable` with client-side coercion checks and inline `field_errors`, schedule and archive fields, run history with 5-second polling while active, run drawer with counts, rejected rows, `Replay` (disabled with tooltip when purged), and downloads; states: loading skeleton, empty call to action, error banner with correlation ID, read-only for non-admins, `ModuleNotEntitled` panel, stale banner, offline badge; telemetry `shuttle_flow_created`, `shuttle_flow_updated`, `shuttle_run_requested`, `shuttle_run_replayed`, `shuttle_archive_downloaded`, `shuttle_mapping_previewed`.
- Dependencies: T206 worker and archives; F048 `useModuleAllowed('data-shuttle')` and `ModuleNotEntitled`; F005 workspace shell navigation entry; F017 signed download URLs.
- Feature flag: `F052_FEATURE` read through the flag hook; routes are not registered when off.

## TDD

- Failing test first: `testing/features/F052/api/run_tests.rs::run_list_pages_newest_first`, `::run_detail_hides_urls_without_sheet_read`, `::run_detail_redacts_unreadable_columns`, `::replay_uses_original_flow_version`, `::replay_purged_archive_conflicts`, `::run_cross_tenant_not_found`; `testing/features/F052/frontend/MappingTable.test.tsx::mapping_table_flags_coercion_mismatch`, `::mapping_table_requires_keys_for_update`, `RunDrawer.test.tsx::run_drawer_polls_while_running`, `::replay_disabled_when_archive_purged`, `FlowListPage.test.tsx::hides_run_for_non_admin`, `::shows_not_entitled_panel`
- Targeted command: `cargo xtask test-feature F052`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: MSW handlers from the seeded flow with two runs; role-switching session helper; MinIO signed URL stub for component tests

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Component and API lanes pass; routes mounted at `/w/:workspaceId/data-shuttle` and `/w/:workspaceId/data-shuttle/:flowId`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S104
- [ ] `finished_at` recorded
