---
id: T197
type: task
status: planned
parent_epic: E008
parent_feature: F050
parent_story: S099
depends_on: [S099]
owned_paths: [services/api/migrations/*_dynamic-views_*.sql, crates/domain/src/dynamic-views/**, crates/persistence/src/dynamic-views/**, services/api/src/dynamic-views/**, testing/features/F050/database/**, testing/features/F050/api/**]
feature_flag: F050_FEATURE
branch: t197-filter-policy
started_at: null
finished_at: null
---

# T197 — Filter policy

## Identity

- Parent story: `S099` Restricted views
- Owner: platform
- Branch: `t197-filter-policy`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4; `docs/capability-contracts.md` row F050

## Objective

Create the dynamic view schema, the policy and predicate model, the row projection function, and the view and policy routes so a restricted row set can be served to shared tenant users.

## Specification

- Owned paths: `services/api/migrations/<ts>_dynamic-views_create_tables.sql`, `services/api/migrations/<ts>_dynamic-views_create_tables.down.sql`, `crates/domain/src/dynamic-views/{mod.rs, view.rs, policy.rs, predicate.rs, projection.rs, errors.rs, service.rs, schema.rs}`, `crates/persistence/src/dynamic-views/{mod.rs, view_repository.rs, policy_repository.rs}`, `services/api/src/dynamic-views/{mod.rs, routes.rs, handlers_view.rs, handlers_policy.rs, handlers_rows.rs, dto.rs}`
- Data access: `DynamicViewRepository` owns `dynamic_views`; `DynamicViewPolicyRepository` owns `dynamic_view_policies`, `dynamic_view_visible_fields`, `dynamic_view_editable_fields`, `dynamic_view_filter_nodes`, and `dynamic_view_filter_values` and exposes `load_policy`, `replace_policy`, `list_visible_columns`, `list_editable_columns`, `is_column_editable`, and `load_compiled_filter`; `view.rs`, `policy.rs`, `projection.rs`, `service.rs`, and every handler in this task hold no SQL and no `sqlx::query*` call, `replace_policy` rewrites all five tables in one `UnitOfWork`, and the rows handler passes the compiled filter and visible column set to the F006 `RowRepository::list_rows_for_policy` named query instead of building a statement (decision section 2.1).
- Contract/input: DDL per F050 ticket section 4 (`dynamic_views`, `dynamic_view_policies`, `dynamic_view_visible_fields`, `dynamic_view_editable_fields`, `dynamic_view_filter_nodes`, `dynamic_view_filter_values` in this task, plus the `dynamic_view_tokens` and `dynamic_view_edits` tables the migration also creates; composite foreign key replacing the subset check, node-kind and op checks, edit-mode checks, single-actor check, indexes); `CreateDynamicViewRequest { name, sheet_id, base_view_id?, description? }`, `PolicyRequest { row_filter, visible_fields, editable_fields, edit_mode, assignment_column_id?, allow_new_rows }`, rows query `{ cursor?, limit?, fields?, filter?, sort? }`; headers `Idempotency-Key`, `If-Match`; audience resolved from F036 shares on `(dynamic-view, id)`.
- Output/behavior: routes `GET /api/v1/dynamic-views`, `POST /api/v1/dynamic-views`, `PATCH /api/v1/dynamic-views/{id}` (name/description only in this task), `DELETE /api/v1/dynamic-views/{id}`, `PUT /api/v1/dynamic-views/{id}/policy`, `GET /api/v1/dynamic-views/{id}/rows`; `load_compiled_filter` turns equality and `in` nodes into bound parameters of the F006 `RowRepository::list_rows_for_policy` query so the narrowing happens on the indexed `cells` lookup, `project_rows(policy, rows, audience)` then evaluates the remaining predicate in memory, strips columns without a `dynamic_view_visible_fields` row, and ignores them in `fields`, `filter`, `sort`; `max_views` enforced from F048 limits; events `dynamic-view.updated.v1` and audit rows written in the same transaction; errors map per ticket section 4.
- Dependencies: F006 `sheets`, `rows`, `cells` tables; F007 column IDs and person column type; F013 `views` for `base_view_id`; F036 share lookup; F048 `RequireModule(ModuleSlug::DynamicViews)` and `Evaluator::limits`.
- Feature flag: `F050_FEATURE` gates router mounting; migration runs regardless.

## TDD

- Failing test first: `testing/features/F050/database/migration_tests.rs::dynamic_view_tables_exist_with_constraints`, `::editable_not_subset_of_visible_rejected`, `::assigned_rows_requires_assignment_column`, `::rollback_drops_tables`; `testing/features/F050/api/view_tests.rs::view_create_starts_with_empty_policy`, `::view_limit_reached_conflicts`, `::unshared_sheet_viewer_not_found`; `testing/features/F050/api/policy_tests.rs::policy_rejects_editable_not_visible`, `::policy_rejects_depth_over_4`; `testing/features/F050/api/rows_tests.rs::rows_drop_hidden_fields_from_request`, `::rows_assigned_to_current_user_filter`
- Targeted command: `cargo xtask test-feature F050`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/dynamic_views.rs` 200-row sheet with `Vendor` and `Vendor status` columns; schema-per-worker database; in-memory outbox recorder

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; router mounted in `services/api/src/router.rs` behind the flag and module guard; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S099
- [ ] `finished_at` recorded
