---
id: S044
type: story
status: planned
parent_epic: E005
parent_feature: F022
depends_on: [S043]
owned_paths: [crates/domain/src/metrics/**, services/api/src/metrics/**, services/worker/src/metrics/**, apps/web/src/features/metrics/**, testing/features/F022/**]
feature_flag: F022_FEATURE
branch: s044-rollups-trends
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 3, 6, 7
- Capability contract: `docs/capability-contracts.md` row F022

# S044 — Rollups/trends

## Identity

- Parent feature: `F022` Metrics and summaries
- Owner: platform
- Branch: `s044-rollups-trends`
- Decision references: `docs/architecture-decisions.md` sections 3, 6, 7; `docs/capability-contracts.md` row F022

## Vertical slice

As a leader, I want a KPI card that shows the current value, how it compares to the previous period or target, and a sparkline of the trend at the grain I choose, and I want stale numbers to refresh themselves, so that weekly reviews run from live governed figures.

## Requirements

- **SR-S044-01:** `values?grain=` rolls daily buckets into week, month, or quarter aligned to `period.timezone` and `week_start`, summing `count`/`sum`, weighting `avg` by `sample_count`, and recomputing `count_distinct` from the source; a finer grain returns `400 invalid` (FR-F022-08).
- **SR-S044-02:** `comparison` yields `delta_abs`, `delta_pct`, and `direction` per FR-F022-09 for `previous_period`, `same_period_last_year`, and `target`, with `flat` under 0.5% (FR-F022-09).
- **SR-S044-03:** `formatted` follows the viewer locale for `number`, `currency`, `percent`, and `duration` via the F049 formatter (FR-F022-10).
- **SR-S044-04:** `meta.stale` is derived from `source_versions` and the newest report snapshot; the stale sweeper enqueues at most one recompute per `scope_key` per 5 minutes and prunes scopes unread for 14 days (FR-F022-07).
- **SR-S044-05:** `KpiCard` renders `formatted`, delta text, direction color, target progress, and `Sparkline`, with loading, empty, error, computing, stale, denied, and offline states, and exposes value and direction as text for assistive technology (FR-F022-13, NFR-F022-03).
- **SR-S044-06:** `MetricEditor` builds the metric from a report or sheet with source, measure, filters, period, format, target, comparison, and scope policy, shows field errors inline, and previews the card (FR-F022-13).
- **SR-S044-07:** `values` responds under 300 ms p95 from cache and a 100,000-row recompute completes under 30 s (NFR-F022-01).

## Surfaces

- Infrastructure/container: none
- Rust service/API: `crates/domain/src/metrics/{rollup.rs, stale.rs}`; `services/api/src/metrics/handlers_values.rs` grain and comparison parameters; `services/worker/src/metrics/stale_sweeper.rs`
- Data/migration: none new
- React/UI: `apps/web/src/features/metrics/{MetricEditor.tsx, MeasurePicker.tsx, PeriodForm.tsx, FormatForm.tsx, TargetForm.tsx, KpiCard.tsx, KpiDelta.tsx, Sparkline.tsx, MetricPreview.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: 52-week value series with DST weeks; MSW handlers for `values` in computing, stale, and denied states; 100,000-row source for the performance lane

## TDD harness

- Test path: `testing/features/F022/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F022_FEATURE`
- Targeted command: `cargo xtask test-feature F022`
- Full command: `cargo xtask test-all`
- First failing tests: `rollup_week_aligns_to_timezone_and_week_start`, `rollup_avg_weighted_by_sample_count`, `comparison_direction_down_is_good`, `stale_sweeper_enqueues_once_per_five_minutes`, `kpi_card_shows_delta_and_direction_text`, `metric_values_p95`

## Exit criteria

- [ ] Requirement tests SR-S044-01 through SR-S044-07 written first and failing
- [ ] Tasks T087 and T088 complete; UI wired to the real API through the generated `MetricsApi` client
- [ ] Unit, API, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `apps/web/src/features/metrics/KpiCard.tsx` exported for dashboards and `MetricEditor.tsx` mounted at `/w/:workspaceId/metrics/:metricId/edit`
- [ ] Handoff evidence recorded in the F022 ticket
