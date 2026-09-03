# F031 e2e cases

File: `testing/features/F031/e2e/{portfolio.spec.ts,portfolio_permissions.spec.ts}`. Playwright against seeded tenant. Flag `F031_FEATURE`.

- `create_portfolio_add_projects_refresh` — FR-F031-01, FR-F031-04, FR-F031-06, FR-F031-13: admin creates "Q4 launches", picks three projects, clicks `Refresh`, sees rows fill and `Last refreshed` update.
- `missing_measure_shows_reason` — FR-F031-05: project without mapped budget column shows `Missing` cell with tooltip `column not in project`.
- `stale_badge_appears_after_threshold` — FR-F031-09: portfolio with `stale_after_seconds: 60`; after clock advance the badge `Stale since` appears; refresh clears it.
- `drill_link_opens_project_sheet` — FR-F031-13: clicking project name opens `/w/{ws}/sheets/{project_sheet_id}` in the same tab.
- `viewer_sees_restricted_row_without_values` — FR-F031-09, FR-F031-12: viewer login shows "Merger" as `Restricted project`, no values, no `Refresh` button.
- `denied_row_has_no_drill_link` — NFR-F031-02: viewer DOM contains no anchor for the restricted row.
- `non_member_sees_not_found` — FR-F031-12: user outside the workspace opens the portfolio URL → not-found page.
- `scheduled_portfolio_refreshes_after_edit` — FR-F031-10: editing a project row then triggering the scheduler tick updates `Last refreshed`.

Evidence: Playwright traces and videos under `testing/evidence/F031/e2e/`.
