---
id: S112
type: story
status: planned
parent_epic: E008
parent_feature: F056
depends_on: [S111]
owned_paths: [crates/domain/src/pivots/**, services/api/src/pivots/**, services/worker/src/pivots/**, apps/web/src/features/pivots/**, testing/features/F056/**]
feature_flag: F056_FEATURE
branch: s112-saved-outputs
started_at: null
finished_at: null
---

# S112 — Saved outputs

## Identity

- Parent feature: `F056` Pivot App
- Owner: platform
- Branch: `s112-saved-outputs`
- Decision references: `docs/architecture-decisions.md` sections 3, 6, 7, 9; `docs/capability-contracts.md` row F056

## Vertical slice

As a report editor, I want to compute a pivot asynchronously, keep the last 20 outputs with stale detection, materialize an output into a sheet, and do all of this from a keyboard-accessible builder, so that summaries are reproducible and shareable as ordinary sheets.

## Requirements

- **SR-S112-01:** `POST /api/v1/pivots/{id}/compute` inserts a `queued` output, enqueues `pivots.compute`, and returns within 2 s; a second compute while one is `queued` or `running` returns `409 conflict` (FR-F056-05).
- **SR-S112-02:** `services/worker/src/pivots/compute_job.rs` runs `run_compute` as the requesting actor, records `source_versions`, `duration_ms`, `row_count`, and `cells`, and publishes `pivot.computed.v1` on `succeeded` and on `failed` with `error_code` in `{ timeout, source_deleted, source_too_large, permission_lost }` (FR-F056-05, FR-F056-07).
- **SR-S112-03:** `GET /api/v1/pivots/{id}/outputs` returns the newest 20 outputs with `stale` computed by comparing `source_versions` to current versions; inserting the 21st prunes the oldest in the same transaction (FR-F056-08, FR-F056-09).
- **SR-S112-04:** `POST /api/v1/pivots/{id}/outputs/{output_id}/materialize` creates a sheet through `sheets::create_sheet` and `sheets::create_row` with one column per dimension and measure and returns `{ sheet_id, version }`; replaying the same `Idempotency-Key` returns the same sheet (FR-F056-10).
- **SR-S112-05:** `services/worker/src/pivots/scheduler.rs` enqueues `hourly` and `daily` pivots at `:00` UTC and skips pivots with an active output (FR-F056-12).
- **SR-S112-06:** `PivotBuilder`, `PivotGrid`, and `OutputHistory` render loading, empty, error, denied, stale, conflict, offline, and success states; viewers get read-only outputs; compute polls every 2 s until terminal (FR-F056-14, NFR-F056-03).
- **SR-S112-07:** Outputs read of 5,000 cells meets NFR-F056-01 and a 100,000-row compute finishes under 30 s p95 (NFR-F056-01).

## Surfaces

- Infrastructure/container: JetStream stream `pivots` with subject `pivots.compute` declared in `services/worker/src/pivots/mod.rs`
- Rust service/API: `crates/domain/src/pivots/{output.rs, service_outputs.rs, materialize.rs}`; `services/api/src/pivots/{handlers_output.rs}`; `services/worker/src/pivots/{mod.rs, compute_job.rs, scheduler.rs}`
- Data/migration: none new; uses tables from S111
- React/UI: `apps/web/src/features/pivots/{PivotListPage.tsx, PivotPage.tsx, PivotBuilder.tsx, SourcePicker.tsx, DimensionPicker.tsx, MeasureEditor.tsx, PivotGrid.tsx, OutputHistory.tsx, OutputStatusChip.tsx, MaterializeDialog.tsx, EntitlementUpsell.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: in-memory JetStream recorder; 100,000-row generator with fixed seed; MSW handlers for output polling

## TDD harness

- Test path: `testing/features/F056/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F056_FEATURE`
- Targeted command: `cargo xtask test-feature F056`
- Full command: `cargo xtask test-all`
- First failing tests: `compute_enqueues_and_returns_queued`, `compute_while_running_conflicts`, `outputs_prune_to_twenty`, `output_stale_after_source_edit`, `materialize_is_idempotent`, `builder_keyboard_reorder_dimensions`, `outputs_read_5k_cells_p95`

## Exit criteria

- [ ] Requirement tests SR-S112-01 through SR-S112-07 written first and failing
- [ ] Tasks T223 and T224 complete; UI wired to real API through generated client
- [ ] Unit, API, worker, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `apps/web/src/features/pivots/PivotPage.tsx` mounted at `/w/:workspaceId/pivots/:pivotId`; worker consumer `services/worker/src/pivots/compute_job.rs` registered in `services/worker/src/main.rs`
- [ ] Handoff evidence recorded in the F056 ticket
