# F040 frontend cases

File: `testing/features/F040/frontend/{InsightCard.test.tsx,InsightFilters.test.tsx,EvidenceTable.test.tsx,DismissDialog.test.tsx,ProposeActionDialog.test.tsx,ActionPreviewDiff.test.tsx,ConfirmActionDialog.test.tsx,ActionRunTimeline.test.tsx,BudgetBanner.test.tsx}`. Vitest with MSW. Flag `F040_FEATURE`.

- `severity_shown_as_text_and_icon` — NFR-F040-03: `InsightCard` renders `High` plus a labelled `AlertTriangle`, never colour alone.
- `card_shows_evidence_count_and_last_seen` — FR-F040-17: `4 records · seen 2 hours ago · occurred 3 times`.
- `evidence_table_links_each_record` — FR-F040-07: `EvidenceTable` renders `Source`, `Record`, `Field`, `Observed`, `Version`, `Seen at` with a deep link per row.
- `evidence_text_is_not_interpreted_as_markup` — FR-F040-16: an escaped `<img onerror=...>` summary renders as literal text with no created element.
- `filters_narrow_by_kind_and_severity` — FR-F040-06: selecting `stalled_work` and `high` issues the filtered query and shows the empty state when none match.
- `dismiss_dialog_explains_suppression_window` — FR-F040-08: choosing `kind_for_scope` states that matching insights are hidden for 30 days.
- `propose_dialog_lists_only_allowed_kinds` — FR-F040-10: exactly the six allowed `action_kind` options are offered.
- `renders_before_and_after_for_each_target` — FR-F040-09: `ActionPreviewDiff` shows one row per target with `Before` and `After` and a caption naming the target count.
- `stale_preview_replaces_diff_in_place` — FR-F040-11: a 409 response swaps in the re-rendered diff with `The data changed since this preview` and a `Re-preview` button.
- `confirm_dialog_restates_target_count_and_risk` — FR-F040-17: the dialog states `4 rows will change`, the risk class, and for `high` the approval that will be requested.
- `confirm_button_is_not_default_focus` — NFR-F040-03: initial focus lands on the dialog heading, not `Confirm`.
- `run_timeline_shows_terminal_states` — FR-F040-13: `queued → running → applied` and the `denied` variant with `error_class` and no applied targets.
- `budget_banner_visible_only_to_tenant_admin` — NFR-F040-05: `BudgetBanner` shows remaining budget for `tenant-admin` and is absent for the manager.
- `rate_limited_scan_shows_countdown` — FR-F040-15: a 429 with `retry_after_seconds: 720` renders `Scan again in 12 minutes`.
- `shows_denied_page_without_entitlement` — FR-F040-01: a viewer without `ai_insights` loading `/insights` sees the denied page.

Evidence: Vitest JUnit under `testing/evidence/F040/frontend/`.
