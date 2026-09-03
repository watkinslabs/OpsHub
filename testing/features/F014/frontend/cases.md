# F014 frontend cases

File: `testing/features/F014/frontend/{FormBuilderPage.test.tsx,ConditionEditor.test.tsx,PublicFormPage.test.tsx,SubmissionsList.test.tsx}`. Vitest with MSW. Flag `F014_FEATURE`.

- `renders_palette_from_sheet_columns` — FR-F014-01: 12 typed columns appear in `FieldPalette` grouped by type.
- `shows_loading_skeleton_then_builder` — FR-F014-01: pending query shows skeleton; resolves to canvas and preview.
- `shows_error_banner_with_correlation_id` — NFR-F014-04: 500 response shows banner containing `correlation_id` and retry.
- `shows_denied_state_for_submitter` — FR-F014-18: submitter role renders read-only notice and no publish control.
- `evaluator_matches_shared_fixtures` — FR-F014-03: `conditions.ts` returns the expected boolean for all 64 cases in `conditions.json`.
- `preview_hides_field_when_condition_false` — FR-F014-03: `FormPreview` hides "Budget" until "Type" is "Purchase" and announces the change.
- `field_editor_validates_rule_by_column_type` — FR-F014-02: regex control disabled for number column; min/max disabled for text.
- `publish_dialog_shows_token_once` — FR-F014-04: publish resolves with token; reopening dialog shows masked value and rotate action.
- `share_dialog_embeds_iframe_snippet` — FR-F014-16: embed tab renders `<iframe src="/public/forms/{token}">` and copy button.
- `stale_conflict_shows_reload_banner` — FR-F014-04: PATCH 409 shows `This form changed` banner.
- `renders_conditional_field_after_value` — FR-F014-03: public page shows "Budget" only after "Type" = "Purchase".
- `shows_field_errors_from_response` — FR-F014-12: 400 with `field_errors.budget` renders message under the field and moves focus.
- `restores_local_draft` — FR-F014-14: values saved under `form-draft:{token}` repopulate after remount.
- `shows_closed_notice` — FR-F014-15: schema with `closed: true` renders `ClosedNotice` with `opens_at`.
- `offline_keeps_draft_and_disables_submit` — FR-F014-14: `navigator.onLine=false` shows offline badge; submit disabled.
- `confirmation_renders_placeholders` — FR-F014-15: `confirmation_html` with `{{submission.id}}` rendered after success.
- `submissions_list_filters_by_status` — FR-F014-17: status filter re-queries with `status=rejected`; rows link to `row_id`.

Evidence: Vitest JUnit under `testing/evidence/F014/frontend/`.
