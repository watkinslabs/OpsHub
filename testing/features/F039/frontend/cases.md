# F039 frontend cases

File: `testing/features/F039/frontend/{ProposalCard.test.tsx,FormulaDiff.test.tsx,PlanDiff.test.tsx,PreviewTable.test.tsx,ExcludedSourcesNotice.test.tsx,ApplyConfirmDialog.test.tsx,AiPanels.test.tsx,AiSettingsPage.test.tsx}`. Vitest with MSW. Flag `F039_FEATURE`.

- `renders_formula_explanation_fields_and_confidence_bucket` — FR-F039-01: card shows the formula, explanation, chips for `Status` and `Due date`, and `medium` for confidence `0.62`.
- `renders_limitations_when_present` — FR-F039-01: two `limitations` entries render as a labelled list; an empty array renders no list.
- `marks_additions_and_removals_with_text_not_color` — FR-F039-13, NFR-F039-03: `FormulaDiff` emits `ins`/`del` elements with the visible labels `Added`, `Removed`, `Changed`.
- `renders_stale_banner_with_regenerate` — FR-F039-13: `stale: true` renders the changed-baseline banner and a `Regenerate` action.
- `plan_diff_groups_changes_by_definition_section` — FR-F039-13: `PlanDiff` renders headed groups for `sources`, `joins`, `filters`, `group_by`, `aggregates`, `calculated_fields`.
- `shows_f035_error_code_badge_per_row` — FR-F039-02: a preview row with `error_code: "missing_reference"` renders that badge with a tooltip naming the reference.
- `shows_restricted_sources_and_hidden_columns_notice` — FR-F039-06: executed rows with `meta.restricted_sources` render the notice above the table.
- `excluded_sources_listed_with_reason_in_words` — FR-F039-03: `excluded_sources` reason `denied` renders as "no access" naming the sheet.
- `apply_is_only_reachable_through_confirmation` — FR-F039-11: clicking `Apply` opens the dialog; `applyProposal` fires only after confirming and carries `Idempotency-Key` and `If-Match`.
- `conflict_response_shows_current_version_and_keeps_proposal` — FR-F039-11: a `409` renders the conflict banner with `current_version` and leaves the proposal actionable.
- `rate_limited_shows_resets_at` — FR-F039-15: `429` with `limit: "per_user_daily"` renders the daily-limit message and `resets_at`.
- `ai_disabled_and_not_entitled_render_distinct_states` — FR-F039-14, FR-F039-15: `reason: "ai_disabled"` and `reason: "not_entitled"` render different copy and different actions.
- `expired_proposal_shows_regenerate` — FR-F039-12: `current_status: expired` renders the expired state with `Regenerate` and no `Apply`.
- `cancel_aborts_generation_and_restores_focus` — FR-F039-16, NFR-F039-03: cancel aborts the request and returns focus to the prompt box.
- `error_banner_shows_correlation_id` — NFR-F039-04: a `502 unavailable` renders the banner with `correlation_id` and `Retry`.
- `telemetry_events_carry_no_prompt_text` — NFR-F039-02: emitted `ai_prompt_submitted` and `ai_proposal_shown` payloads contain `kind`, `request_id`, and confidence bucket only.
- `non_admin_sees_denied_page` — FR-F039-14: a sheet-editor loading `/admin/ai-settings` sees the denied page.
- `panel_stacks_to_single_column_below_768` — FR-F039-16: at 360 px the diff renders one column and no horizontal page scroll.

Evidence: Vitest JUnit and MSW request logs under `testing/evidence/F039/frontend/`.
