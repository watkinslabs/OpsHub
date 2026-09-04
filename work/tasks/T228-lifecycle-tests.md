---
id: T228
type: task
status: planned
parent_epic: E008
parent_feature: F057
parent_story: S114
depends_on: [T227]
owned_paths: [testing/features/F057/e2e/**, testing/features/F057/accessibility/**, testing/features/F057/performance/**, testing/features/F057/api/**, testing/features/F057/database/**]
feature_flag: F057_FEATURE
branch: t228-lifecycle-tests
started_at: null
finished_at: null
---

# T228 — Lifecycle tests

## Identity

- Parent story: `S114` Asset governance
- Owner: platform
- Branch: `t228-lifecycle-tests`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 9; `docs/capability-contracts.md` row F057

## Objective

Prove the full asset lifecycle (register, render, rights, approve, collect, archive, purge) end to end with permission, accessibility, and performance evidence.

## Specification

- Owned paths: `testing/features/F057/api/lifecycle_tests.rs`, `testing/features/F057/database/constraint_tests.rs`, `testing/features/F057/e2e/assets.spec.ts`, `testing/features/F057/accessibility/assets.a11y.spec.ts`, `testing/features/F057/performance/asset_bench.rs`
- Contract/input: lifecycle test drives one asset through every state transition and asserts the exact event sequence `asset.created.v1`, `asset.rendition-ready.v1` ×3, `asset.rights-updated.v1`, `asset.updated.v1` (pending), `asset.updated.v1` (approved), `asset.archived.v1`; the 200,000-asset generator seeds the performance tenant.
- Output/behavior: E2E covers register → thumbnails appear → rights → approval from the approver inbox → `Usable` badge → add to collection → archive → hidden; expired rights and rejected approval both show `Not usable` reasons; unentitled tenant sees the upsell; axe reports zero serious violations on library, drawer, and tree; performance lane records list p95 (< 500 ms) and thumbnail readiness (< 60 s p95 for 50 MB).
- Data access: no test opens a connection or issues SQL of its own — every fixture write and every assertion goes through the `crates/persistence/src/assets/` repositories (`AssetRepository`, `AssetTagRepository`, `AssetRenditionRepository`, `AssetRightsRepository`, `AssetCollectionRepository`, `AssetMetadataFieldRepository`), including the 200,000-asset generator, which inserts in repository batches (decision section 2.1). `constraint_tests.rs` is the exception by purpose: it asserts the normalized shape directly — duplicate `asset_tags` row rejected, `asset_tag_definitions(tenant_id, slug)` unique, territory code absent from `asset_territory_codes` rejected, channel outside the check constraint rejected, `asset_metadata_values` rejected with zero or two typed columns set, a `select` value rejected when the option is not declared, `asset_metadata_fields` row removal rejected while values exist, and `assets.probe` the only remaining `jsonb` column in the module.
- Dependencies: T227 complete; Playwright, axe, and MinIO harness from `testing/harness/`; F027 purge job for the retention assertion.
- Feature flag: `F057_FEATURE`

## TDD

- Failing test first: `testing/features/F057/api/lifecycle_tests.rs::asset_lifecycle_event_sequence`, `::archived_asset_purged_after_retention`; `testing/features/F057/database/constraint_tests.rs::asset_tag_row_unique_per_asset`, `::unknown_territory_code_rejected`, `::invalid_channel_rejected`, `::metadata_value_requires_exactly_one_typed_column`, `::metadata_select_value_must_be_declared_option`, `::metadata_field_removal_blocked_with_values`, `::probe_is_only_jsonb_column`; `testing/features/F057/e2e/assets.spec.ts::register_render_rights_approve_collect_archive`, `::expired_rights_shows_not_usable`, `::unentitled_tenant_sees_upsell`, `::viewer_has_no_mutation_controls`; `testing/features/F057/accessibility/assets.a11y.spec.ts::library_drawer_tree_have_no_serious_axe_violations`; `testing/features/F057/performance/asset_bench.rs::library_list_200k_p95`, `::thumbnail_ready_within_60s`
- Targeted command: `cargo xtask test-feature F057`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: 200,000-asset generator with fixed seed; real worker with `RenditionBackend` fake; Playwright against the real API on seeded entitled and unentitled tenants

## Exit criteria

- [ ] Lifecycle, database-constraint, E2E, accessibility, and performance lanes pass in targeted and full modes
- [ ] p95 targets from NFR-F057-01 recorded under `testing/evidence/F057/performance/`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S114
- [ ] `finished_at` recorded
