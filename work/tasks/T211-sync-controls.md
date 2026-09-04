---
id: T211
type: task
status: planned
parent_epic: E008
parent_feature: F053
parent_story: S106
depends_on: [S106]
owned_paths: [crates/domain/src/datamesh/**, crates/persistence/src/datamesh/**, services/api/src/datamesh/**, services/worker/src/datamesh/**, apps/web/src/features/datamesh/**, testing/features/F053/api/**, testing/features/F053/frontend/**]
feature_flag: F053_FEATURE
branch: t211-sync-controls
started_at: null
finished_at: null
---

# T211 — Sync controls

## Identity

- Parent story: `S106` Controlled sync
- Owner: platform
- Branch: `t211-sync-controls`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 6, 7; `docs/capability-contracts.md` row F053

## Objective

Implement the sync run request, the worker consumer that writes the change plan with provenance and records conflicts, the on-change listener and scheduler, the conflict routes, and the mapping editor with preview, runs, and conflicts tabs.

## Specification

- Owned paths: `crates/domain/src/datamesh/{run.rs, conflict.rs, service_sync.rs}`, `crates/persistence/src/datamesh/{run_repository.rs, conflict_repository.rs}`, `services/api/src/datamesh/{handlers_sync.rs, handlers_conflict.rs}`, `services/worker/src/datamesh/{sync_consumer.rs, writer.rs, change_listener.rs, scheduler.rs}`, `apps/web/src/features/datamesh/{MappingListPage.tsx, MappingRow.tsx, MappingEditorPage.tsx, SheetPairPicker.tsx, MatchKeyTable.tsx, FieldMapTable.tsx, FieldMapRow.tsx, ExpressionField.tsx, SyncModeFields.tsx, PreviewTab.tsx, PreviewCounts.tsx, PreviewTable.tsx, RunsTab.tsx, RunRow.tsx, ConflictsTab.tsx, ConflictRow.tsx, ResolveDialog.tsx, api.ts, hooks.ts, routes.ts}`
- Contract/input: job payload `{ tenant_id, mapping_id, run_id, trigger, correlation_id }` on subject `datamesh.sync`; `ResolveConflictRequest { resolution: keep_source | keep_target | manual_value, value?, reason? }` with `Idempotency-Key`; conflicts list query `{ cursor?, limit? (≤100), kind?, status? }`; listener input events `row.updated.v1`, `cell.updated.v1`, `cells.bulk-updated.v1`, `row.deleted.v1` filtered by `source_sheet_id` and excluding `source = datamesh`; generated `DatameshApi` client; route params `workspaceId`, `mappingId`, query `tab`.
- Output/behavior: `POST /api/v1/datamesh/mappings/{id}/sync` inserts a `queued` run through `MeshRunRepository::insert_queued_run` (partial index yields `409 already_active`) and publishes the job; consumer marks `running`, computes the plan from T210, enforces `max_rows_per_sync`, re-checks owner `sheet-editor`, writes in batches of 500 through the F008 bulk cell service with `source = datamesh` and `run_id`, creates F009 links `{ kind: datamesh, mapping_id, source_row_id }`, creates rows for `unmatched_policy: create`, clears for `deletion_policy: clear`, writes back target-only changes on bidirectional maps, records `ambiguous_match`, `both_changed`, `unmatched_source`, `source_deleted` conflicts, advances `last_cursor`, finishes with counts and publishes `mapping.synced.v1` plus one `mapping-conflict.detected.v1` per conflict; a repeated cursor finishes `succeeded` with zero writes; retries three times, 15-minute timeout, dead-letter with reason; listener debounces 60 seconds per mapping; scheduler claims cron mappings through `MappingRepository::claim_due_scheduled_mappings`, which is the only place the `for update skip locked` statement exists; resolve applies the value through the cell service, marks `resolved`, and returns `409` when either row version moved; UI renders the four tabs with states per ticket section 3 and telemetry `datamesh_mapping_created`, `datamesh_mapping_updated`, `datamesh_preview_run`, `datamesh_sync_requested`, `datamesh_conflict_resolved`.
- Data access: `run.rs`, `conflict.rs`, `service_sync.rs`, `sync_consumer.rs`, `writer.rs`, `change_listener.rs`, `scheduler.rs`, `handlers_sync.rs`, and `handlers_conflict.rs` hold no SQL and no pool handle. `MeshRunRepository` owns `datamesh_runs` (`insert_queued_run`, `find_active_run`, `find_succeeded_run_by_cursor` on `source_cursor_sheet_version`, `claim_run`, `finish_run`); `ConflictRepository` owns `datamesh_conflicts` (`list_conflicts_page`, `count_open_conflicts`, `insert_open_conflicts`, `find_open_conflict`, `resolve_conflict`); the listener resolves mappings with `MappingRepository::list_enabled_mappings_for_source_sheet` and the writer loads its `datamesh_mapping_field_maps` rows with `MappingRepository::list_field_maps` and advances the cursor with `MappingRepository::advance_cursor`. One run's cell writes, conflict rows, counts, and cursor advance commit in a single `UnitOfWork`, as do a resolve's cell write and conflict update (decision section 2.1).
- Dependencies: T210 engine and plan; F008 bulk cell service; F009 link service; F048 `useModuleAllowed('datamesh')` and `ModuleNotEntitled`; F005 navigation shell.
- Feature flag: `F053_FEATURE`; consumer, listener, and scheduler idle when off; routes not registered in the web app when off.

## TDD

- Failing test first: `testing/features/F053/api/sync_tests.rs::sync_request_conflicts_while_active`, `::sync_repeated_cursor_writes_nothing`, `::sync_writes_with_provenance_links`, `::sync_if_empty_skips_filled_cells`, `::sync_unmatched_create_adds_rows`, `::sync_deletion_clear_empties_cells`, `::sync_both_changed_records_conflict`, `::sync_sheet_denied_when_owner_lost_access`, `::sync_too_many_rows_fails_before_write`, `::listener_debounces_and_ignores_own_writes`; `testing/features/F053/api/conflict_tests.rs::resolve_keep_target_writes_value`, `::resolve_rejects_moved_row`, `::resolve_non_admin_denied`; `testing/features/F053/frontend/PreviewTab.test.tsx::shows_counts_and_change_markers`, `ConflictsTab.test.tsx::conflicts_tab_resolves_keep_target`, `::shows_row_moved_notice_on_conflict`, `FieldMapTable.test.tsx::flags_incompatible_pair_inline`, `MappingListPage.test.tsx::hides_sync_for_non_admin`
- Targeted command: `cargo xtask test-feature F053`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: seeded mapping with completed run and two open conflicts; recorded event payloads for the listener; MSW handlers; role-switching session helper

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Consumer, listener, and scheduler registered in `services/worker/src/main.rs`; routes mounted at `/w/:workspaceId/datamesh` and `/w/:workspaceId/datamesh/:mappingId`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S106
- [ ] `finished_at` recorded
