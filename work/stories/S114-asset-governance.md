---
id: S114
type: story
status: planned
parent_epic: E008
parent_feature: F057
depends_on: [S113]
owned_paths: [crates/domain/src/assets/**, crates/persistence/src/assets/**, services/api/src/assets/**, services/worker/src/assets/**, apps/web/src/features/assets/**, testing/features/F057/**]
feature_flag: F057_FEATURE
branch: s114-asset-governance
started_at: null
finished_at: null
---

# S114 — Asset governance

## Identity

- Parent feature: `F057` DAM assets
- Owner: platform
- Branch: `s114-asset-governance`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 5, 6, 7, 9; `docs/capability-contracts.md` row F057

## Vertical slice

As a brand manager, I want renditions generated automatically, usage rights with expiry, approval through the standard approval engine, and a library UI that shows whether an asset is usable, so that only approved, rights-cleared material is used.

## Requirements

- **SR-S114-01:** `services/worker/src/assets/rendition_job.rs` consumes `assets.render`, produces `thumbnail`, `preview`, `web` for images and `poster`, `preview` for video, and persists each through `AssetRenditionRepository::upsert_rendition` with checksum — the job file holds no SQL — then publishes `asset.rendition-ready.v1` per kind from the same `UnitOfWork`; after 3 failed attempts the asset is `rendition_state: failed` with `error_code` (FR-F057-03, FR-F057-14).
- **SR-S114-02:** `GET /api/v1/assets/{id}/renditions/{kind}` re-checks F017 file read access, returns 302 to a 15-minute signed URL when ready, `404` for unknown kind, and `409` with `rendition_state` when pending or failed (FR-F057-04).
- **SR-S114-03:** `PUT /api/v1/assets/{id}/rights` validates license, dates, ISO territories, and channels, and `AssetRightsRepository::upsert_rights` with `replace_rights_territories` and `replace_rights_channels` writes the `asset_rights` row plus its `asset_rights_territories` and `asset_rights_channels` rows in one `UnitOfWork` while the request and response keep both as JSON string arrays; it publishes `asset.rights-updated.v1`, and every read derives `rights_state: active|expired|none` from the typed `valid_until` column at end of day in the tenant timezone (FR-F057-05).
- **SR-S114-04:** `PATCH /api/v1/assets/{id}` with `{ approval: request }` creates an F020 approval under the tenant DAM policy and sets `approval_state: pending`; `services/worker/src/assets/approval_consumer.rs` applies `approval.decided.v1` to `approved` or `rejected` through `AssetRepository::update_asset_fields` and issues no SQL of its own; `usable` is true only for `approved` and not `expired` (FR-F057-06).
- **SR-S114-05:** `AssetLibraryPage`, `AssetDetailDrawer`, `RightsForm`, `ApprovalPanel`, and `CollectionTree` render loading, empty, error, denied, stale, conflict, offline, and success states; unusable assets show a reason badge; viewers see no mutation controls (FR-F057-13, NFR-F057-03).
- **SR-S114-06:** The library list over 200,000 assets meets NFR-F057-01 and thumbnails are ready within 60 s p95 for 50 MB images (NFR-F057-01).
- **SR-S114-07:** Rendition jobs are idempotent on the unique `(asset_id, file_version_id, kind)` index through `AssetRenditionRepository::upsert_rendition`, the rights-expiry sweep reads `AssetRightsRepository::list_rights_expiring_before` rather than scanning arrays, and both expose the metrics in NFR-F057-04.

## Surfaces

- Data access: `crates/persistence/src/assets/{rendition_repository.rs, rights_repository.rs, asset_repository.rs}` hold every SQL statement for this slice — `AssetRenditionRepository` owns `asset_renditions`, `AssetRightsRepository` owns `asset_rights`, `asset_rights_territories`, `asset_rights_channels`, and the seeded `asset_territory_codes`, and the approval consumer reuses `AssetRepository`. The rendition worker, the approval consumer, the rendition and rights handlers, and the rights-expiry sweep depend on these traits and contain no `sqlx::query*` call (decision section 2.1)
- Infrastructure/container: JetStream stream `assets` with subjects `assets.render` and consumer `assets-video` (concurrency 2, 10-minute timeout) declared in `services/worker/src/assets/mod.rs`
- Rust service/API: `crates/domain/src/assets/{rendition.rs, rights.rs, approval.rs, usable.rs}`; `services/api/src/assets/{handlers_rendition.rs, handlers_rights.rs}`; `services/worker/src/assets/{mod.rs, rendition_job.rs, backend.rs, approval_consumer.rs}`
- Data/migration: none new; uses the thirteen tables from S113, including `asset_rights_territories`, `asset_rights_channels`, and `asset_territory_codes`
- React/UI: `apps/web/src/features/assets/{AssetLibraryPage.tsx, AssetGrid.tsx, AssetTile.tsx, AssetDetailDrawer.tsx, RenditionPanel.tsx, RightsForm.tsx, ApprovalPanel.tsx, MetadataForm.tsx, CollectionTree.tsx, CollectionAssetsEditor.tsx, RegisterAssetDialog.tsx, EntitlementUpsell.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: `RenditionBackend` fake with deterministic bytes; MinIO bucket prefix per worker; F020 fixture policy with one approver; MSW handlers for pending → ready renditions

## TDD harness

- Test path: `testing/features/F057/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F057_FEATURE`
- Targeted command: `cargo xtask test-feature F057`
- Full command: `cargo xtask test-all`
- First failing tests: `rendition_job_writes_three_image_kinds`, `rendition_url_redirects_when_ready`, `rights_expired_makes_asset_unusable`, `rights_replace_rewrites_territory_rows`, `rights_unknown_territory_code_rejected`, `approval_decision_sets_state`, `drawer_shows_not_usable_reason`, `library_list_200k_p95`

## Exit criteria

- [ ] Requirement tests SR-S114-01 through SR-S114-07 written first and failing
- [ ] Tasks T227 and T228 complete; UI wired to real API through generated client
- [ ] Unit, API, worker, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `apps/web/src/features/assets/AssetLibraryPage.tsx` mounted at `/w/:workspaceId/assets`; worker consumers `services/worker/src/assets/rendition_job.rs` and `approval_consumer.rs` registered in `services/worker/src/main.rs`
- [ ] Handoff evidence recorded in the F057 ticket
