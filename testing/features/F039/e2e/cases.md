# F039 e2e cases

File: `testing/features/F039/e2e/ai_assist.spec.ts`. Playwright against the seeded tenant with `AI_PROVIDER=recorded` and the socket guard. Flag `F039_FEATURE`, F048 `ai-assist` entitlement `active`.

- `generate_and_apply_formula` — FR-F039-01, FR-F039-02, FR-F039-11, FR-F039-16: a sheet-editor opens the formula editor on `Days late`, asks "days between the due date and today, blank when done", sees the proposal with chips for `Status` and `Due date` and a 5-row preview, confirms `Apply`, and the column shows computed values after the F035 recalculation.
- `compile_preview_and_save_report` — FR-F039-03, FR-F039-06, FR-F039-11: a report-editor asks "open risks per owner across the launch sheets", sees the plan with two sources, clicks `Preview rows`, then `Save as report`, and the new report appears on `/reports` with the same definition.
- `viewer_never_sees_denied_sheet_data` — FR-F039-07, NFR-F039-02: a viewer without `Finance FY26` asks a question that would need it, sees `Finance FY26` under excluded sources, and neither the plan, the explanation, nor the previewed rows contain any value from that sheet.
- `reject_keeps_column_unchanged` — FR-F039-12: the editor rejects a formula proposal with a reason; the column formula is unchanged and the proposal shows as rejected.
- `stale_baseline_blocks_apply` — FR-F039-11, FR-F039-13: a second session changes the column formula; the first session's `Apply` returns the conflict banner with `current_version` and offers `Regenerate`.
- `daily_limit_stops_generation` — FR-F039-15: after 50 requests the panel shows the daily-limit message with `resets_at` and the prompt box is disabled until reset.
- `settings_disable_hides_entry_points` — FR-F039-14, FR-F039-16: a tenant-admin sets `enabled: false`; the formula editor and reports list no longer show the AI entry points and direct navigation shows the disabled state.

Evidence: Playwright traces, screenshots, and the recorded provider call log under `testing/evidence/F039/e2e/`.
