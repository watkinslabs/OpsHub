---
id: S142
type: story
status: planned
parent_epic: E003
parent_feature: F071
depends_on: [S141, F013]
owned_paths: [apps/web/src/features/migration/**, testing/features/F071/**]
feature_flag: F071_FEATURE
branch: s142-mapped-provisioning
started_at: null
finished_at: null
---

# S142 — Mapped provisioning

## Identity

- Parent feature: `F071` Migration import
- Owner: platform
- Branch: `s142-mapped-provisioning`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 6, 9; `docs/capability-contracts.md` row F071

## Vertical slice

As a sheet editor, I want to read the dry run tab by tab, change the types I disagree with, see and waive what could not be brought over, and then press one button that turns the whole workbook into real sheets with their columns, views, hierarchy, and links — and know that a failure removes what it started rather than leaving me a half-built workspace.

## Requirements

- **SR-S142-01:** The review screen at `/w/:workspaceId/migrations/:migrationId` renders the tab list with row counts and issue badges, the column review table with source header, sample values, inferred type, a labelled confidence chip, and a type select limited to the twelve F007 types, and the issues panel grouped `Blocking`, `Warning`, `Information` with per-issue waive; overrides live in a local reducer keyed by `column_map_id` and are submitted whole with the commit mutation (covers FR-F071-08, FR-F071-16).
- **SR-S142-02:** `Create everything` is disabled while any unwaived `blocking` issue remains and while any column is still `ambiguous` without an override, and the confirm dialog states the tab count, the row count, the destination folder, and the number of accepted ambiguities before the commit request is sent (FR-F071-03, FR-F071-09).
- **SR-S142-03:** `POST /api/v1/migrations/{id}/commit` submitted from the review screen carries `column_overrides`, `sheet_overrides`, `accept_ambiguous`, and `waived_issue_ids` with `Idempotency-Key` and `If-Match`; a `400 invalid` with `field_errors.column_overrides` returns the user to the offending rows with the message attached to each, and a `409 conflict` renders the already-committing surface (FR-F071-09).
- **SR-S142-04:** The commit progress panel polls `GET /api/v1/migrations/{id}` every 3 s, shows each tab moving `pending → committing → committed`, `failed`, or `skipped` with its committed row count, announces each completed tab through a polite live region, and on `completed` offers a link that opens the first created sheet (FR-F071-10, FR-F071-11, NFR-F071-03).
- **SR-S142-05:** A failed tab is shown with its reason and the statement that its sheet was removed, and `DELETE /api/v1/migrations/{id}` from the review or list screen states that every sheet this migration created will be removed, then leaves the destination folder as it was (FR-F071-11).
- **SR-S142-06:** Every surface ships loading, empty, error with `correlation_id`, denied, stale, conflict, offline, and success from the F062 patterns; the entry point is hidden for a viewer or commenter and the route renders the denied surface (FR-F071-16, NFR-F071-03).
- **SR-S142-07:** The seven harness lanes under `testing/features/F071/` cover every FR-F071 and NFR-F071 id, including the resume-after-crash, failed-tab rollback, unresolved-reference, unsupported-view, and permission-negative cases, with fixtures that reach no external network (FR-F071-12, FR-F071-13, FR-F071-14, NFR-F071-04).
- **SR-S142-08:** Performance is asserted rather than asserted-to: 20-tab analysis under 90 s, preview under 800 ms p95 at 50 tabs and 2,000 column maps, a 100,000-row commit under 15 minutes, and parser peak resident memory under 512 MB (NFR-F071-01, NFR-F071-05).

## Surfaces

- Infrastructure/container: no new infrastructure; the screen reads the F071 routes through the generated client and the commit job runs on the F004 worker registered by S141
- Data access: none in this slice — the web app holds no data access and every read and write goes through the F071 API, whose SQL lives in `crates/persistence/src/migration/` behind the four repository classes (decision section 2.1)
- Rust service/API: consumed only; the commit route, provisioner, resume, and rollback are delivered by T282 under S141
- Data/migration: none; the four tables arrive with S141
- React/UI: `apps/web/src/features/migration/{MigrationListPage.tsx, MigrationUploadPanel.tsx, MigrationReviewPage.tsx, TabPlanList.tsx, ColumnReviewTable.tsx, TypeOverrideSelect.tsx, ConfidenceChip.tsx, SampleValueList.tsx, IssuePanel.tsx, IssueGroup.tsx, CommitProgressPanel.tsx, CommitConfirmDialog.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: MSW handlers for the five routes with `analyzing`, `ready`, `committing`, `completed`, and `failed` fixtures; `testing/fixtures/migration.rs` for the API, database, e2e, accessibility, and performance lanes; workbook and archive generators in `testing/harness/workbooks/`

## TDD harness

- Test path: `testing/features/F071/{frontend,e2e,accessibility,performance,requirements}/`
- Feature flag: `F071_FEATURE`
- Targeted command: `cargo xtask test-feature F071`
- Full command: `cargo xtask test-all`
- First failing tests: `review_table_lists_inferred_type_and_confidence`, `commit_disabled_until_blocking_issue_waived`, `ambiguous_column_requires_override_or_acceptance`, `override_error_returns_message_to_offending_row`, `progress_panel_announces_each_committed_tab`, `failed_tab_states_its_sheet_was_removed`, `delete_migration_states_sheets_will_be_removed`, `viewer_sees_denied_surface_on_migration_route`

## Exit criteria

- [ ] Requirement tests SR-S142-01 through SR-S142-08 written first and failing
- [ ] Tasks T283 and T284 complete and wired through the app router
- [ ] React, E2E, accessibility, permission, and performance tests pass in targeted and full modes
- [ ] Production call path named: `apps/web/src/features/migration/routes.ts` registered in `apps/web/src/routes.tsx` (`/w/:workspaceId/migrations`, `/w/:workspaceId/migrations/:migrationId`), calling the generated `MigrationApi` against the routes mounted by S141
- [ ] Handoff evidence recorded in the F071 ticket
