---
id: T222
type: task
status: planned
parent_epic: E008
parent_feature: F056
parent_story: S111
depends_on: [T221]
owned_paths: [crates/domain/src/pivots/**, crates/persistence/src/pivots/**, services/api/src/pivots/**, testing/features/F056/api/**, testing/features/F056/requirements/**]
feature_flag: F056_FEATURE
branch: t222-pivot-permissions
started_at: null
finished_at: null
---

# T222 — Pivot permissions

## Identity

- Parent story: `S111` Pivot configuration
- Owner: platform
- Branch: `t222-pivot-permissions`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4; `docs/capability-contracts.md` row F056

## Objective

Implement the pivot domain service and the four definition routes with entitlement, role, tenant, idempotency, optimistic concurrency, audit, and outbox enforcement.

## Specification

- Owned paths: `crates/domain/src/pivots/{service.rs, validate.rs}`, `crates/persistence/src/pivots/pivot_queries.rs`, `services/api/src/pivots/{mod.rs, routes.rs, handlers_pivot.rs, dto.rs, entitlement.rs}`
- Contract/input: `CreatePivotRequest { name, source, row_dimensions, column_dimensions?, measures, filters?, refresh_policy? }`, `UpdatePivotRequest` with optional fields, list query `{ cursor?, limit?, workspace_id?, source_id?, sort? }`; headers `Idempotency-Key`, `If-Match`.
- Output/behavior: routes `GET /api/v1/pivots`, `POST /api/v1/pivots`, `PATCH /api/v1/pivots/{id}`, `DELETE /api/v1/pivots/{id}` return `PivotResponse { id, workspace_id, name, source, row_dimensions, column_dimensions, measures, filters, refresh_policy, version, created_at, updated_at, deleted_at }`; order of checks is flag, entitlement (`denied` + `field_errors.entitlement`), tenant (`not_found`), then `report-editor` on the source (`denied`); validation errors carry indexed `field_errors` whose index is the child row's `position`; events `pivot.updated.v1` and audit rows written in the same transaction. The response keeps `row_dimensions`, `column_dimensions`, `measures`, and `filters` as JSON arrays reassembled from the child tables in `position` order, so the OpenAPI schema is unchanged.
- Data access: `service.rs`, `validate.rs`, and every handler depend on the `PivotRepository` trait from T221 and contain no SQL; create, update, and soft delete each run one `UnitOfWork` that writes the `pivots` row, replaces the definition child rows through `replace_row_dimensions`/`replace_column_dimensions`/`replace_measures`/`replace_filters`, and appends the audit and outbox rows. `crates/persistence/src/pivots/pivot_queries.rs` adds the named list query backing `GET /api/v1/pivots` (cursor page filtered by `workspace_id` and `source_id`, sorted by `name` or `updated_at`); there is no generic query method (decision section 2.1).
- Dependencies: T221 schema, `PivotRepository`, and validation types; F048 `require_entitlement`; F003 `authz::require`; F004 outbox writer.
- Feature flag: `F056_FEATURE` gates router mounting.

## TDD

- Failing test first: `testing/features/F056/api/pivot_tests.rs::pivot_create_returns_version_one`, `::pivot_bucket_on_text_column_invalid`, `::pivot_avg_on_text_column_invalid`, `::pivot_missing_entitlement_denied`, `::pivot_viewer_create_denied`, `::pivot_cross_tenant_not_found`, `::pivot_stale_version_conflicts`, `::pivot_idempotent_replay_returns_original`, `::pivot_mutation_writes_audit_and_outbox`, `::pivot_patch_replaces_definition_rows_in_one_transaction`, `::pivot_response_keeps_array_shape`
- Targeted command: `cargo xtask test-feature F056`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/pivots.rs` entitled and unentitled tenants; in-memory outbox recorder; real F048 entitlement middleware

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Router mounted in `services/api/src/router.rs` behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S111
- [ ] `finished_at` recorded
