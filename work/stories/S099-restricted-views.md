---
id: S099
type: story
status: planned
parent_epic: E008
parent_feature: F050
depends_on: [F013, F036, F048]
owned_paths: [crates/domain/src/dynamic-views/**, crates/persistence/src/dynamic-views/**, services/api/src/dynamic-views/**, services/api/migrations/*_dynamic-views_*.sql, testing/features/F050/**]
feature_flag: F050_FEATURE
branch: s099-restricted-views
started_at: null
finished_at: null
---

# S099 — Restricted views

## Identity

- Parent feature: `F050` Dynamic View
- Owner: platform
- Branch: `s099-restricted-views`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 10; `docs/capability-contracts.md` row F050

## Vertical slice

As a sheet owner, I want to create a dynamic view with a row filter and a visible field set, share it with tenant users or an expiring public token, and have the server return only the permitted rows and fields, so that an audience sees exactly its slice of the sheet and nothing else.

Out of this slice: editing through the view, edit records, and the web UI (S100).

## Requirements

- **SR-S099-01:** `POST /api/v1/dynamic-views` creates a view with an empty policy (`edit_mode: none`, no visible fields) and returns `DynamicViewResponse` with version 1; the tenant limit `max_views` is enforced with `409 conflict` (covers FR-F050-01, FR-F050-11).
- **SR-S099-02:** `PUT /api/v1/dynamic-views/{id}/policy` validates the predicate tree (depth ≤ 4, ≤ 20 leaves, real column IDs), `visible_fields`, `editable_fields ⊆ visible_fields`, edit mode and `allow_new_rows` rules, returning `400 invalid` with the offending `field_errors`; `DynamicViewPolicyRepository::replace_policy` then persists the accepted policy as `dynamic_view_visible_fields`, `dynamic_view_editable_fields`, `dynamic_view_filter_nodes`, and `dynamic_view_filter_values` rows in one `UnitOfWork`, with the request and response array/object shapes unchanged (FR-F050-02, FR-F050-03).
- **SR-S099-03:** `GET /api/v1/dynamic-views/{id}/rows` loads the compiled policy through `DynamicViewPolicyRepository::load_compiled_filter`, reads rows through the F006 `RowRepository::list_rows_for_policy` named query, projects them for the caller's audience with `project_rows`, drops columns without a `dynamic_view_visible_fields` row from `fields`, `filter`, and `sort`, and pages by cursor with `limit` ≤ 500; the handler contains no SQL (FR-F050-04).
- **SR-S099-04:** `PATCH /api/v1/dynamic-views/{id}` enables a public token by inserting one `dynamic_view_tokens` row with `expires_at` ≤ 30 days, or revokes the live row; `GET /public/dynamic-views/{token}` resolves the SHA-256 hash through `DynamicViewTokenRepository::find_live_by_hash`, refuses expired or revoked tokens with `403 denied`, and returns no tenant, workspace, or sheet identifiers (FR-F050-05, FR-F050-08).
- **SR-S099-05:** `GET /api/v1/dynamic-views` and `DELETE /api/v1/dynamic-views/{id}` list and soft-delete views for the owner; `soft_delete_with_token_revocation` sets `revoked_at` on the live token row and invalidates shares in the same transaction (FR-F050-09).
- **SR-S099-06:** Unshared tenant users and foreign tenants receive `404 not_found` on every route; non-entitled tenants receive `403 denied` from `RequireModule(ModuleSlug::DynamicViews)` (FR-F050-11, FR-F050-12).
- **SR-S099-07:** Every mutation requires `Idempotency-Key` and `If-Match`, writes an audit row, and publishes `dynamic-view.updated.v1` (FR-F050-10).
- **SR-S099-08:** Filtered rows over the 100,000-row fixture respond under 500 ms p95 and token resolution adds under 20 ms (NFR-F050-01).

## Surfaces

- Infrastructure/container: none beyond F004 baseline
- Data access: `crates/persistence/src/dynamic-views/{mod.rs, view_repository.rs, token_repository.rs, policy_repository.rs, edit_repository.rs}` hold every SQL statement for this slice — `DynamicViewRepository` owns `dynamic_views`, `DynamicViewTokenRepository` owns `dynamic_view_tokens`, `DynamicViewPolicyRepository` owns `dynamic_view_policies` and its four child tables, `DynamicViewEditRepository` owns `dynamic_view_edits`; the domain services and the `services/api/src/dynamic-views` handlers depend on the repository traits and contain no `sqlx::query*` call, and the restricted row read composes the policy into the F006 `RowRepository::list_rows_for_policy` named query rather than assembling SQL in the handler (decision section 2.1)
- Rust service/API: `crates/domain/src/dynamic-views/{mod.rs, view.rs, policy.rs, predicate.rs, projection.rs, token.rs, errors.rs, service.rs}`; `services/api/src/dynamic-views/{mod.rs, routes.rs, handlers_view.rs, handlers_policy.rs, handlers_rows.rs, handlers_public.rs, dto.rs}`
- Data/migration: `services/api/migrations/<ts>_dynamic-views_create_tables.sql` creating `dynamic_views`, `dynamic_view_policies`, `dynamic_view_visible_fields`, `dynamic_view_editable_fields`, `dynamic_view_filter_nodes`, `dynamic_view_filter_values`, `dynamic_view_tokens`, and `dynamic_view_edits` with the foreign keys, enum checks, and indexes from ticket section 4
- React/UI: none in this story (S100 and T199 cover UI)
- Mocks/fixtures: `testing/fixtures/dynamic_views.rs` owner, shared user, unshared sheet viewer, tenant B, 200-row sheet, live and revoked tokens; in-memory outbox recorder; F048 evaluator with `dynamic-views` active

## TDD harness

- Test path: `testing/features/F050/api/`, `testing/features/F050/database/`, `testing/features/F050/performance/`
- Feature flag: `F050_FEATURE`
- Targeted command: `cargo xtask test-feature F050`
- Full command: `cargo xtask test-all`
- First failing tests: `view_create_starts_with_empty_policy`, `policy_rejects_editable_not_visible`, `policy_replace_rewrites_field_and_filter_rows`, `editable_field_row_without_visible_row_rejected`, `rows_drop_hidden_fields_from_request`, `token_expiry_over_30_days_invalid`, `second_live_token_row_rejected`, `public_view_response_has_no_tenant_ids`, `unshared_sheet_viewer_not_found`

## Exit criteria

- [ ] Requirement tests SR-S099-01 through SR-S099-08 written first and failing
- [ ] Tasks T197 and T198 complete and wired through `services/api` router
- [ ] Unit, API, database, permission, and performance tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/dynamic-views/routes.rs` mounted in `services/api/src/router.rs` under `RequireModule(ModuleSlug::DynamicViews)`; public router mounted at `/public/dynamic-views`
- [ ] Handoff evidence recorded in the F050 ticket
