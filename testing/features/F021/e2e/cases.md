# F021 e2e cases

File: `testing/features/F021/e2e/report.spec.ts`. Playwright against seeded tenant. Flag `F021_FEATURE`.

- `build_three_sheet_report_and_refresh` — FR-F021-01, FR-F021-03, FR-F021-07: editor creates "Portfolio status", joins Risks and Budget to Projects, saves, refreshes, and sees 120 rows with `computed_at`.
- `group_and_calculated_field_visible` — FR-F021-05, FR-F021-06: group by owner and add `Days late`; headers show sums and rows show computed values.
- `stale_banner_after_source_edit` — FR-F021-09, FR-F021-13: second session edits a Projects row; viewer reload shows the stale banner; refresh clears it.
- `restricted_viewer_sees_notice` — FR-F021-10: restricted viewer opens the report, sees no Risks rows and the restricted-sources bar.
- `viewer_cannot_edit_or_refresh` — FR-F021-15, NFR-F021-02: viewer sees read-only editor and no refresh control.
- `non_member_sees_not_found` — FR-F021-13: user outside the workspace opens the report URL → not-found page.
- `keyboard_only_join_and_filter` — FR-F021-15, NFR-F021-03: no mouse; join and filter added; live region announces "Join added".

Evidence: Playwright traces and videos under `testing/evidence/F021/e2e/`.
