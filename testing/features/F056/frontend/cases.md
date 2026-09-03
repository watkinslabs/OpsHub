# F056 frontend cases

File: `testing/features/F056/frontend/{PivotBuilder.test.tsx,PivotGrid.test.tsx,OutputHistory.test.tsx,MaterializeDialog.test.tsx}`. Vitest with MSW. Flag `F056_FEATURE`.

- `adds_and_reorders_dimensions_by_keyboard` — FR-F056-14: Enter adds a column chip; Alt+ArrowDown reorders; live region announces.
- `blocks_fourth_row_dimension` — FR-F056-01: fourth row dimension disabled with hint "Up to 3 row dimensions".
- `measure_editor_filters_aggregates_by_type` — FR-F056-03: text column offers only `count` and `count_distinct`.
- `shows_loading_skeleton_then_grid` — FR-F056-14: pending outputs query shows 6 skeleton rows, then cells.
- `shows_empty_state_with_compute_now` — FR-F056-14: no outputs renders call to action.
- `polls_until_terminal_status` — FR-F056-05: chip goes queued → running → succeeded, polling stops after terminal.
- `shows_stale_banner` — FR-F056-09: `stale: true` renders recompute banner; click emits `pivot_stale_recompute_clicked`.
- `shows_error_with_error_code_and_correlation_id` — NFR-F056-04: failed output shows `timeout` and correlation ID.
- `viewer_sees_read_only_output` — FR-F056-14: viewer role hides builder, compute, and materialize.
- `unentitled_tenant_sees_upsell` — FR-F056-04: 403 with `entitlement: pivot` renders `EntitlementUpsell`.
- `materialize_dialog_opens_new_sheet` — FR-F056-10: success navigates to `/w/:workspaceId/sheets/:sheetId`.
- `offline_disables_compute_and_materialize` — FR-F056-14: `navigator.onLine=false` disables actions with offline badge.

Evidence: Vitest JUnit under `testing/evidence/F056/frontend/`.
