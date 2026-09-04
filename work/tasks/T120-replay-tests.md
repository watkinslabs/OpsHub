---
id: T120
type: task
status: planned
parent_epic: E006
parent_feature: F030
parent_story: S060
depends_on: [S060]
owned_paths: [crates/domain/src/connectors/replay.rs, services/api/src/connectors/handlers_replay.rs, apps/web/src/features/connectors/**, testing/features/F030/**]
feature_flag: F030_FEATURE
branch: t120-replay-tests
started_at: null
finished_at: null
---

# T120 — Replay and replay tests

## Identity

- Parent story: `S060` CRM and file sync
- Owner: platform
- Branch: `t120-replay-tests`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 7, 9; `docs/capability-contracts.md` row F030

## Objective

Implement run replay — full, failed-only, and dry-run — with its API route, conflict and replay UI, and the E2E, accessibility, and performance suites that prove idempotency and the F030 budgets end to end.

## Specification

- Owned paths: `crates/domain/src/connectors/replay.rs`, `services/api/src/connectors/handlers_replay.rs`, `apps/web/src/features/connectors/{ConflictQueue.tsx, ConflictDiff.tsx, MergeChooser.tsx, FailedRecordTable.tsx, ReplayDialog.tsx}`, `testing/features/F030/{e2e,accessibility,performance,requirements}/**`; no persistence file is created here — replay reads and writes through the `crates/persistence/src/connectors/` repositories added by T117 and T119
- Contract/input: `POST /api/v1/sync-runs/{id}/replay` body `{ dry_run?: bool, only_failed?: bool }` with `Idempotency-Key`; response `ReplayResponse { run_id?, would_create, would_update, would_skip, would_conflict, samples: [{ external_id, action, field_diffs }] }`.
- Output/behavior: `replay.rs` starts a new run with `trigger: replay` from the source run's `cursor_before`, or over only the external IDs returned by `SyncRunRepository::list_failed_records_for_replay(run_id)` when `only_failed` is true; idempotency comes from `sync_record_links` compared on `external_version`, so an already-applied record is counted `skipped` and never rewritten; `dry_run: true` executes the plan and mapping stages, collects the projected outcome, and commits nothing, returning at most 50 samples; replaying a `queued` or `running` run returns `409 conflict`; replay honors the sync's current mappings, not the mappings at the time of the source run, and records both mapping versions on the run; the UI adds the conflict queue with per-field `Keep OpsHub`, `Keep external`, and `Merge` (per-field chooser), bulk keep-external capped at 100 selected rows, the failed-record table paging `sync_run_failed_records` rows with `external_id`, classification and provider code, and `Replay` and `Dry-run replay` confirmations that name the record count; every state is keyboard reachable, states use text plus icon, and the conflict diff reads OpsHub then external in sequence for screen readers.
- Data access: `replay.rs` and `handlers_replay.rs` contain no SQL — the replay plan loads mappings, cursors, failed records, and record links through the `crates/persistence/src/connectors/` repository traits, and the dry-run projection runs the plan and mapping stages inside a `UnitOfWork` that is rolled back, so nothing is committed. Every suite in this task follows the same rule: fixtures are built and assertions are read through `SyncRepository`, `SyncMappingRepository`, `SyncRunRepository`, `SyncCursorRepository`, `SyncConflictRepository`, and `SyncRecordLinkRepository`, and no test opens a pool or issues a `sqlx::query*` of its own; the database lane asserts the normalized shape — one `sync_conflict_fields` row per conflicting field, one `sync_run_failed_records` row per failed external ID per run, `sync_mapping_transform_args` and `sync_mapping_value_map` rows behind every non-`identity` transform, `sync_database_objects` rows behind the `database` allowlist, and no `jsonb` column in the module beyond `sync_mappings.default_value`, the three `sync_conflict_fields` value columns, and `sync_run_failed_records.provider_payload` (decision sections 2 and 2.1).
- Dependencies: T119 run engine, conflict queue, and record links; T118 mapping evaluation for the dry-run projection; T117 routes and run history; F028 idempotency middleware.
- Feature flag: `F030_FEATURE` gates the replay route and the conflict and replay UI.

## TDD

- Failing test first: `testing/features/F030/api/replay_tests.rs::replay_starts_from_source_cursor_before`, `::replay_only_failed_skips_applied_records`, `::dry_run_replay_writes_nothing`, `::replay_of_running_run_conflicts`, `::replay_uses_current_mappings_and_records_versions`; `testing/features/F030/database/constraint_tests.rs::conflict_fields_row_per_changed_field`, `::failed_record_rows_survive_only_failed_replay`, `::no_unaudited_jsonb_column_remains_in_connectors`; `testing/features/F030/frontend/ConflictDiff.test.tsx::shows_both_values_per_field`; `testing/features/F030/frontend/MergeChooser.test.tsx::requires_a_choice_for_every_conflicting_field`; `testing/features/F030/e2e/syncs.spec.ts::build_jira_sync_and_first_run`, `::resolve_conflict_from_queue`, `::replay_failed_run_from_history`; `testing/features/F030/accessibility/syncs.a11y.spec.ts::conflict_queue_has_no_serious_violations`, `::mapping_rows_reorder_without_pointer`; `testing/features/F030/performance/run_bench.rs::ten_thousand_records_under_ten_minutes`, `::sync_and_conflict_reads_p95_under_500ms`, `::mapping_preview_under_one_second`
- Targeted command: `cargo xtask test-feature F030`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/connectors.rs` partial run with 40 failed records out of 500, a sync with 3 open conflicts, and a 10,000-record generator; `testing/harness/connectors/` mocks with a failure mode that can be switched off between the original run and the replay; Playwright project seeded with tenant A and an integration-admin

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Replay route mounted through `services/api/src/connectors/routes.rs`; conflict and replay UI reachable from `/admin/syncs/:syncId`
- [ ] Every FR-F030 and NFR-F030 id in `testing/features/F030/requirements/cases.md` maps to a passing case
- [ ] Owned-path check passes; file limit, lint, axe, and performance gates pass
- [ ] Handoff evidence recorded in S060
- [ ] `finished_at` recorded
