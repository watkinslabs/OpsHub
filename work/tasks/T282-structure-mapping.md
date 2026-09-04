---
id: T282
type: task
status: planned
parent_epic: E003
parent_feature: F071
parent_story: S141
depends_on: [T281]
owned_paths: [crates/domain/src/migration/**, services/api/src/migration/**, services/worker/src/migration/**, testing/features/F071/api/**, testing/features/F071/e2e/**]
feature_flag: F071_FEATURE
branch: t282-structure-mapping
started_at: null
finished_at: null
---

# T282 — Structure mapping

## Identity

- Parent story: `S141` Source parsing
- Owner: platform
- Branch: `t282-structure-mapping`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 7, 9; `docs/capability-contracts.md` row F071

## Objective

Map the staged plan onto real OpsHub structure and apply it: views, cross-tab links, hierarchy, and formula translation at analysis time, then the reviewed commit — overrides, the ambiguity and blocking-issue gates, per-tab transactional provisioning, chunked resumable row streaming, per-tab rollback, deletion, and cleanup.

## Specification

- Owned paths: `crates/domain/src/migration/{plan/{mod.rs, structure.rs, views.rs, links.rs, hierarchy.rs, formulas.rs}, commit/{mod.rs, provisioner.rs, chunker.rs, rollback.rs}}`, `services/api/src/migration/{handlers_commit.rs, handlers_delete.rs}`, `services/worker/src/migration/{commit_job.rs, cleanup_job.rs}`
- Contract/input: `CommitMigrationRequest { column_overrides: [{ column_map_id, target_type, settings? }], sheet_overrides: [{ sheet_map_id, name?, included }], accept_ambiguous, waived_issue_ids }` with `Idempotency-Key` and `If-Match`; the staged plan read back through the S141 repositories.
- Output/behavior: routes `POST /api/v1/migrations/{id}/commit` and `DELETE /api/v1/migrations/{id}`. `views.rs` maps an AutoFilter or table filter to a `grid` view filter AST using `eq`, `contains`, and `between`, a saved sort state to at most 5 `view_sorts` with `view_sorts_truncated` beyond that, and hidden columns and column order to `view_columns`; pivot tables, slicers, and Smartsheet card, calendar, and Gantt definitions raise `unsupported_view_kind` or `unsupported_view_export`. `links.rs` resolves a single-cell or single-column cross-tab reference against a target tab with a unique non-empty key column, stages the column as `link`, and records the target tab and key index; anything else raises `cross_workbook_reference` or `unresolved_reference` and keeps the last computed value as text. `hierarchy.rs` maps outline levels to indent depth 20 with `hierarchy_depth_exceeded` beyond it. `formulas.rs` translates a formula whose functions are all supported by F035 and otherwise writes the computed value with `unsupported_formula_function`. `handlers_commit.rs` replaces overridden `migration_column_maps` rows with `state = overridden` after re-validating each against the F007 create-column contract, refuses an unresolved `ambiguous` column without `accept_ambiguous` and an unwaived `blocking` issue with `400 invalid`, refuses a `committing` or `completed` migration with `409 conflict`, then answers `202` and emits `migration.started.v1`. `provisioner.rs` writes each tab's sheet, columns, options, and views in one `UnitOfWork` through the F006, F007, and F013 domain services; `chunker.rs` streams rows from object storage in 1,000-row chunks through the F008 bulk row service with `Idempotency-Key = <migration_id>:<sheet_ordinal>:<chunk_index>`, advancing `cursor_row_number` and `committed_rows`; `commit_job.rs` claims through `claim_committing_sheet` and resumes at the cursor; after every tab is committed the link pass creates one F009 link per row and records a failure as an issue rather than rolling a sheet back; `rollback.rs` soft-deletes a terminally failed tab's sheet and rows in one transaction and marks it `failed`; completion emits `migration.completed.v1` with `first_sheet_id`. `handlers_delete.rs` soft-deletes the migration and every sheet it created and removes the source object; `cleanup_job.rs` sweeps terminal migrations past `expires_at`.
- Data access: `plan/`, `commit/`, the two handlers, and the two jobs hold no SQL; every read and write goes through the four repositories from T281 with the named queries `claim_committing_sheet`, `advance_sheet_cursor`, `replace_column_maps`, and `count_blocking_issues`, and sheets, columns, options, rows, cells, views, links, and hierarchy are reached only through the F006, F007, F008, F009, and F013 domain services, so this feature never opens a second writer onto their tables (decision section 2.1).
- Dependencies: F006 sheet and row creation, F007 columns and options, F008 bulk row writes and idempotency, F009 links and indent, F013 views and filter AST, F035 for the supported function set, F004 for the worker, quota, retries, and dead letters.
- Feature flag: `F071_FEATURE` gates the commit and delete routes and both jobs.

## TDD

- Failing test first: `testing/features/F071/api/plan_tests.rs::autofilter_becomes_grid_view_filter`, `::sixth_sort_truncated_with_issue`, `::pivot_table_reported_as_unsupported_view_kind`, `::resolvable_cross_tab_reference_staged_as_link`, `::cross_workbook_reference_kept_as_text_with_issue`, `::outline_depth_beyond_twenty_flattened_with_issue`, `::unsupported_formula_function_falls_back_to_value`; `testing/features/F071/api/commit_tests.rs::override_revalidated_against_column_contract`, `::ambiguous_column_requires_override_or_acceptance`, `::unwaived_blocking_issue_refuses_commit`, `::second_commit_returns_conflict`, `::tab_structure_failure_creates_nothing`, `::commit_resumes_from_cursor_without_duplicate_rows`, `::failed_tab_sheet_and_rows_soft_deleted`, `::link_pass_runs_after_all_tabs_and_never_rolls_back_a_sheet`, `::delete_removes_every_sheet_the_migration_created`, `::commenter_cannot_commit`; `testing/features/F071/e2e/migration.spec.ts::commit_creates_sheets_views_and_links`
- Targeted command: `cargo xtask test-feature F071`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/migration.rs`; workbook generators with an AutoFilter, a sort state, grouped rows, a cross-tab reference, a cross-workbook reference, and an unsupported function; worker handlers invoked directly with a kill switch between tabs and between chunks; in-memory outbox recorder; fixed clock

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Commit and delete routes and both jobs registered behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S141
- [ ] `finished_at` recorded
