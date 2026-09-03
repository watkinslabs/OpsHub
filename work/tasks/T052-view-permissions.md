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

- Owned paths: `crates/domain/src/views/{share.rs, service_share.rs, scoped_reader.rs}`, `services/api/src/views/{handlers_share.rs}`, `apps/web/src/features/views/{ShareViewDialog.tsx, ExportViewButton.tsx, ViewSwitcher.tsx}`
- Contract/input: `ShareViewRequest { principal_kind: user|group, principal_id, role: viewer|editor, expires_at? }` on `POST /api/v1/views/{id}/share`; list query `{ cursor?, limit?, kind?, sort? }` on `GET /api/v1/sheets/{sheet_id}/views`; `POST /api/v1/exports` (F010) with `{ view_id, format: csv }`.
- Output/behavior: `share_view` requires owner, rejects a null `principal_id` and a `principal_kind` outside `user|group`, rejects a second live share for the same principal with `conflict`, publishes `view.shared.v1`, and returns `ViewShareResponse { id, principal_kind, principal_id, role, expires_at }`; `revoke_share` sets `revoked_at`; F013 mints no tokens and registers no unauthenticated route, so `list_views` unions private-owned, `sheet`, and shared views and hides everything else, and an F036 scoped-token actor targeting this view reads it through the same `view_rows` filtering path; `ShareViewDialog` lists user and group shares with revoke and links to F036 for public share links; `ExportViewButton` calls the F010 export with `view_id` and links to the job status; telemetry `view_shared`, `view_exported`.
- Dependencies: T051 complete page; F003 principal resolution for groups; F010 export job accepting `view_id`; F036 is not required because view links are scoped to one view and use this feature's `view_shares` table.
- Feature flag: `F013_FEATURE`.

## TDD

- Failing test first: `testing/features/F013/api/view_share_tests.rs::view_share_requires_principal_and_is_unique`, `::view_share_non_owner_denied`, `::view_list_hides_unshared_private`, `::scoped_reader_cannot_mutate`, `::revoked_share_not_found`, `::group_share_visible_to_member`; `testing/features/F013/frontend/ShareViewDialog.test.tsx::share_dialog_manages_user_and_group_shares`, `::hidden_for_non_owner`; `testing/features/F013/e2e/views.spec.ts::group_share_read_only_for_member`; `testing/features/F013/performance/view_rows_bench.rs::view_rows_filtered_100k_p95`, `::card_lane_move_p95`, `::calendar_month_5k_rows_p95`
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
