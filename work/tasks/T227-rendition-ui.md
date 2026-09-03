---
id: T227
type: task
status: planned
parent_epic: E008
parent_feature: F057
parent_story: S114
depends_on: [S114]
owned_paths: [crates/domain/src/assets/**, services/api/src/assets/**, services/worker/src/assets/**, apps/web/src/features/assets/**, testing/features/F057/api/**, testing/features/F057/frontend/**]
feature_flag: F057_FEATURE
branch: t227-rendition-ui
started_at: null
finished_at: null
---

# T227 — Rendition UI

## Identity

- Parent story: `S114` Asset governance
- Owner: platform
- Branch: `t227-rendition-ui`
- Decision references: `docs/architecture-decisions.md` sections 5, 6, 7; `docs/capability-contracts.md` row F057

## Objective

Build the rendition worker, the rendition and approval paths, and the asset library UI with grid, detail drawer, rights form, approval panel, and collection tree wired to the real API.

## Specification

- Owned paths: `crates/domain/src/assets/{rendition.rs, approval.rs}`, `services/api/src/assets/handlers_rendition.rs`, `services/worker/src/assets/{mod.rs, rendition_job.rs, backend.rs, approval_consumer.rs}`, `apps/web/src/features/assets/{AssetLibraryPage.tsx, AssetGrid.tsx, AssetTile.tsx, AssetDetailDrawer.tsx, RenditionPanel.tsx, RightsForm.tsx, ApprovalPanel.tsx, MetadataForm.tsx, CollectionTree.tsx, CollectionAssetsEditor.tsx, RegisterAssetDialog.tsx, EntitlementUpsell.tsx, api.ts, hooks.ts, routes.ts}`
- Contract/input: job payload `{ tenant_id, asset_id, file_version_id, kinds, correlation_id }`; `RenditionBackend` trait `render(source: ByteStream, kind) -> Result<Rendered, RenditionError>`; `GET /api/v1/assets/{id}/renditions/{kind}`; `PATCH /api/v1/assets/{id} { approval: request }`; generated `AssetsApi` client.
- Output/behavior: worker writes renditions with checksum and publishes `asset.rendition-ready.v1`; three failures set `rendition_state: failed` with `error_code`; rendition route redirects to a 15-minute signed URL or returns `409`; approval request creates an F020 approval; consumer applies decisions; UI renders virtualized tiles with badges, drawer with renditions, rights form, approval history, metadata form, collection tree with keyboard expand/collapse, register dialog listing clean files only, and all states in ticket section 3; telemetry per ticket section 4.
- Dependencies: T226 rights and usable derivation; F017 signed URL helper; F020 `approvals::request`; F046 notification channel for rendition-ready refresh.
- Feature flag: `F057_FEATURE` read through `useFlag`; routes not registered when off.

## TDD

- Failing test first: `testing/features/F057/api/rendition_tests.rs::rendition_job_writes_three_image_kinds`, `::rendition_job_video_poster_and_preview`, `::rendition_failed_after_three_attempts`, `::rendition_url_redirects_when_ready`, `::rendition_url_unreadable_file_not_found`; `testing/features/F057/api/approval_tests.rs::approval_decision_sets_state`; `testing/features/F057/frontend/AssetGrid.test.tsx::renders_tiles_with_badges`, `AssetDetailDrawer.test.tsx::drawer_shows_not_usable_reason`, `RightsForm.test.tsx::validates_dates_and_territories`, `CollectionTree.test.tsx::keyboard_expand_collapse`
- Targeted command: `cargo xtask test-feature F057`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `RenditionBackend` fake; MinIO prefix per worker; MSW handlers for pending → ready

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Worker consumers registered in `services/worker/src/main.rs`; routes mounted behind the flag
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S114
- [ ] `finished_at` recorded
