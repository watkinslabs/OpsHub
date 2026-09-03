---
id: S099
type: story
status: planned
parent_epic: E008
parent_feature: F050
depends_on: [F013, F036, F048]
owned_paths: [crates/domain/src/dynamic-views/**, services/api/src/dynamic-views/**, services/api/migrations/*_dynamic-views_*.sql, testing/features/F050/**]
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
- Decision references: `docs/architecture-decisions.md` sections 2–4, 10; `docs/capability-contracts.md` row F050

## Vertical slice

As a sheet owner, I want to create a dynamic view with a row filter and a visible field set, share it with tenant users or an expiring public token, and have the server return only the permitted rows and fields, so that an audience sees exactly its slice of the sheet and nothing else.

Out of this slice: editing through the view, edit records, and the web UI (S100).

## Requirements

- **SR-S099-01:** `POST /api/v1/dynamic-views` creates a view with an empty policy (`edit_mode: none`, no visible fields) and returns `DynamicViewResponse` with version 1; the tenant limit `max_views` is enforced with `409 conflict` (covers FR-F050-01, FR-F050-11).
- **SR-S099-02:** `PUT /api/v1/dynamic-views/{id}/policy` validates the predicate tree (depth ≤ 4, ≤ 20 leaves, real column IDs), `visible_fields`, `editable_fields ⊆ visible_fields`, edit mode and `allow_new_rows` rules, returning `400 invalid` with the offending `field_errors` (FR-F050-02, FR-F050-03).
- **SR-S099-03:** `GET /api/v1/dynamic-views/{id}/rows` projects rows through `project_rows` for the caller's audience, drops hidden fields from `fields`, `filter`, and `sort`, and pages by cursor with `limit` ≤ 500 (FR-F050-04).
- **SR-S099-04:** `PATCH /api/v1/dynamic-views/{id}` enables a public token with `expires_at` ≤ 30 days, or revokes it; `GET /public/dynamic-views/{token}` resolves the SHA-256 hash, refuses expired or revoked tokens with `403 denied`, and returns no tenant, workspace, or sheet identifiers (FR-F050-05, FR-F050-08).
- **SR-S099-05:** `GET /api/v1/dynamic-views` and `DELETE /api/v1/dynamic-views/{id}` list and soft-delete views for the owner; deletion invalidates the token and shares immediately (FR-F050-09).
- **SR-S099-06:** Unshared tenant users and foreign tenants receive `404 not_found` on every route; non-entitled tenants receive `403 denied` from `RequireModule(ModuleSlug::DynamicViews)` (FR-F050-11, FR-F050-12).
- **SR-S099-07:** Every mutation requires `Idempotency-Key` and `If-Match`, writes an audit row, and publishes `dynamic-view.updated.v1` (FR-F050-10).
- **SR-S099-08:** Filtered rows over the 100,000-row fixture respond under 500 ms p95 and token resolution adds under 20 ms (NFR-F050-01).

## Surfaces

- Infrastructure/container: none beyond F004 baseline
- Rust service/API: `crates/domain/src/dynamic-views/{mod.rs, view.rs, policy.rs, predicate.rs, projection.rs, token.rs, errors.rs, service.rs}`; `services/api/src/dynamic-views/{mod.rs, routes.rs, handlers_view.rs, handlers_policy.rs, handlers_rows.rs, handlers_public.rs, dto.rs}`
- Data/migration: `services/api/migrations/<ts>_dynamic-views_create_tables.sql` creating `dynamic_views`, `dynamic_view_policies`, `dynamic_view_edits` with the constraints from ticket section 4
- React/UI: none in this story (S100 and T199 cover UI)
- Mocks/fixtures: `testing/fixtures/dynamic_views.rs` owner, shared user, unshared sheet viewer, tenant B, 200-row sheet, live and revoked tokens; in-memory outbox recorder; F048 evaluator with `dynamic-views` active

## TDD harness

- Test path: `testing/features/F050/api/`, `testing/features/F050/database/`, `testing/features/F050/performance/`
- Feature flag: `F050_FEATURE`
- Targeted command: `cargo xtask test-feature F050`
- Full command: `cargo xtask test-all`
- First failing tests: `view_create_starts_with_empty_policy`, `policy_rejects_editable_not_visible`, `rows_drop_hidden_fields_from_request`, `token_expiry_over_30_days_invalid`, `public_view_response_has_no_tenant_ids`, `unshared_sheet_viewer_not_found`

## Exit criteria

- [ ] Requirement tests SR-S099-01 through SR-S099-08 written first and failing
- [ ] Tasks T197 and T198 complete and wired through `services/api` router
- [ ] Unit, API, database, permission, and performance tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/dynamic-views/routes.rs` mounted in `services/api/src/router.rs` under `RequireModule(ModuleSlug::DynamicViews)`; public router mounted at `/public/dynamic-views`
- [ ] Handoff evidence recorded in the F050 ticket
