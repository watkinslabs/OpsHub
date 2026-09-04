---
id: T283
type: task
status: planned
parent_epic: E003
parent_feature: F071
parent_story: S142
depends_on: [S142, T282]
owned_paths: [apps/web/src/features/migration/**, testing/features/F071/frontend/**]
feature_flag: F071_FEATURE
branch: t283-migration-ui
started_at: null
finished_at: null
---

# T283 — Migration UI

## Identity

- Parent story: `S142` Mapped provisioning
- Owner: platform
- Branch: `t283-migration-ui`
- Decision references: `docs/architecture-decisions.md` sections 3, 4, 6, 9; `docs/capability-contracts.md` row F071

## Objective

Build the migration list, upload, review, and commit-progress surfaces: the per-tab column review table with confidence and inline type override, the grouped issues panel with waive, the gated `Create everything` action, and the progress panel that reports each tab as it lands.

## Specification

- Owned paths: `apps/web/src/features/migration/{MigrationListPage.tsx, MigrationUploadPanel.tsx, MigrationReviewPage.tsx, TabPlanList.tsx, ColumnReviewTable.tsx, TypeOverrideSelect.tsx, ConfidenceChip.tsx, SampleValueList.tsx, IssuePanel.tsx, IssueGroup.tsx, CommitProgressPanel.tsx, CommitConfirmDialog.tsx, api.ts, hooks.ts, routes.ts}`
- Contract/input: the generated `MigrationApi` with `createMigration`, `listMigrations`, `getMigration`, `commitMigration`, and `deleteMigration`; query keys `['migrations', filters, cursor]` and `['migration', id]` polling every 3 s while `analyzing` or `committing`.
- Output/behavior: routes `/w/:workspaceId/migrations` and `/w/:workspaceId/migrations/:migrationId` registered in `apps/web/src/routes.tsx`. `MigrationUploadPanel` posts the F017 upload then `createMigration` and navigates to the review route. `TabPlanList` lists tabs with row counts and per-severity issue badges. `ColumnReviewTable` renders one row per column map with source header, up to 5 sample values, `ConfidenceChip` showing `High`, `Medium`, or `Low` plus the numeric value in monospace, and `TypeOverrideSelect` limited to the twelve F007 types with per-type settings fields; overrides accumulate in a reducer keyed by `column_map_id` and never reach the server before commit. `IssuePanel` groups `Blocking`, `Warning`, and `Information` with counts and a waive action per issue. `Create everything` stays disabled while an unwaived blocking issue or an undecided ambiguous column remains; `CommitConfirmDialog` states the tab count, row count, destination folder, and accepted-ambiguity count, then calls `commitMigration` with the overrides, waived ids, and `accept_ambiguous`. A `400 invalid` maps `field_errors.column_overrides` back onto the offending rows; a `409 conflict` renders the already-committing surface. `CommitProgressPanel` shows per-tab state and committed row counts, announces each completed tab through a polite live region, states that a failed tab's sheet was removed, and on completion links to the first created sheet. Every component composes the F062 loading, empty, error with `correlation_id`, denied, stale, conflict, offline, and success patterns; all colour, spacing, and type come from tokens and every icon from the shared registry.
- Data access: none; the web app holds no SQL and reaches the four `migration` tables only through the F071 API.
- Dependencies: F062 primitives and patterns, F017 upload, F005 workspace tree for the destination folder, F049 for number and date formatting in samples, the F044 generated client.
- Feature flag: `F071_FEATURE` gates the routes and the workspace-tree entry point.

## TDD

- Failing test first: `testing/features/F071/frontend/ColumnReviewTable.test.tsx::review_table_lists_inferred_type_and_confidence`, `::confidence_is_text_and_icon_not_colour_alone`, `::type_override_offers_only_the_twelve_types`; `testing/features/F071/frontend/IssuePanel.test.tsx::issues_grouped_by_severity_with_counts`, `::waiving_last_blocking_issue_enables_commit`; `testing/features/F071/frontend/CommitConfirmDialog.test.tsx::dialog_states_tabs_rows_folder_and_accepted_ambiguities`, `::ambiguous_column_requires_override_or_acceptance`, `::override_error_returns_message_to_offending_row`; `testing/features/F071/frontend/CommitProgressPanel.test.tsx::progress_panel_announces_each_committed_tab`, `::failed_tab_states_its_sheet_was_removed`, `::conflict_renders_already_committing_surface`; `testing/features/F071/frontend/MigrationListPage.test.tsx::viewer_sees_denied_surface_on_migration_route`, `::error_banner_shows_correlation_id`
- Targeted command: `cargo xtask test-feature F071`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: MSW handlers for the five routes with `analyzing`, `ready`, `committing`, `completed`, and `failed` fixtures; a 50-tab preview fixture for virtualisation; fixed clock and UTC

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Routes registered behind the flag; no direct vendor import, no literal colour, spacing, or duration, no icon outside the registry
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S142
- [ ] `finished_at` recorded
