---
id: T228
type: task
status: planned
parent_epic: E008
parent_feature: F057
parent_story: S114
depends_on: [T227]
owned_paths: [testing/features/F057/e2e/**, testing/features/F057/accessibility/**, testing/features/F057/performance/**, testing/features/F057/api/**]
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
- Decision references: `docs/architecture-decisions.md` section 9; `docs/capability-contracts.md` row F057

## Objective

Prove the full asset lifecycle (register, render, rights, approve, collect, archive, purge) end to end with permission, accessibility, and performance evidence.

## Specification

- Owned paths: `testing/features/F057/api/lifecycle_tests.rs`, `testing/features/F057/e2e/assets.spec.ts`, `testing/features/F057/accessibility/assets.a11y.spec.ts`, `testing/features/F057/performance/asset_bench.rs`
- Contract/input: lifecycle test drives one asset through every state transition and asserts the exact event sequence `asset.created.v1`, `asset.rendition-ready.v1` ×3, `asset.rights-updated.v1`, `asset.updated.v1` (pending), `asset.updated.v1` (approved), `asset.archived.v1`; the 200,000-asset generator seeds the performance tenant.
- Output/behavior: E2E covers register → thumbnails appear → rights → approval from the approver inbox → `Usable` badge → add to collection → archive → hidden; expired rights and rejected approval both show `Not usable` reasons; unentitled tenant sees the upsell; axe reports zero serious violations on library, drawer, and tree; performance lane records list p95 (< 500 ms) and thumbnail readiness (< 60 s p95 for 50 MB).
- Dependencies: T227 complete; Playwright, axe, and MinIO harness from `testing/harness/`; F027 purge job for the retention assertion.
- Feature flag: `F057_FEATURE`

## TDD

- Failing test first: `testing/features/F057/api/lifecycle_tests.rs::asset_lifecycle_event_sequence`, `::archived_asset_purged_after_retention`; `testing/features/F057/e2e/assets.spec.ts::register_render_rights_approve_collect_archive`, `::expired_rights_shows_not_usable`, `::unentitled_tenant_sees_upsell`, `::viewer_has_no_mutation_controls`; `testing/features/F057/accessibility/assets.a11y.spec.ts::library_drawer_tree_have_no_serious_axe_violations`; `testing/features/F057/performance/asset_bench.rs::library_list_200k_p95`, `::thumbnail_ready_within_60s`
- Targeted command: `cargo xtask test-feature F057`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: 200,000-asset generator with fixed seed; real worker with `RenditionBackend` fake; Playwright against the real API on seeded entitled and unentitled tenants

## Exit criteria

- [ ] Lifecycle, E2E, accessibility, and performance lanes pass in targeted and full modes
- [ ] p95 targets from NFR-F057-01 recorded under `testing/evidence/F057/performance/`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S114
- [ ] `finished_at` recorded
