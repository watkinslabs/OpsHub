---
id: T141
type: task
status: planned
parent_epic: E004
parent_feature: F036
parent_story: S071
depends_on: [S071]
owned_paths: [services/api/migrations/*_sharing_*.sql, crates/domain/src/sharing/**, crates/persistence/src/sharing/**, crates/auth/src/sharing/**, services/api/src/sharing/**, testing/features/F036/database/**, testing/features/F036/api/**, testing/features/F036/performance/**]
feature_flag: F036_FEATURE
branch: t141-share-grants-api
started_at: null
finished_at: null
---

# T141 — Share grants API

## Identity

- Parent story: `S071` Resource sharing grants
- Owner: platform
- Branch: `t141-share-grants-api`
- Decision references: `docs/architecture-decisions.md` sections 2–4; `docs/capability-contracts.md` row F036

## Objective

Create the sharing schema, the `ShareRepository` that owns every `shares` query, the grant use cases with deny-wins and closest-allow evaluation plugged into the F003 engine, the four share routes, and the hourly expiry sweeper.

## Specification

- Owned paths: `services/api/migrations/<ts>_sharing_create_tables.sql`, `services/api/migrations/<ts>_sharing_create_tables.down.sql`, `crates/domain/src/sharing/{mod.rs, share.rs, role.rs, evaluate.rs, errors.rs, service.rs, sweeper.rs, repository.rs}` (`repository.rs` declares the `ShareRepository` trait; no SQL in this crate), `crates/persistence/src/sharing/{mod.rs, share_repository.rs}`, `crates/auth/src/sharing/{mod.rs, grant_source.rs}`, `services/api/src/sharing/{mod.rs, routes.rs, handlers_share.rs, dto.rs}`
- Contract/input: DDL for `shares`, `share_links`, `guest_invitations`, `guest_users` per F036 ticket section 4; `CreateShareRequest { target_kind, target_id, principal: { kind, id }, role, effect, expires_at? }`, `UpdateShareRequest { role?, effect?, expires_at? }`, list query `{ cursor?, limit?, principal_kind?, effect? }`; headers `Idempotency-Key`, `If-Match`; F003 `GrantSource` trait `{ fn grants_for(actor, target_chain) -> Vec<Grant> }` served from `ShareRepository::list_for_principal` and `list_for_target`; F005 `ancestors(target) -> Vec<TargetRef>`; F002 group membership lookup.
- Output/behavior: routes `GET /api/v1/{target_kind}/{target_id}/shares`, `POST /api/v1/shares`, `PATCH /api/v1/shares/{id}`, `DELETE /api/v1/shares/{id}` return `ShareResponse` and `Page<ShareResponse>` with `inherited_from` on inherited entries; duplicate pair → `409 already_shared` detected by `ShareRepository::find_grant`; last-owner revoke or downgrade → `409 last_owner` decided by `ShareRepository::lock_owner_grants` and `count_owners`, which take the same row lock in the same transaction that `select ... for update` took before and serialize the same concurrent revokes; `evaluate_access` returns `EffectiveAccess` applying any deny on the chain first, then the allow closest to the target, ignoring grants with `expires_at < now`, caching per `(actor_id, target)` for the request; events `share.granted.v1`, `share.updated.v1`, `share.revoked.v1` in the same transaction as audit rows; grant, update, and revoke each run in one `UnitOfWork` that also writes the audit row and enqueues the outbox event; `sweep_expired` runs hourly, batches through `ShareRepository::claim_expired(cutoff, limit)` and `revoke(share_id)` rather than issuing SQL, and publishes `share.revoked.v1 { reason: expired }` idempotently; `sqlx migrate revert` drops the four tables.
- Dependencies: the shared `Repository` and `UnitOfWork` contracts in `crates/persistence`; F003 engine registry in `crates/auth/src/engine.rs` accepting a `GrantSource`; F005 ancestry; F002 groups; F004 outbox writer and scheduler.
- Feature flag: `F036_FEATURE` gates router mounting and `GrantSource` registration; migration runs regardless.

## TDD

- Failing test first: `testing/features/F036/database/migration_tests.rs::sharing_tables_exist_with_constraints`, `::share_unique_per_target_principal`, `::sharing_foreign_keys_restrict_delete`, `::sharing_polymorphic_refs_have_no_orphans`, `::rollback_drops_tables`; `testing/features/F036/api/share_tests.rs::share_grant_returns_version_one`, `::share_duplicate_principal_conflicts`, `::share_update_stale_version_conflicts`, `::share_last_owner_revoke_conflicts`, `::share_list_includes_inherited_with_source`, `::share_editor_denied`, `::share_cross_tenant_not_found`; `testing/features/F036/api/evaluate_tests.rs::share_deny_beats_inherited_allow`, `::share_closest_allow_narrows_role`, `::share_expired_grant_ignored_and_swept`, `::share_no_grant_denies`; `testing/features/F036/performance/evaluate_bench.rs::evaluate_access_overhead_p95`; API and evaluation tests exercise the routes and `ShareRepository` trait and contain no SQL
- Targeted command: `cargo xtask test-feature F036`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/sharing.rs` tenants A and B, owner, admin, editor, `dana`, group `Contractors`, workspace with folder and sheet; schema-per-worker database; in-memory outbox recorder; fixed clock

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; router mounted in `services/api/src/router.rs`, `ShareRepository` registered in `crates/persistence/src/sharing/mod.rs`, and `ShareGrantSource` registered in `crates/auth/src/engine.rs` behind the flag; `cargo xtask check-persistence` and OpenAPI regeneration pass without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S071
- [ ] `finished_at` recorded
