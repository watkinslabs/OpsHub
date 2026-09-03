# F054 frontend cases

File: `testing/features/F054/frontend/{FlowBuilderPage.test.tsx,StepForm.test.tsx,RunConsolePage.test.tsx,StepTimeline.test.tsx}`. Vitest with MSW. Flag `F054_FEATURE`.

- `FlowBuilderPage.test.tsx::builder_rejects_second_trigger` — FR-F054-01: adding a second trigger shows inline error and disables publish.
- `FlowBuilderPage.test.tsx::publish_dialog_shows_graph_errors` — FR-F054-05: 409 `cycle` renders the offending step highlighted with the message.
- `FlowBuilderPage.test.tsx::shows_stale_banner_on_conflict` — FR-F054-05: PATCH 409 shows `This flow changed` with reload.
- `FlowBuilderPage.test.tsx::shows_not_entitled_panel` — FR-F054-13: `useModuleAllowed('bridge')` false renders `ModuleNotEntitled` with reason.
- `StepForm.test.tsx::connector_form_lists_owner_connections` — FR-F054-03: only connections the editor may use appear; action input fields come from the schema.
- `StepForm.test.tsx::wait_form_bounds_delay` — FR-F054-09: delay under 1 minute or over 30 days blocks save.
- `StepForm.test.tsx::transform_form_rejects_cross_sheet_reference` — FR-F054-04: expression with a cross-sheet function shows a validation message.
- `RunConsolePage.test.tsx::console_retry_button_only_on_failed_step` — FR-F054-10: `Retry step` rendered for the failed Slack step only.
- `RunConsolePage.test.tsx::payload_viewer_shows_redaction_markers` — FR-F054-08: `authorization` value renders `***` with a `redacted` label.
- `RunConsolePage.test.tsx::polls_while_run_active` — FR-F054-15: `running` run refetches every 5 s; `succeeded` stops polling.
- `RunConsolePage.test.tsx::viewer_has_no_retry_or_cancel` — FR-F054-14: viewer session hides both actions and shows read-only label.
- `RunConsolePage.test.tsx::shows_error_banner_with_correlation_id` — NFR-F054-04: 500 response shows banner with `correlation_id` and retry.
- `StepTimeline.test.tsx::keyboard_navigation_and_live_region` — NFR-F054-03: arrow keys move between steps; status change announces `Step 3 succeeded`.
- `RunConsolePage.test.tsx::offline_disables_actions` — FR-F054-15: `navigator.onLine=false` shows offline badge and disables retry and cancel.

Evidence: Vitest JUnit under `testing/evidence/F054/frontend/`.
