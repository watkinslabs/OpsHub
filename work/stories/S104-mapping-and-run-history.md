---
id: S104
type: story
status: planned
parent_epic: E008
parent_feature: F052
depends_on: [S103]
owned_paths: [crates/domain/src/data-shuttle/**, crates/persistence/src/data-shuttle/**, services/api/src/data-shuttle/**, services/worker/src/data-shuttle/**, apps/web/src/features/data-shuttle/**, testing/features/F052/**]
feature_flag: F052_FEATURE
branch: s104-mapping-and-run-history
started_at: null
finished_at: null
---

# S104 — Mapping and run history

## Identity

- Parent feature: `F052` Data Shuttle
- Owner: platform
- Branch: `s104-mapping-and-run-history`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 6, 7; `docs/capability-contracts.md` row F052

## Vertical slice

As a data administrator, I want to build the column mapping against a sample file, browse every run with its counts and rejected rows, download the archived file and validation report, and replay a run from its archive, so that I can diagnose and recover a bad import without leaving the app.

Out of this slice: schedule execution and the worker (S103); connector authentication (F029); PDF export (F025).

## Requirements

- **SR-S104-01:** `GET /api/v1/data-shuttle/flows/{id}/runs` pages newest first by opaque cursor with `limit` ≤ 100 and filters `status` and `since` through `ShuttleRunRepository::list_runs_by_flow`; `GET /api/v1/data-shuttle/runs/{id}` returns counts, up to 50 `shuttle_run_rejections` rows read by `list_rejections_head` and serialized as the `rejected_sample` array, and 15-minute archive and report URLs only when the caller can read the sheet (covers FR-F052-10, NFR-F052-02).
- **SR-S104-02:** `POST /api/v1/data-shuttle/runs/{id}/replay` starts a new run from the archive using the captured `flow_version`, records `replay_of_run_id`, and returns `409 conflict` with `field_errors.archive = "purged"` when `ShuttleArchiveRepository::find_archive_for_run` reports `purged_at` set (FR-F052-09).
- **SR-S104-03:** `GET /api/v1/data-shuttle/flows` lists flows with `next_run_at`, last run status, and cursor paging through `ShuttleFlowRepository::list_flows_with_last_run`, one query joining `shuttle_schedules` and the newest `shuttle_runs` row rather than a per-row lookup; cross-tenant flow and run ids return `404 not_found` (FR-F052-14).
- **SR-S104-04:** `FlowEditorPage` builds the `mapping` object from a sample file preview of the first 20 rows — the API keeps the array shape and the server stores each entry as a `shuttle_flow_column_maps` row — validates coercion against column types client-side, shows `field_errors` from the API inline, and edits `validation`, `schedule`, and `archive_policy` (FR-F052-02, FR-F052-03, FR-F052-04, FR-F052-14).
- **SR-S104-05:** `RunHistoryPage` and `RunDrawer` show status, counts, rejected rows, replay, and downloads, poll every 5 seconds while a run is active, and render loading, empty, error, denied, stale, not-entitled, and offline states (FR-F052-14, NFR-F052-03).
- **SR-S104-06:** Non-`data-admin` users see flows and runs read-only without `Run` or `Replay`; a tenant without entitlement sees `ModuleNotEntitled`; navigation shows `Data Shuttle` only when `useModuleAllowed('data-shuttle')` is true (FR-F052-12, FR-F052-14).
- **SR-S104-07:** Flow list and run list respond in under 500 ms p95 with 1,000 runs per flow; a 100,000-row import finishes in under 10 minutes (NFR-F052-01).

## Surfaces

- Infrastructure/container: none beyond S103
- Data access: `crates/persistence/src/data-shuttle/{run_repository.rs, archive_repository.rs, flow_repository.rs}` extended with `list_runs_by_flow`, `list_rejections_head`, `find_archive_for_run`, and `list_flows_with_last_run`; `service_runs.rs`, `replay.rs`, `handlers_run.rs`, and `handlers_download.rs` hold no SQL and reach every table through those repositories, and the replay path writes the new run, its trigger, and `replay_of_run_id` in one `UnitOfWork` (decision section 2.1)
- Rust service/API: `crates/domain/src/data-shuttle/{service_runs.rs, replay.rs}`; `services/api/src/data-shuttle/{handlers_run.rs, handlers_download.rs}`; `services/worker/src/data-shuttle/replay.rs`
- Data/migration: none new; uses the S103 tables
- React/UI: `apps/web/src/features/data-shuttle/{FlowListPage.tsx, FlowRow.tsx, FlowEditorPage.tsx, LocationPicker.tsx, MappingTable.tsx, MappingRow.tsx, SamplePreview.tsx, ValidationFields.tsx, ScheduleFields.tsx, ArchiveFields.tsx, RunHistoryPage.tsx, RunRow.tsx, RunDrawer.tsx, RejectedRowsTable.tsx, ReplayConfirmDialog.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: seeded flow with 1,000 runs for paging and performance; MSW handlers for component tests; Playwright against the real API with MinIO

## TDD harness

- Test path: `testing/features/F052/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F052_FEATURE`
- Targeted command: `cargo xtask test-feature F052`
- Full command: `cargo xtask test-all`
- First failing tests: `run_list_pages_newest_first`, `run_detail_hides_urls_without_sheet_read`, `replay_purged_archive_conflicts`, `mapping_table_flags_coercion_mismatch`, `run_drawer_polls_while_running`, `create_flow_run_and_replay`

## Exit criteria

- [ ] Requirement tests SR-S104-01 through SR-S104-07 written first and failing
- [ ] Tasks T207 and T208 complete; UI wired to real API through generated client
- [ ] Unit, API, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `apps/web/src/features/data-shuttle/FlowListPage.tsx` mounted at `/w/:workspaceId/data-shuttle`; `RunHistoryPage.tsx` at `/w/:workspaceId/data-shuttle/:flowId`
- [ ] Handoff evidence recorded in the F052 ticket
