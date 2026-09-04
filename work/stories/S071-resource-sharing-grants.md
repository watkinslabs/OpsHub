---
id: S071
type: story
status: planned
parent_epic: E004
parent_feature: F036
depends_on: [F003, F005]
owned_paths: [crates/domain/src/sharing/**, crates/persistence/src/sharing/**, crates/auth/src/sharing/**, services/api/src/sharing/**, apps/web/src/features/sharing/**, services/api/migrations/*_sharing_*.sql, testing/features/F036/**]
feature_flag: F036_FEATURE
branch: s071-resource-sharing-grants
started_at: null
finished_at: null
---

# S071 — Resource sharing grants

## Identity

- Parent feature: `F036` Sharing, guests, and links
- Owner: platform
- Branch: `s071-resource-sharing-grants`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 6; `docs/capability-contracts.md` row F036

## Vertical slice

As a resource owner, I want to grant users and groups a specific role on a workspace, folder, sheet, view, report, dashboard, or document, deny a principal explicitly, and manage those grants in a share dialog, so that access is granular, narrowable, and visible.

## Requirements

- **SR-S071-01:** `POST /api/v1/shares` creates one `shares` row per `(target, principal)` with `role`, `effect`, and optional `expires_at`, returns `ShareResponse` version 1, and publishes `share.granted.v1`; a duplicate pair returns `409 conflict` with `field_errors.principal = "already_shared"` (covers FR-F036-01, FR-F036-02).
- **SR-S071-02:** `PATCH /api/v1/shares/{id}` requires `If-Match` and publishes `share.updated.v1`; `DELETE` publishes `share.revoked.v1`; revoking or downgrading the last `owner` grant returns `409 conflict` with `field_errors.role = "last_owner"`, decided under `ShareRepository::lock_owner_grants` and `count_owners` in the revoke `UnitOfWork` so concurrent revokes stay serialized (FR-F036-02, FR-F036-03).
- **SR-S071-03:** `ShareGrantSource` in `crates/auth/src/sharing/` reads grants through `ShareRepository::list_for_principal` and `list_for_target` and evaluates deny-wins then closest-allow over the `target → folder → workspace` chain for the actor and its groups; no grant means deny; evaluation errors fail closed (FR-F036-04, NFR-F036-04).
- **SR-S071-04:** `GET /api/v1/{target_kind}/{target_id}/shares` returns direct and inherited grants with `inherited_from`, cursor paging with `limit` ≤ 200, and `principal_kind` and `effect` filters, and requires owner or admin (FR-F036-05).
- **SR-S071-05:** Expired grants are ignored by evaluation and swept hourly into `share.revoked.v1` with `reason = expired`; the sweeper batches through `ShareRepository::claim_expired(cutoff, limit)` and `revoke(share_id)` and issues no SQL of its own (FR-F036-13).
- **SR-S071-06:** `ShareDialog` with `PeopleList`, `RoleSelect`, `AddPeopleSearch`, and the admin-only `Deny` option renders loading, empty, error, denied, stale, and offline states and rolls back optimistic role changes on `conflict` (FR-F036-14).
- **SR-S071-07:** Every mutation checks `Idempotency-Key` and runs in one `UnitOfWork` whose base repository contract writes the audit row and enqueues the outbox event; editors receive `403 denied` on every share route and foreign tenants `404 not_found`; evaluation adds ≤ 5 ms p95 (FR-F036-15, NFR-F036-01).

## Surfaces

- Infrastructure/container: hourly `sharing.sweep_expired` job registered in the API process scheduler
- Rust service/API: `crates/domain/src/sharing/{share.rs, role.rs, evaluate.rs, errors.rs, service.rs, sweeper.rs}` (repository traits only, no SQL); `crates/persistence/src/sharing/{mod.rs, share_repository.rs}` holding every share query; `crates/auth/src/sharing/{grant_source.rs}`; `services/api/src/sharing/{routes.rs, handlers_share.rs, dto.rs}`
- Data/migration: `services/api/migrations/<ts>_sharing_create_tables.sql` creating `shares`, `share_links`, `guest_invitations`, `guest_users` with constraints and indexes from ticket section 4
- React/UI: `apps/web/src/features/sharing/{ShareDialog.tsx, PeopleList.tsx, PersonRow.tsx, RoleSelect.tsx, AddPeopleSearch.tsx, api.ts, hooks.ts}`
- Mocks/fixtures: `testing/fixtures/sharing.rs` owner, admin, editor, viewer, `dana`, group `Contractors`, foreign tenant, seeded workspace grant and sheet deny; in-memory outbox recorder; MSW handlers for the dialog

## TDD harness

- Test path: `testing/features/F036/{api,database,frontend,performance}/`
- Feature flag: `F036_FEATURE`
- Targeted command: `cargo xtask test-feature F036`
- Full command: `cargo xtask test-all`
- First failing tests: `share_grant_returns_version_one`, `share_duplicate_principal_conflicts`, `share_last_owner_revoke_conflicts`, `share_deny_beats_inherited_allow`, `share_closest_allow_narrows_role`, `share_editor_denied`, `share_dialog_role_change_rolls_back_on_conflict`

## Exit criteria

- [ ] Requirement tests SR-S071-01 through SR-S071-07 written first and failing
- [ ] Tasks T141 and T142 complete and wired through `services/api` router and the F003 `GrantSource` registry
- [ ] Unit, API, database, React, permission, and performance tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/sharing/routes.rs` mounted in `services/api/src/router.rs`; `crates/auth/src/sharing/grant_source.rs` registered in `crates/auth/src/engine.rs` and backed by `crates/persistence/src/sharing/share_repository.rs`; `apps/web/src/features/sharing/ShareDialog.tsx` opened from the sheet header `Share` button
- [ ] Handoff evidence recorded in the F036 ticket
