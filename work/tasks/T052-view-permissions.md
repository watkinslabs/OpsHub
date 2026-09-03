---
id: T052
type: task
status: planned
parent_epic: E003
parent_feature: F013
parent_story: S026
depends_on: [T051]
owned_paths: [crates/domain/src/views/**, services/api/src/views/**, apps/web/src/features/views/**, testing/features/F013/api/**, testing/features/F013/frontend/**, testing/features/F013/e2e/**, testing/features/F013/performance/**]
feature_flag: F013_FEATURE
branch: t052-view-permissions
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 3, 4, 6
- Capability contract: `docs/capability-contracts.md` row F013

# T052 — View permissions

## Identity

- Parent story: `S026` Timeline
- Owner: platform
- Branch: `t052-view-permissions`
- Decision references: `docs/architecture-decisions.md` sections 3, 4, 6; `docs/capability-contracts.md` row F013

## Objective

Implement view sharing to users, groups, and expiring links, the link actor with read-only scope, the visibility-aware list, the export handoff, and the performance proof for filtered view rows.

## Specification

- Owned paths: `crates/domain/src/views/{share.rs, service_share.rs, link_actor.rs}`, `services/api/src/views/{handlers_share.rs, public_link.rs}`, `apps/web/src/features/views/{ShareViewDialog.tsx, ExportViewButton.tsx, ViewSwitcher.tsx}`
- Contract/input: `ShareViewRequest { principal_kind: user|group|link, principal_id?, role: viewer|editor, expires_at? }` on `POST /api/v1/views/{id}/share`; `GET /public/views/{token}` resolves a link token to a `ViewLinkActor`; list query `{ cursor?, limit?, kind?, sort? }` on `GET /api/v1/sheets/{sheet_id}/views`; `POST /api/v1/exports` (F010) with `{ view_id, format: csv }`.
- Output/behavior: `share_view` requires owner, stores a 32-byte random token as SHA-256 `token_hash` for links, enforces `expires_at` ≤ now + 30 days, publishes `view.shared.v1`, and returns `ViewShareResponse { id, principal_kind, principal_id, role, expires_at, url? }`; `revoke_share` sets `revoked_at`; `link_actor.rs` grants `Permission::ViewRead` on that view only, rejects every mutation with `denied`, and returns `not_found` after expiry or revocation; `list_views` unions private-owned, `sheet`, and shared views and hides everything else; `ShareViewDialog` lists shares with revoke and copies the link URL; `ExportViewButton` calls the F010 export with `view_id` and links to the job status; telemetry `view_shared`, `view_exported`.
- Dependencies: T051 complete page; F003 principal resolution for groups; F010 export job accepting `view_id`; F036 is not required because view links are scoped to one view and use this feature's `view_shares` table.
- Feature flag: `F013_FEATURE`.

## TDD

- Failing test first: `testing/features/F013/api/view_share_tests.rs::view_share_link_expires_within_30_days`, `::view_share_non_owner_denied`, `::view_list_hides_unshared_private`, `::link_actor_cannot_mutate`, `::expired_link_not_found`, `::group_share_visible_to_member`; `testing/features/F013/frontend/ShareViewDialog.test.tsx::creates_link_share_and_copies_url`, `::hidden_for_non_owner`; `testing/features/F013/e2e/views.spec.ts::share_link_opens_read_only`; `testing/features/F013/performance/view_rows_bench.rs::view_rows_filtered_100k_p95`, `::card_lane_move_p95`, `::calendar_month_5k_rows_p95`
- Targeted command: `cargo xtask test-feature F013`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: group with two members, expired and active link tokens with fixed clock; 100,000-row generator with fixed seed; Playwright guest session with no tenant login

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Permission-negative suite green, including link actor and cross-tenant cases
- [ ] p95 targets from NFR-F013-01 met in the performance lane
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S026
- [ ] `finished_at` recorded
