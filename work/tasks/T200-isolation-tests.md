---
id: T200
type: task
status: planned
parent_epic: E008
parent_feature: F050
parent_story: S100
depends_on: [T199]
owned_paths: [testing/features/F050/**]
feature_flag: F050_FEATURE
branch: t200-isolation-tests
started_at: null
finished_at: null
---

# T200 — Isolation tests

## Identity

- Parent story: `S100` Controlled editing
- Owner: platform
- Branch: `t200-isolation-tests`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 4, 9, 10; `docs/capability-contracts.md` row F050

## Objective

Complete the F050 harness with the isolation, E2E, accessibility, and performance suites proving that hidden data never leaves the service and that every audience boundary holds.

## Specification

- Owned paths: `testing/features/F050/api/isolation_tests.rs`, `testing/features/F050/database/constraint_tests.rs`, `testing/features/F050/e2e/dynamic_view.spec.ts`, `testing/features/F050/accessibility/dynamic_view.a11y.spec.ts`, `testing/features/F050/performance/{rows_bench.rs, edit_bench.rs}`, `testing/features/F050/requirements/cases.md` (final traceability), `testing/features/F050/README.md`
- Contract/input: seeded tenant A (owner, vendor 1, vendor 2, unshared sheet viewer), tenant B, a 100,000-row sheet generator for the performance lane, a live token and a revoked token; raw HTTP capture for body inspection.
- Output/behavior: isolation suite asserts hidden column IDs and values are absent from raw response bodies, outbox payloads, audit diffs, and captured logs; vendor 1 never sees vendor 2 rows through rows, edits, or `preview_as`; tenant B receives `404` on every route and the token of tenant A resolves only under tenant A's module guard; E2E covers owner policy → vendor edit → owner sees edit → revoke blocks link; accessibility covers axe on grid, editor, dialog, and editable-cell announcements; performance covers 100k-row filtered list p95 < 500 ms, edit p95 < 800 ms, token resolve < 20 ms; the requirements table maps every FR-F050-01..14 and NFR-F050-01..04 to case IDs and lanes.
- Data access: no test in this suite opens a pool or issues SQL of its own; every fixture write and every state assertion goes through the `crates/persistence/src/dynamic-views/` repositories (`DynamicViewRepository`, `DynamicViewPolicyRepository`, `DynamicViewTokenRepository`, `DynamicViewEditRepository`) and the F006 `RowRepository`, so the tests exercise the same path production uses. `constraint_tests.rs` is the one exception and asserts the normalized shape directly against the database: an editable-field row without a matching visible-field row is rejected by the composite foreign key, a duplicate `(view_id, column_id)` in either field table is rejected, a filter node with `node_kind` `and` carrying `column_id` or `op` is rejected, a `dynamic_view_filter_values` row without its node is rejected, a second `dynamic_view_tokens` row for a view with `revoked_at is null` is rejected, an edit row with both or neither actor column is rejected, deleting a view cascades to policy, field, and filter rows while `dynamic_view_edits` blocks it with `on delete restrict`, and `dynamic_view_edits.before`/`after` are the only `jsonb` columns in the module (decision sections 2 and 2.1).
- Dependencies: T199 UI and edit route; F004 compose baseline for Playwright.
- Feature flag: `F050_FEATURE` on for the suite; one E2E case runs with the flag off and asserts `/dv/{token}` is not-found.

## TDD

- Failing test first: `testing/features/F050/api/isolation_tests.rs::hidden_values_absent_from_bodies_events_logs`, `::vendor_cannot_see_other_vendor_rows`, `::cross_tenant_every_route_not_found`, `::preview_as_ignored_for_non_owner`; `testing/features/F050/database/constraint_tests.rs::editable_field_row_requires_visible_field_row`, `::duplicate_field_row_rejected`, `::filter_node_group_with_operand_rejected`, `::filter_value_orphan_rejected`, `::second_live_token_row_rejected`, `::edit_requires_exactly_one_actor`, `::view_delete_cascades_policy_rows_and_restricts_edits`, `::only_edit_diff_columns_are_jsonb`; `testing/features/F050/e2e/dynamic_view.spec.ts::owner_policy_to_vendor_edit_round_trip`, `::revoked_link_shows_inactive_page`; `testing/features/F050/accessibility/dynamic_view.a11y.spec.ts::grid_editor_dialog_no_serious_axe_violations`; `testing/features/F050/performance/rows_bench.rs::filtered_rows_100k_p95`
- Targeted command: `cargo xtask test-feature F050`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: Playwright against the real API with seeded roles; k6 script for rows and edits; log capture sink from `testing/harness/logs.rs`

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Isolation, database-constraint, E2E, accessibility, and performance lanes pass; evidence stored under `testing/evidence/F050/`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S100
- [ ] `finished_at` recorded
