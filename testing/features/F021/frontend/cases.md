# F021 frontend cases

File: `testing/features/F021/frontend/{ReportEditor.test.tsx,JoinBuilder.test.tsx,FilterBuilder.test.tsx,ReportViewer.test.tsx}`. Vitest with MSW. Flag `F021_FEATURE`.

- `renders_rows_and_group_headers` — FR-F021-15: seeded response renders 3 group headers with aggregates and 120 rows.
- `shows_computing_state_and_polls` — FR-F021-07: `latest_snapshot.status queued` shows progress badge and refetches every 2 s.
- `shows_stale_banner_and_refresh` — FR-F021-09: `meta.stale true` shows banner with `computed_at` and `Refresh now` calling `refreshReport`.
- `shows_restricted_sources_bar` — FR-F021-10: `restricted_sources` non-empty renders the info bar and emits `report_restricted_sources_shown`.
- `hidden_columns_absent_from_table` — FR-F021-10: `hidden_columns` entries produce no column header.
- `join_builder_keyboard_add_join` — FR-F021-03: keyboard-only add of `Risks.project = Projects.id` updates the definition draft.
- `join_builder_shows_type_mismatch_error` — FR-F021-03: 400 with `definition.joins[0]` highlights the join row.
- `filter_builder_limits_depth` — FR-F021-04: nesting past depth 4 disables `Add group`.
- `calculated_field_editor_shows_parse_error` — FR-F021-06: 400 message shown inline under the expression.
- `shows_denied_state_for_viewer` — FR-F021-15: viewer role renders editor read-only and hides `Save`.
- `shows_error_banner_with_correlation_id` — NFR-F021-04: 500 shows banner with `correlation_id` and retry.
- `offline_disables_refresh` — FR-F021-15: `navigator.onLine=false` disables `Refresh now` and shows the badge.

Evidence: Vitest JUnit under `testing/evidence/F021/frontend/`.
