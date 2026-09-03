---
id: S113
type: story
status: planned
parent_epic: E008
parent_feature: F057
depends_on: [F017, F020, F048]
owned_paths: [crates/domain/src/assets/**, services/api/src/assets/**, services/api/migrations/*_assets_*.sql, testing/features/F057/**]
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
- Decision references: `docs/architecture-decisions.md` sections 2–5; `docs/capability-contracts.md` row F057

## Vertical slice

As an asset editor with the DAM entitlement, I want to register scanned files as assets with typed metadata and tags, organize them into collections, and search the library through the API, so that a governed catalog exists before renditions, rights, and approvals are layered on.

## Requirements

- **SR-S113-01:** `POST /api/v1/assets` with `{ file_id, title, description?, tags?, metadata?, collection_ids? }` verifies the F017 scan state is `clean`, validates metadata against the tenant schema, inserts `assets` and `asset_collection_items`, and returns `AssetResponse` with version 1 (covers FR-F057-01, FR-F057-02, FR-F057-12).
- **SR-S113-02:** Every asset and collection route checks `F057_FEATURE` and `require_entitlement(tenant, "dam")` before role checks, returning `403 denied` with `field_errors.entitlement = "dam"`; a foreign tenant receives `404 not_found` (FR-F057-11).
- **SR-S113-03:** `GET /api/v1/assets` pages by cursor with filters `q`, `collection_id`, `approval_state`, `rights_state`, `mime_prefix`, `usable`, and sorts by `title`, `created_at`, `updated_at`, using the GIN `search` index for `q` (FR-F057-07).
- **SR-S113-04:** `GET /api/v1/assets/{id}` and `PATCH /api/v1/assets/{id}` return and update title, description, tags, and metadata with `If-Match`; a stale version returns `409 conflict`; every mutation writes an audit diff and publishes `asset.created.v1` or `asset.updated.v1` (FR-F057-10).
- **SR-S113-05:** `POST /api/v1/asset-collections` enforces depth ≤ 5 and unique name per parent; `PUT /api/v1/asset-collections/{id}/assets` replaces ordered membership (≤ 5,000) after verifying read access to each asset (FR-F057-08).
- **SR-S113-06:** `DELETE /api/v1/assets/{id}` sets `archived_at`, publishes `asset.archived.v1`, and hides the asset from lists and collection listings while keeping `asset_collection_items` rows (FR-F057-09).
- **SR-S113-07:** The migration creates the five tables with the constraints and indexes in ticket section 4 (NFR-F057-02).

## Surfaces

- Infrastructure/container: none beyond F004 baseline and MinIO from compose
- Rust service/API: `crates/domain/src/assets/{mod.rs, asset.rs, collection.rs, metadata.rs, errors.rs, service.rs, service_collections.rs}`; `services/api/src/assets/{mod.rs, routes.rs, handlers_asset.rs, handlers_collection.rs, dto.rs, entitlement.rs}`
- Data/migration: `services/api/migrations/<ts>_assets_create_tables.sql` and `.down.sql`
- React/UI: none in this story (S114 and T227 cover UI)
- Mocks/fixtures: `testing/fixtures/assets.rs` entitled and unentitled tenants, editor, viewer, foreign tenant, 20 clean files, one quarantined file, 5-field metadata schema, 3-level collection tree

## TDD harness

- Test path: `testing/features/F057/api/`, `testing/features/F057/database/`
- Feature flag: `F057_FEATURE`
- Targeted command: `cargo xtask test-feature F057`
- Full command: `cargo xtask test-all`
- First failing tests: `asset_register_returns_version_one`, `asset_register_unscanned_file_invalid`, `asset_metadata_type_mismatch_invalid`, `asset_missing_entitlement_denied`, `asset_search_uses_gin_index`, `collection_depth_six_rejected`, `asset_archive_hides_from_collections`

## Exit criteria

- [ ] Requirement tests SR-S113-01 through SR-S113-07 written first and failing
- [ ] Tasks T225 and T226 complete and wired through `services/api` router
- [ ] Unit, API, database, permission tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/assets/routes.rs` mounted in `services/api/src/router.rs` behind `F057_FEATURE`
- [ ] Handoff evidence recorded in the F057 ticket
