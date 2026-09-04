---
id: T284
type: task
status: planned
parent_epic: E003
parent_feature: F071
parent_story: S142
depends_on: [T283]
owned_paths: [testing/features/F071/**]
feature_flag: F071_FEATURE
branch: t284-migration-tests
started_at: null
finished_at: null
---

# T284 — Migration tests

## Identity

- Parent story: `S142` Mapped provisioning
- Owner: platform
- Branch: `t284-migration-tests`
- Decision references: `docs/architecture-decisions.md` sections 4, 6, 9; `docs/capability-contracts.md` row F071

## Objective

Complete the F071 harness: the traceability lane covering every FR and NFR id, the end-to-end journey from upload to created sheets, the permission-negative and tenant-isolation set, the accessibility lane, and the performance lane that turns each NFR number into an assertion.

## Specification

- Owned paths: `testing/features/F071/{feature.toml, README.md, requirements/cases.md, api/cases.md, database/cases.md, frontend/cases.md, e2e/{cases.md, migration.spec.ts}, accessibility/{cases.md, migration.a11y.spec.ts}, performance/{cases.md, analysis_bench.rs, commit_bench.rs, preview_bench.rs}}`
- Contract/input: the seeded tenant from `testing/fixtures/migration.rs` — tenant A and B, a sheet-editor, a viewer, a commenter, destination folder `Delivery`, and the generated `q3-delivery.xlsx`, `smartsheet-export.zip`, `airtable-base.zip`, a 50-tab workbook, a 120,000-row tab, and an over-expanding zip.
- Output/behavior: the requirements lane maps every FR-F071-01 through FR-F071-16 and NFR-F071-01 through NFR-F071-05 id to the lane that proves it. The e2e spec drives the whole journey — upload `q3-delivery.xlsx`, wait out analysis, change `Owner` from `text` to `person`, waive the conditional-format issue, commit, watch each tab land, open the first created sheet, confirm its columns, its grid view, its indented rows, and its cross-tab link chip — plus a second journey that deletes an abandoned migration and confirms the folder is unchanged. The permission set proves a viewer is denied on create, a commenter on commit, and that a foreign-tenant `file_id`, `target_folder_id`, and migration id all return `not_found`. The accessibility lane runs axe over the list, review, and progress surfaces in both themes and asserts the labelled type selects, the non-colour confidence signal, the grouped issue headings, the live-region announcements, and keyboard reach for override, waive, and commit. The performance lane asserts 20-tab analysis under 90 s, preview under 800 ms p95 at 50 tabs and 2,000 column maps, a 100,000-row commit under 15 minutes, and parser peak resident memory under 512 MB, and records a negative control proving no lane opens a socket to an external product.
- Data access: none; the lanes exercise the F071 API, the four repositories, and the worker handlers, and no test opens its own connection or writes SQL outside `crates/persistence`.
- Dependencies: F043 for lane isolation, F004 for the worker harness and outbox recorder, F062 for the theme and density matrix, F067 for the seed generators the performance lane reuses.
- Feature flag: `F071_FEATURE` selects the suite; `cargo xtask test-all` enables every suite.

## TDD

- Failing test first: `testing/features/F071/e2e/migration.spec.ts::upload_review_override_commit_opens_created_sheet`, `::delete_abandoned_migration_leaves_folder_unchanged`, `::committed_sheet_shows_hierarchy_and_link_chip`; `testing/features/F071/accessibility/migration.a11y.spec.ts::migration_routes_have_no_serious_violations`, `::confidence_is_text_and_icon_not_colour_alone`, `::commit_progress_announced_through_live_region`, `::override_and_waive_are_keyboard_reachable`; `testing/features/F071/performance/analysis_bench.rs::twenty_tab_analysis_under_ninety_seconds`, `::parser_peak_memory_under_512mb`; `testing/features/F071/performance/preview_bench.rs::preview_p95_under_800ms_at_fifty_tabs`; `testing/features/F071/performance/commit_bench.rs::hundred_thousand_row_commit_under_fifteen_minutes`
- Targeted command: `cargo xtask test-feature F071`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/migration.rs`; workbook and archive generators in `testing/harness/workbooks/`; F017 stub with pre-scanned fixtures; in-memory outbox recorder; one schema and one object-storage prefix per worker; fixed clock `2026-09-03T00:00:00Z` and UTC

## Exit criteria

- [ ] Every FR-F071 and NFR-F071 id appears in `testing/features/F071/requirements/cases.md` with the lane that proves it
- [ ] All seven lanes run green in targeted and full modes and write evidence to `testing/evidence/F071/`
- [ ] Positive control recorded: a known defect turns each new gate red and its removal turns it green
- [ ] Owned-path check passes
- [ ] File limit gate passes
- [ ] Handoff evidence recorded in S142
- [ ] `finished_at` recorded
