---
id: T223
type: task
status: planned
parent_epic: E008
parent_feature: F056
parent_story: S112
depends_on: [S112]
owned_paths: [crates/domain/src/pivots/**, crates/persistence/src/pivots/**, services/api/src/pivots/**, services/worker/src/pivots/**, apps/web/src/features/pivots/**, testing/features/F056/api/**, testing/features/F056/frontend/**]
feature_flag: F056_FEATURE
branch: t223-pivot-ui
started_at: null
finished_at: null
---

# T223 — Pivot UI

## Identity

- Parent story: `S112` Saved outputs
- Owner: platform
- Branch: `t223-pivot-ui`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 6, 7; `docs/capability-contracts.md` row F056

## Objective

Deliver the compute, outputs, and materialize routes with the worker job and scheduler, and build the pivot builder, grid, and output history pages wired to the real API.

## Specification

- Owned paths: `crates/domain/src/pivots/{output.rs, service_outputs.rs, materialize.rs}`, `crates/persistence/src/pivots/{output_repository.rs, source_version_rows.rs}`, `services/api/src/pivots/handlers_output.rs`, `services/worker/src/pivots/{mod.rs, compute_job.rs, scheduler.rs}`, `apps/web/src/features/pivots/{PivotListPage.tsx, PivotPage.tsx, PivotBuilder.tsx, SourcePicker.tsx, DimensionPicker.tsx, MeasureEditor.tsx, PivotGrid.tsx, OutputHistory.tsx, OutputStatusChip.tsx, MaterializeDialog.tsx, EntitlementUpsell.tsx, api.ts, hooks.ts, routes.ts}`
- Contract/input: `POST /api/v1/pivots/{id}/compute` (no body), `GET /api/v1/pivots/{id}/outputs?cursor&limit`, `POST /api/v1/pivots/{id}/outputs/{output_id}/materialize { sheet_name? }`; job payload `{ tenant_id, pivot_id, output_id, actor_id, correlation_id }`; generated `PivotsApi` client.
- Output/behavior: compute inserts a `queued` output and enqueues `pivots.compute`; the worker loads the definition from `PivotRepository::find_with_definition`, folds with T221 `aggregate::fold`, writes `succeeded`/`failed` with one `pivot_output_source_versions` row per source, and publishes `pivot.computed.v1`; outputs list computes `stale` by joining those rows to current source versions, returns `source_versions` in its unchanged JSON object shape, and prunes past 20 with the source-version rows cascading; materialize reads the definition and `cells` through the repositories and creates a sheet via F006 domain calls with one column per dimension and measure row in `position` order; the UI renders builder chips with keyboard reorder, a grid with frozen first column, an output history with status chips polled every 2 s, the stale banner, the entitlement upsell, and all states in ticket section 3; telemetry `pivot_created`, `pivot_computed`, `pivot_compute_failed`, `pivot_materialized`, `pivot_stale_recompute_clicked`.
- Data access: `crates/persistence/src/pivots/output_repository.rs` implements `PivotOutputRepository` over `pivot_outputs` and `pivot_output_source_versions` with `insert_queued_output`, `find_active_output`, `mark_running`, `mark_terminal`, `list_recent_outputs`, `prune_outputs_beyond_limit`, `record_source_versions`, `list_stale_output_ids`, and `load_cells`; `source_version_rows.rs` maps those rows to and from the `source_versions` object. `output.rs`, `service_outputs.rs`, `materialize.rs`, `handlers_output.rs`, `compute_job.rs`, and `scheduler.rs` hold no SQL and open no connection: the compute transition, the insert-and-prune, and the materialize write (pivot repositories plus the F006 sheet repositories) each run in one `UnitOfWork` under the requesting actor's permission context (decision section 2.1).
- Dependencies: T222 routes and service; F006 `create_sheet`/`create_row`; F004 JetStream consumer harness; F005 workspace shell for the entry point.
- Feature flag: `F056_FEATURE` read through `useFlag`; routes are not registered when off.

## TDD

- Failing test first: `testing/features/F056/api/output_tests.rs::compute_enqueues_and_returns_queued`, `::compute_while_running_conflicts`, `::outputs_prune_to_twenty`, `::output_stale_after_source_edit`, `::materialize_is_idempotent`, `::scheduler_skips_active_output`, `::compute_records_one_source_version_row_per_source`, `::pruned_output_cascades_source_version_rows`; `testing/features/F056/frontend/PivotBuilder.test.tsx::adds_and_reorders_dimensions_by_keyboard`, `OutputHistory.test.tsx::polls_until_terminal_status`, `PivotGrid.test.tsx::shows_stale_banner`
- Targeted command: `cargo xtask test-feature F056`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: in-memory JetStream recorder; MSW handlers replaying queued → running → succeeded

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Worker consumer registered in `services/worker/src/main.rs`; routes mounted behind the flag
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S112
- [ ] `finished_at` recorded
