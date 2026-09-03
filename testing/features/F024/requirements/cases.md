# F024 requirements cases

Feature: Charts and insights. Flag `F024_FEATURE`. Fixtures `testing/fixtures/charts.rs`, clock `2026-09-03T00:00:00Z`, timezone `America/New_York`, seed `0x0F24`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F024-REQ-001` | FR-F024-01 | api, frontend | spec omitting `formatting` and `error_state` → 400 `invalid` with `field_errors` `spec.formatting` and `spec.error_state`; spec over 32 KB → 400; complete spec accepted |
| `F024-REQ-002` | FR-F024-02 | api | `pie` with 2 measures, `bar` with 3 dimensions, `burndown` without `done_field`, `workload` with a `day` bucket → 400 `invalid` from `ChartError::KindLimit` |
| `F024-REQ-003` | FR-F024-03 | api, performance | bar over report "Portfolio status" → one series per measure, points folded by `Projects.owner`, `meta.scope: viewer`; 21st series and 1,001st point → `truncated: true`; hidden `Budget.margin` → every `y` null |
| `F024-REQ-004` | FR-F024-04 | api, database, e2e | saving a chart widget upserts `chart_definitions` by `widget_id`; `GET /charts/{id}` returns `spec`, `widget_id`, `version`; `PATCH` with `If-Match` purges `widget_cache` and publishes `chart.updated.v1`; stale `If-Match` → 409 `conflict` |
| `F024-REQ-005` | FR-F024-05 | api, frontend | `kpi` resolver returns the F022 values payload under viewer scope; `metric_comparison` returns both metrics with `delta_abs`, `delta_pct`, `direction`; unreadable metric → widget status `denied` |
| `F024-REQ-006` | FR-F024-06 | api | `GET /time-series/{metric_id}` grain week, horizon 30, method `linear` → 5 projected weekly points with `lower`/`upper`; `moving_average` → window mean; 2 available buckets → `projected: []`; `horizon_days: 120` → 400 |
| `F024-REQ-007` | FR-F024-07 | api | read with no stored projection enqueues `charts.project`; job writes `time_series_points`, records `run_id`, publishes `time-series.projected.v1`; replay of the same `run_id` is a no-op; newer metric run keeps `meta.stale: true` |
| `F024-REQ-008` | FR-F024-08 | api, performance | burndown for "Sprint 12" 2026-08-20..2026-09-03 with done values `Done, Cancelled` → 15 daily points, `remaining` falling by rows done each local day, `ideal` linear from 200 to 0, rows created after `start` in `added`; span 367 days → 400; second identical call served from the 60 s cache |
| `F024-REQ-009` | FR-F024-09 | api, frontend | `timeline` returns bars sorted by `start`, null `end_field` → `milestone: true`, 501st bar truncated; `workload` returns cells for ≤ 200 people × 53 buckets with `capacity` 40 h default for `sum` and `over_capacity` set above it |
| `F024-REQ-010` | FR-F024-10 | frontend, e2e | `formatted` follows `formatting` through the F049 formatter in the viewer locale; `timezone` drives bucket edges across the DST day and is echoed in `meta`; empty series → `empty_state.message`; failed query → `error_state.message` with `correlation_id` |
| `F024-REQ-011` | FR-F024-11 | frontend, e2e, accessibility | the eight renderers are registered in the F023 renderer registry and draw from a `ChartData` payload; `ChartSpecEditor` blocks save on a missing declaration; `Show as table` renders the same numbers as an accessible table |
| `F024-REQ-012` | FR-F024-12 | api, e2e | report source without `report-viewer` → 403 `denied`; foreign-tenant chart, sheet, or metric id → 404 `not_found`; `PATCH /charts/{id}` without `Idempotency-Key` → 400 and with it writes audit `chart.update`; both events carry the contract envelope |
| `F024-NFR-001` | NFR-F024-01 | performance | chart query p95 < 800 ms on 100,000 rows with 2 dimensions; burndown p95 < 2 s over 10,000 rows and 90 days; cached time-series p95 < 300 ms; projection job < 5 s; 1,000-point line render < 100 ms |
| `F024-NFR-002` | NFR-F024-02 | api, database | every point computed under the viewer scope; hidden fields yield null measures; `time_series_points` rows separated by `scope_key`; cross-tenant and restricted-source negatives return `not_found` |
| `F024-NFR-003` | NFR-F024-03 | accessibility | axe serious and critical = 0 on all eight renderers; `aria-label` names kind, series count, min, max, latest; table alternative keyboard-reachable; pattern fills at 3:1 contrast; reduced motion disables transitions |
| `F024-NFR-004` | NFR-F024-04 | api, database | projection and burndown jobs retry 3 times, dead-letter on the fourth, and are idempotent by `run_id`; spans carry `tenant_id`, `chart_id`, `metric_id`, `sheet_id`, `scope_key`; `chart_query_duration_seconds`, `projection_failures_total`, `burndown_cache_hits_total` emitted |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F024/`.
