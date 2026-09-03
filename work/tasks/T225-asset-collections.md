---
id: T225
type: task
status: planned
parent_epic: E008
parent_feature: F057
parent_story: S113
depends_on: [S113]
owned_paths: [services/api/migrations/*_assets_*.sql, crates/domain/src/assets/**, services/api/src/assets/**, testing/features/F057/database/**, testing/features/F057/api/**]
feature_flag: F057_FEATURE
branch: t225-asset-collections
started_at: null
finished_at: null
---

# T225 — Asset collections

## Identity

- Parent story: `S113` Asset library
- Owner: platform
- Branch: `t225-asset-collections`
- Decision references: `docs/architecture-decisions.md` sections 2–4; `docs/capability-contracts.md` row F057

## Objective

Create the five asset tables and implement asset registration, listing, archive, and collection routes with entitlement, ACL, idempotency, concurrency, audit, and outbox enforcement.

## Specification

- Owned paths: `services/api/migrations/<ts>_assets_create_tables.sql`, `services/api/migrations/<ts>_assets_create_tables.down.sql`, `crates/domain/src/assets/{mod.rs, asset.rs, collection.rs, errors.rs, schema.rs, service.rs, service_collections.rs}`, `services/api/src/assets/{mod.rs, routes.rs, handlers_asset.rs, handlers_collection.rs, dto.rs, entitlement.rs}`
- Contract/input: `RegisterAssetRequest { file_id, title, description?, tags?, metadata?, collection_ids? }`, `UpdateAssetRequest { title?, description?, tags?, metadata? }`, list query `{ cursor?, limit?, q?, collection_id?, approval_state?, rights_state?, mime_prefix?, usable?, sort? }`, `CreateCollectionRequest { name, description?, visibility, parent_id? }`, `ReplaceCollectionAssetsRequest { asset_ids }`; headers `Idempotency-Key`, `If-Match`.
- Output/behavior: DDL per ticket section 4 including the generated `search` tsvector, GIN index, rendition uniqueness, collection name uniqueness, and depth check; routes `GET/POST /api/v1/assets`, `GET/PATCH/DELETE /api/v1/assets/{id}`, `GET/POST /api/v1/asset-collections`, `PUT /api/v1/asset-collections/{id}/assets` return `AssetResponse` and `CollectionResponse`; check order is flag, entitlement, tenant, role; register verifies F017 scan state `clean` and enqueues `assets.render`; archive publishes `asset.archived.v1` and keeps membership rows.
- Dependencies: F017 `files::get_for_actor` and scan state; F048 `require_entitlement`; F003 `authz::require`; F004 outbox writer.
- Feature flag: `F057_FEATURE` gates router mounting; migration runs regardless.
- Large-table note: `assets` is expected to reach 200,000 rows per tenant; every list filter has a supporting index; future columns must be additive and nullable.

## TDD

- Failing test first: `testing/features/F057/database/migration_tests.rs::asset_tables_exist_with_constraints`, `::duplicate_rendition_kind_rejected`, `::collection_depth_six_rejected`, `::rollback_drops_tables`; `testing/features/F057/api/asset_tests.rs::asset_register_returns_version_one`, `::asset_register_unscanned_file_invalid`, `::asset_missing_entitlement_denied`, `::asset_cross_tenant_not_found`, `::asset_archive_hides_from_collections`; `testing/features/F057/api/collection_tests.rs::collection_replace_requires_read_access`
- Targeted command: `cargo xtask test-feature F057`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: schema-per-worker database; `testing/fixtures/assets.rs` clean and quarantined files; in-memory outbox and JetStream recorders

## Exit criteria

- [ ] Tests written before the migration and services and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; router mounted behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S113
- [ ] `finished_at` recorded
