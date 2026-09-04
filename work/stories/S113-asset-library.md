---
id: S113
type: story
status: planned
parent_epic: E008
parent_feature: F057
depends_on: [F017, F020, F048]
owned_paths: [crates/domain/src/assets/**, crates/persistence/src/assets/**, services/api/src/assets/**, services/api/migrations/*_assets_*.sql, testing/features/F057/**]
feature_flag: F057_FEATURE
branch: s113-asset-library
started_at: null
finished_at: null
---

# S113 — Asset library

## Identity

- Parent feature: `F057` DAM assets
- Owner: platform
- Branch: `s113-asset-library`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 5; `docs/capability-contracts.md` row F057

## Vertical slice

As an asset editor with the DAM entitlement, I want to register scanned files as assets with typed metadata and tags, organize them into collections, and search the library through the API, so that a governed catalog exists before renditions, rights, and approvals are layered on.

## Requirements

- **SR-S113-01:** `POST /api/v1/assets` with `{ file_id, title, description?, tags?, metadata?, collection_ids? }` verifies the F017 scan state is `clean`, validates metadata against the `asset_metadata_fields` rows, and through `AssetRepository::insert_asset` and `AssetCollectionRepository::replace_collection_items` writes the `assets` row, one `asset_tags` row per resolved `asset_tag_definitions` entry, one `asset_metadata_values` row per supplied field, and the `asset_collection_items` rows in one `UnitOfWork`, returning `AssetResponse` with `tags` and `metadata` in their original JSON array and object shapes and version 1 (covers FR-F057-01, FR-F057-02, FR-F057-12).
- **SR-S113-02:** Every asset and collection route checks `F057_FEATURE` and `require_entitlement(tenant, "dam")` before role checks, returning `403 denied` with `field_errors.entitlement = "dam"`; a foreign tenant receives `404 not_found` (FR-F057-11).
- **SR-S113-03:** `AssetRepository::list_assets_page` pages `GET /api/v1/assets` by cursor with filters `q`, `tag`, `territory`, `channel`, `collection_id`, `approval_state`, `rights_state`, `mime_prefix`, `usable`, and sorts by `title`, `created_at`, `updated_at`, using the GIN index on the maintained `search` vector for `q` and joins to `asset_tags`, `asset_rights_territories`, and `asset_rights_channels` for the set filters (FR-F057-07).
- **SR-S113-04:** `GET /api/v1/assets/{id}` and `PATCH /api/v1/assets/{id}` return and update title, description, tags, and metadata with `If-Match`; a tag or metadata edit replaces the `asset_tags` and `asset_metadata_values` rows and refreshes `assets.search` in the same transaction; a stale version returns `409 conflict`; every mutation writes an audit diff and publishes `asset.created.v1` or `asset.updated.v1` (FR-F057-10).
- **SR-S113-05:** `POST /api/v1/asset-collections` enforces depth ≤ 5 and unique name per parent; `PUT /api/v1/asset-collections/{id}/assets` replaces ordered membership (≤ 5,000) after verifying read access to each asset (FR-F057-08).
- **SR-S113-06:** `DELETE /api/v1/assets/{id}` sets `archived_at`, publishes `asset.archived.v1`, and hides the asset from lists and collection listings while keeping `asset_collection_items` rows (FR-F057-09).
- **SR-S113-07:** The migration creates the thirteen tables with the foreign keys, closed-enum checks, and indexes in ticket section 4, including `asset_tag_definitions`, `asset_tags`, `asset_territory_codes`, `asset_rights_territories`, `asset_rights_channels`, `asset_metadata_fields`, `asset_metadata_field_options`, and `asset_metadata_values`; no array column and no queried `jsonb` column remains (NFR-F057-02).

## Surfaces

- Infrastructure/container: none beyond F004 baseline and MinIO from compose
- Data access: `crates/persistence/src/assets/{mod.rs, asset_repository.rs, tag_repository.rs, collection_repository.rs, metadata_field_repository.rs}` hold every SQL statement for this slice — `AssetRepository` owns `assets`, `asset_tags`, `asset_metadata_values`; `AssetTagRepository` owns `asset_tag_definitions`; `AssetCollectionRepository` owns `asset_collections`, `asset_collection_items`; `AssetMetadataFieldRepository` owns `asset_metadata_fields`, `asset_metadata_field_options`. The domain services and the `services/api/src/assets` handlers depend on the repository traits and contain no `sqlx::query*` call, and register, update, and membership replacement run in one `UnitOfWork` (decision section 2.1)
- Rust service/API: `crates/domain/src/assets/{mod.rs, asset.rs, tag.rs, collection.rs, metadata.rs, errors.rs, service.rs, service_collections.rs}`; `services/api/src/assets/{mod.rs, routes.rs, handlers_asset.rs, handlers_collection.rs, dto.rs, entitlement.rs}`
- Data/migration: `services/api/migrations/<ts>_assets_create_tables.sql` and `.down.sql`
- React/UI: none in this story (S114 and T227 cover UI)
- Mocks/fixtures: `testing/fixtures/assets.rs` entitled and unentitled tenants, editor, viewer, foreign tenant, 20 clean files, one quarantined file, 5-field metadata schema, 3-level collection tree

## TDD harness

- Test path: `testing/features/F057/api/`, `testing/features/F057/database/`
- Feature flag: `F057_FEATURE`
- Targeted command: `cargo xtask test-feature F057`
- Full command: `cargo xtask test-all`
- First failing tests: `asset_register_returns_version_one`, `asset_register_unscanned_file_invalid`, `asset_metadata_type_mismatch_invalid`, `asset_missing_entitlement_denied`, `asset_search_uses_gin_index`, `collection_depth_six_rejected`, `asset_archive_hides_from_collections`, `asset_tag_row_written_per_tag`, `asset_metadata_value_row_rejects_two_typed_columns`, `metadata_field_removal_blocked_by_foreign_key`

## Exit criteria

- [ ] Requirement tests SR-S113-01 through SR-S113-07 written first and failing
- [ ] Tasks T225 and T226 complete and wired through `services/api` router
- [ ] Unit, API, database, permission tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/assets/routes.rs` mounted in `services/api/src/router.rs` behind `F057_FEATURE`
- [ ] Handoff evidence recorded in the F057 ticket
