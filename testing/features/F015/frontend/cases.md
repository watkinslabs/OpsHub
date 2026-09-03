# F015 frontend cases

File: `testing/features/F015/frontend/{TemplateCatalogPage.test.tsx,ProvisionDialog.test.tsx,ProvisioningStatus.test.tsx,BaselineList.test.tsx,CaptureBaselineDialog.test.tsx,VariancePanel.test.tsx}`. Vitest with MSW. Flag `F015_FEATURE`.

- `catalog_renders_builtins_and_category_filter` — FR-F015-15: ten built-in cards; selecting `IT` narrows to one plus tenant templates.
- `catalog_hides_provision_for_non_admin` — FR-F015-14: editor role sees cards without `Provision` and with the explanation.
- `catalog_shows_empty_state_with_browse_builtins` — FR-F015-15: no tenant templates and `include_builtin=false` renders `No templates yet`.
- `submits_with_workspace_start_date_roles` — FR-F015-06: dialog calls `provision` with `workspace_id`, `start_date`, `role_assignments`.
- `shows_not_published_field_error` — FR-F015-06: 400 `not_published` renders under the version picker.
- `announces_step_progress` — NFR-F015-03: polled run moves `rows` from running to completed and the live region reads `Rows 120 of 120 complete`.
- `shows_failed_run_with_rollback_badge` — FR-F015-08: `failed` run renders the failing step, error code, `Rolled back` badge, and `Retry provisioning`.
- `stops_polling_when_completed` — FR-F015-09: after `completed` no further `getRun` calls; `Open project` links to the first sheet.
- `lists_baselines_with_row_count` — FR-F015-11: three baselines sorted by captured date with `row_count` and measures.
- `hides_capture_for_non_admin` — FR-F015-14: editor sees the list without `Capture baseline`.
- `validates_name_and_measures` — FR-F015-10: empty name and no measures block submit; 409 `limit` shows the message.
- `variance_panel_shows_totals` — FR-F015-12: totals cards read `1 slipped`, `1 added`, `1 removed`, `Max slip 3d`.
- `status_filter_narrows_rows` — FR-F015-12: choosing `Slipped` leaves one row.
- `open_in_gantt_sets_baseline_param` — FR-F015-15: button navigates with `?baseline_id=<id>`.
- `shows_error_banner_with_correlation_id` — NFR-F015-04: 500 on variance renders banner containing `correlation_id` and retry.
- `offline_disables_provision_and_capture` — FR-F015-15: `navigator.onLine=false` disables both buttons and shows the badge.

Evidence: Vitest JUnit under `testing/evidence/F015/frontend/`.
