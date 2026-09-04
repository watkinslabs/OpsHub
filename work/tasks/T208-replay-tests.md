---
id: T208
type: task
status: planned
parent_epic: E008
parent_feature: F052
parent_story: S104
depends_on: [T207]
owned_paths: [testing/features/F052/**]
feature_flag: F052_FEATURE
branch: t208-replay-tests
started_at: null
finished_at: null
---

# T208 — Replay tests

## Identity

- Parent story: `S104` Mapping and run history
- Owner: platform
- Branch: `t208-replay-tests`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 7, 9; `docs/capability-contracts.md` row F052

## Objective

Complete the F052 harness with the E2E, accessibility, performance, and replay/recovery suites so every FR/NFR in the ticket has executable evidence before acceptance.

## Specification

- Owned paths: `testing/features/F052/e2e/data_shuttle.spec.ts`, `testing/features/F052/accessibility/data_shuttle.a11y.spec.ts`, `testing/features/F052/performance/{import_bench.rs, run_list_bench.rs, ack_bench.rs}`, `testing/features/F052/api/replay_tests.rs`, `testing/features/F052/database/constraint_tests.rs`, `testing/features/F052/requirements/cases.md` (final traceability), `testing/features/F052/README.md`
- Contract/input: seeded tenant A (data-admin, editor, viewer), tenant B without entitlement, `Budget` sheet, sample files in MinIO, one flow with 1,000 historical runs for paging and performance; Playwright sessions per role; scheduler clock advanced through the harness.
- Output/behavior: E2E covers create import flow → run now → counts → replay → archive download, scheduled run firing after the clock passes `next_run_at`, viewer read-only, and not-entitled panel; replay suite proves replay from archive reproduces the original counts, replay after a flow edit still uses the captured `flow_version`, purged archive is refused, and a dead-lettered run can be replayed after the storage stub recovers; accessibility covers axe on list, editor, drawer, keyboard mapping edits, and status text; performance covers 100,000-row import under 10 minutes, run acknowledgement under 2 seconds, run list p95 under 500 ms with 1,000 runs; the requirements table maps FR-F052-01..14 and NFR-F052-01..04 to case IDs with lanes.
- Data access: no test opens a connection or issues SQL of its own; every fixture write and every assertion about persisted state goes through the `crates/persistence/src/data-shuttle/` repositories — seeded flows and their mapping, key, and required-column rows through `ShuttleFlowRepository`, the 1,000 historical runs and their rejection rows through `ShuttleRunRepository`, archives through `ShuttleArchiveRepository` (decision section 2.1). `constraint_tests.rs` proves the normalized shape directly against the database: `shuttle_flow_column_maps` rejects a repeated `source_column` and two source columns mapped to one `column_id`, `shuttle_flow_key_columns` rejects a sixth key ordinal, `shuttle_flow_required_columns` rejects a `column_id` from another sheet, `shuttle_run_rejections` rejects a duplicate `(run_id, row_number)`, deleting a flow cascades its three child tables while `shuttle_runs` is restricted, and `shuttle_run_rejections.cell_values` is the only remaining `jsonb` column in the module.
- Dependencies: T207 UI and routes; F004 compose profile with MinIO and JetStream.
- Feature flag: `F052_FEATURE` on for the suite; one E2E case runs with the flag off and asserts the navigation entry is absent, routes 404, and the scheduler does not fire.

## TDD

- Failing test first: `testing/features/F052/e2e/data_shuttle.spec.ts::create_flow_run_and_replay`, `::scheduled_run_fires_after_next_run_at`, `::viewer_sees_read_only_history`, `::flag_off_hides_module`; `testing/features/F052/api/replay_tests.rs::replay_reproduces_original_counts`, `::replay_after_flow_edit_uses_captured_version`, `::replay_dead_lettered_run_after_recovery`; `testing/features/F052/database/constraint_tests.rs::column_map_rejects_duplicate_source_column`, `::column_map_rejects_two_sources_for_one_column`, `::key_column_rejects_sixth_ordinal`, `::required_column_rejects_foreign_sheet_column`, `::rejection_row_unique_per_run_row_number`, `::flow_delete_cascades_child_rows_and_restricts_runs`; `testing/features/F052/accessibility/data_shuttle.a11y.spec.ts::pages_have_no_serious_axe_violations`; `testing/features/F052/performance/ack_bench.rs::run_request_ack_p95_under_2s`
- Targeted command: `cargo xtask test-feature F052`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: Playwright against the real API and MinIO; k6 script for run acknowledgement; failing-then-recovering storage stub for the dead-letter replay case

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] E2E, accessibility, performance, and replay lanes pass; evidence stored under `testing/evidence/F052/`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S104
- [ ] `finished_at` recorded
