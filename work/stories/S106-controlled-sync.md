---
id: S106
type: story
status: planned
parent_epic: E008
parent_feature: F053
depends_on: [S105]
owned_paths: [crates/domain/src/datamesh/**, services/api/src/datamesh/**, services/worker/src/datamesh/**, apps/web/src/features/datamesh/**, testing/features/F053/**]
feature_flag: F053_FEATURE
branch: s106-controlled-sync
started_at: null
finished_at: null
---

# S106 — Controlled sync

## Identity

- Parent feature: `F053` DataMesh
- Owner: platform
- Branch: `s106-controlled-sync`
- Decision references: `docs/architecture-decisions.md` sections 3, 4, 6, 7; `docs/capability-contracts.md` row F053

## Vertical slice

As a data administrator, I want to run a mapping manually, on source changes, or on a schedule, have it write matched fields with provenance and never overwrite a concurrent edit, and resolve every conflict from a dedicated tab, so that reference data converges across sheets under my control.

Out of this slice: mapping definition and preview (S105); automatic conflict resolution policies; multi-source mappings.

## Requirements

- **SR-S106-01:** `POST /api/v1/datamesh/mappings/{id}/sync` returns `202` with a `queued` run within 2 seconds, rejects a second active run with `409 already_active`, and a repeated `source_version_cursor` finishes `succeeded` with zero writes (covers FR-F053-05).
- **SR-S106-02:** The worker writes matched fields through the F008 bulk cell service as the owner honouring `overwrite`, applies `unmatched_policy` and `deletion_policy`, attaches F009 `datamesh` links to every written cell, and fails with `sheet_denied` when the owner lost `sheet-editor`; changed-row sets above `max_rows_per_sync` fail with `too_many_rows` before writing (FR-F053-06, FR-F053-10, FR-F053-13).
- **SR-S106-03:** Bidirectional maps write back target-only changes and record `both_changed` conflicts with both values and versions when both sides changed (FR-F053-07).
- **SR-S106-04:** `GET /api/v1/datamesh/mappings/{id}/conflicts` pages open conflicts with `kind` and `status` filters; `POST /api/v1/datamesh/conflicts/{id}/resolve` applies `keep_source`, `keep_target`, or `manual_value`, marks the conflict resolved, and returns `409 conflict` when either row version moved (FR-F053-08).
- **SR-S106-05:** `on_change` mappings run at most once per 60 seconds per mapping from source-sheet row and cell events, ignoring events tagged `source = datamesh`; `scheduled` mappings run by cron; finished runs publish `mapping.synced.v1` and each conflict publishes `mapping-conflict.detected.v1` (FR-F053-09, FR-F053-11).
- **SR-S106-06:** `MappingEditorPage` with `Setup`, `Preview`, `Runs`, and `Conflicts` tabs renders key and field map tables, preview counts and sample with change markers, run history polling while active, and side-by-side conflicts with `ResolveDialog`, with loading, empty, error, denied, not-entitled, stale, and offline states, and passes axe (FR-F053-14, NFR-F053-03).
- **SR-S106-07:** Non-`data-admin` users see everything read-only without `Sync now` or resolve; navigation shows `DataMesh` only when `useModuleAllowed('datamesh')` is true (FR-F053-12, FR-F053-14).
- **SR-S106-08:** A 10,000-changed-row sync finishes in under 2 minutes; conflicts list p95 under 500 ms; runs retry three times, time out at 15 minutes, and dead-letter with the reason on the run (NFR-F053-01, NFR-F053-04).

## Surfaces

- Infrastructure/container: JetStream subject `datamesh.sync` and consumer on the sheet row/cell event subjects
- Rust service/API: `crates/domain/src/datamesh/{run.rs, plan.rs, conflict.rs, service_sync.rs}`; `services/api/src/datamesh/{handlers_sync.rs, handlers_conflict.rs}`; `services/worker/src/datamesh/{sync_consumer.rs, writer.rs, change_listener.rs, scheduler.rs}`
- Data/migration: none new; uses the S105 tables
- React/UI: `apps/web/src/features/datamesh/{MappingListPage.tsx, MappingRow.tsx, MappingEditorPage.tsx, SheetPairPicker.tsx, MatchKeyTable.tsx, FieldMapTable.tsx, FieldMapRow.tsx, ExpressionField.tsx, SyncModeFields.tsx, PreviewTab.tsx, PreviewCounts.tsx, PreviewTable.tsx, RunsTab.tsx, RunRow.tsx, ConflictsTab.tsx, ConflictRow.tsx, ResolveDialog.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: seeded mapping with a completed run and two open conflicts; recorded `row.updated.v1` payloads for the listener; MSW handlers for component tests; Playwright against the real API

## TDD harness

- Test path: `testing/features/F053/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F053_FEATURE`
- Targeted command: `cargo xtask test-feature F053`
- Full command: `cargo xtask test-all`
- First failing tests: `sync_request_conflicts_while_active`, `sync_writes_with_provenance_links`, `sync_both_changed_records_conflict`, `resolve_rejects_moved_row`, `listener_debounces_and_ignores_own_writes`, `conflicts_tab_resolves_keep_target`, `create_mapping_preview_sync_resolve`

## Exit criteria

- [ ] Requirement tests SR-S106-01 through SR-S106-08 written first and failing
- [ ] Tasks T211 and T212 complete; UI wired to real API through generated client
- [ ] Unit, API, worker, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `apps/web/src/features/datamesh/MappingEditorPage.tsx` mounted at `/w/:workspaceId/datamesh/:mappingId`; `services/worker/src/datamesh/sync_consumer.rs` registered in `services/worker/src/main.rs`
- [ ] Handoff evidence recorded in the F053 ticket
