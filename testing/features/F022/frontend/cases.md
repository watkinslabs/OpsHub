# F022 frontend cases

File: `testing/features/F022/frontend/{KpiCard.test.tsx,Sparkline.test.tsx,MetricEditor.test.tsx}`. Vitest with MSW. Flag `F022_FEATURE`.

- `kpi_card_shows_delta_and_direction_text` — FR-F022-13: current 7, delta -2 renders "7" and text "down 2 vs last week" with the better color token.
- `kpi_card_shows_computing_then_value` — FR-F022-06: `meta.status computing` shows badge; refetch resolves to the value.
- `kpi_card_stale_badge_triggers_recompute` — FR-F022-07: `meta.stale true` shows badge; `Recompute` calls `recomputeMetric`.
- `kpi_card_target_progress` — FR-F022-09: target 5 with value 7 shows progress and "2 over target".
- `kpi_card_shows_empty_when_no_series` — FR-F022-13: empty series renders "No data yet".
- `kpi_card_error_shows_correlation_id` — NFR-F022-04: 500 renders "Unavailable" with correlation id and retry.
- `sparkline_has_text_summary` — NFR-F022-03: `aria-label` reads "52 weeks, low 3, high 11, latest 7".
- `metric_editor_validates_measure_type` — FR-F022-01: choosing `sum` on a text column shows the inline error from `field_errors`.
- `metric_editor_owner_scope_disabled_without_policy` — FR-F022-05: scope policy `owner` disabled when tenant policy is off.
- `metric_editor_denied_for_viewer` — FR-F022-13: viewer role renders read-only fields and no `Save`.
- `offline_disables_recompute` — FR-F022-13: `navigator.onLine=false` disables `Recompute`.

Evidence: Vitest JUnit under `testing/evidence/F022/frontend/`.
