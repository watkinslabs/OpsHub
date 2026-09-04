---
id: T087
type: task
status: planned
parent_epic: E005
parent_feature: F022
parent_story: S044
depends_on: [S044]
owned_paths: [crates/domain/src/metrics/**, crates/persistence/src/metrics/**, services/api/src/metrics/**, services/worker/src/metrics/**, apps/web/src/features/metrics/**, testing/features/F022/api/**, testing/features/F022/frontend/**]
feature_flag: F022_FEATURE
branch: t087-kpi-ui
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 3, 6, 7
- Capability contract: `docs/capability-contracts.md` row F022

# T087 — KPI UI

## Identity

- Parent story: `S044` Rollups/trends
- Owner: platform
- Branch: `t087-kpi-ui`
- Decision references: `docs/architecture-decisions.md` sections 3, 6, 7; `docs/capability-contracts.md` row F022

## Objective

Add grain rollups, comparisons, stale sweeping, and the KPI card and metric editor components so a leader sees a formatted value, trend delta, and sparkline that refresh themselves.

## Specification

- Owned paths: `crates/domain/src/metrics/{rollup.rs, stale.rs}` (no SQL), `crates/persistence/src/metrics/{metric_value_repository.rs, metric_run_repository.rs}` for `list_values`, `prune_runs_older_than`, `prune_unread_scopes`, `services/api/src/metrics/handlers_values.rs` (grain and comparison), `services/worker/src/metrics/stale_sweeper.rs`, `apps/web/src/features/metrics/{MetricEditor.tsx, MeasurePicker.tsx, PeriodForm.tsx, FormatForm.tsx, TargetForm.tsx, KpiCard.tsx, KpiDelta.tsx, Sparkline.tsx, MetricPreview.tsx, api.ts, hooks.ts, routes.ts}`
- Contract/input: generated `MetricsApi` client; `values` query `grain` coarser than or equal to the metric grain; `comparison` per metric; tenant locale from F049 for `formatted`.
- Output/behavior: `rollup.rs` re-buckets by the `period_timezone` and `week_start` columns, sums `count`/`sum`, weights `avg` by `sample_count`, recomputes `count_distinct` from the snapshot, and rejects finer grains with `400 invalid`; `compare.rs` produces `delta_abs`, `delta_pct`, `direction` with `flat` under 0.5%; `stale.rs` marks values stale by joining `metric_run_sources` against current source versions and the newest snapshot; `stale_sweeper.rs` runs every 5 minutes, enqueues at most one recompute per stale `scope_key`, and calls `prune_runs_older_than` and `prune_unread_scopes` for scopes unread for 14 days, holding no SQL itself; `KpiCard` shows `formatted`, `KpiDelta` text (`down 2 vs last week`), target progress bar, `Sparkline` with an `aria-label` summary (`52 weeks, low 3, high 11, latest 7`), and badges for computing and stale with `Recompute`; `MetricEditor` validates inline from `field_errors` and previews the card; states per ticket section 3; telemetry `metric_created`, `metric_recompute_requested`, `kpi_card_rendered`, `kpi_card_opened_source`.
- Dependencies: T086 values route and worker; F005 workspace shell; F049 locale hook.
- Feature flag: `F022_FEATURE` read through the flag hook; editor routes are not registered when off.

## TDD

- Failing test first: `testing/features/F022/api/rollup_tests.rs::rollup_week_aligns_to_timezone_and_week_start`, `::rollup_avg_weighted_by_sample_count`, `::rollup_finer_grain_invalid`, `::comparison_direction_down_is_good`, `::stale_sweeper_enqueues_once_per_five_minutes`; `testing/features/F022/frontend/KpiCard.test.tsx::kpi_card_shows_delta_and_direction_text`, `::kpi_card_shows_computing_then_value`, `::kpi_card_stale_badge_triggers_recompute`; `testing/features/F022/frontend/MetricEditor.test.tsx::shows_measure_type_error_inline`
- Targeted command: `cargo xtask test-feature F022`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: 52-week series with DST weeks; MSW handlers for computing, stale, denied responses; `en-US` and `de-DE` locale fixtures

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Component tests pass; `KpiCard` exported from `apps/web/src/features/metrics/index.ts` for dashboard use
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S044
- [ ] `finished_at` recorded
