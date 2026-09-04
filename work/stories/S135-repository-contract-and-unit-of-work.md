---
id: S135
type: story
status: planned
parent_epic: E001
parent_feature: F068
depends_on: [F001]
owned_paths: [crates/persistence/src/lib.rs, crates/persistence/src/repository/**, crates/persistence/src/uow/**, testing/features/F068/api/**, testing/features/F068/database/**]
feature_flag: F068_FEATURE
branch: s135-repository-contract-and-unit-of-work
started_at: null
finished_at: null
---

# S135 — Repository contract and unit of work

## Identity

- Parent feature: `F068` Persistence layer and data access classes
- Owner: platform
- Branch: `s135-repository-contract-and-unit-of-work`
- Decision references: `docs/architecture-decisions.md` sections 2 and 2.1 (canonical data model and data access), section 3 (cursor and version conventions); `docs/capability-contracts.md` row F068 (aggregate `repository`, module `persistence`)

## Vertical slice

As a platform maintainer, I want the sealed `Repository` contract with its seven operations, the `BaseRepository` that is its only implementation, the `UnitOfWork` that owns a transaction shared by several repositories, and `UserRepository` (F002's file, referenced as the worked example rather than owned here) over F002's `users` table as the worked example, so that a new object type is added by declaring a `RepositorySpec` and the tenant predicate, soft-delete filter, version check, audit row, and outbox row are applied whether the author remembers them or not.

## Requirements

- **SR-S135-01:** `crates/persistence/src/repository/mod.rs` declares the seven operations with the exact signatures and associated types of FR-F068-01, and the trait is sealed by a private module so `BaseRepository<'_, S>` is its only implementation and a hand-written implementation fails to compile (FR-F068-02).
- **SR-S135-02:** `RepositorySpec` carries constants, associated types, `map_row`, `bind_new`, `bind_patch`, `payload`, and `event`, and no member of it returns SQL text or an executor, so a specification cannot express a predicate (FR-F068-03).
- **SR-S135-03:** Every generated read binds `tenant_id = $1` from `TenantCtx` and adds `and deleted_at is null` unless `Visibility::Deleted` or `Visibility::Any` is passed; a foreign-tenant or soft-deleted row returns `RepoError::NotFound` with no distinguishing signal (FR-F068-04, NFR-F068-02).
- **SR-S135-04:** `update`, `soft_delete`, and `restore` are one statement carrying `version = $expected`, bump the version, and return the new entity; zero affected rows triggers one scoped re-read that separates `VersionConflict { expected, actual }` from `NotFound` (FR-F068-05).
- **SR-S135-05:** Each mutation writes the `audit_events` row and the `outbox_events` row on the same connection before returning, with `before`, `after`, and `field_diff` computed by the base from `COLUMNS`, and no public `audit`, `enqueue`, or `publish` method exists on any type in the crate (FR-F068-06).
- **SR-S135-06:** `S::event(op)` is total over the five mutating operations and returns `EventName::Named` or `EventName::Silent`; `UserSpec` maps insert, update, soft delete, restore, and purge to `user.created.v1`, `user.updated.v1`, `user.deactivated.v1`, `user.updated.v1`, and a silent purge (FR-F068-07).
- **SR-S135-07:** `WriteCtx` is the only argument type of a mutating method and carries the idempotency key; a replayed key hits the `(tenant_id, idempotency_key)` unique index and returns the first call's entity rather than writing twice (FR-F068-08).
- **SR-S135-08:** `PurgeCtx` is constructible only from a `PurgeGrant` verified against a `purge:{aggregate}` scope, deletes the row and its `CO_TABLES` children in one batch, writes an audit row with the full pre-image, and publishes nothing (FR-F068-09).
- **SR-S135-09:** `list` is keyset paginated over F028's `SignedCursor` with the payload, 24-hour expiry, `SORTABLE` check, and `table`, `tenant_id`, `order`, and `filter_hash` mismatch rules of FR-F068-10, returning `Page { items, next_cursor, has_more }` and never using `offset`.
- **SR-S135-10:** `UnitOfWork::begin`, `repo::<S>()`, `commit`, and `rollback` thread one transaction through several repositories; `repo` borrows `&mut self` so only one handle is live, and `BaseRepository` has no `begin`, `commit`, `rollback`, or `savepoint`, so a handed transaction is never nested and a pool handle wraps its own single write (FR-F068-11, FR-F068-12).
- **SR-S135-11:** `UserRepository` is `BaseRepository<'static, UserSpec>` over F002's `users` table and exposes `find_by_email`, `list_active_in_group`, and `count_by_status` built from `select` and `select_page`; the crate exposes no `query`, `execute`, `raw`, `sql`, or `pool` member and re-exports no SQLx type (FR-F068-13).

## Surfaces

- Rust crate: `crates/persistence/src/lib.rs`; `crates/persistence/src/repository/{mod.rs, spec.rs, filter.rs, base.rs, audit.rs, outbox.rs, cursor.rs, error.rs}`; `crates/persistence/src/uow/mod.rs`; `crates/persistence/src/users/{mod.rs, spec.rs, queries.rs}`
- Consumed and not edited: F004's `crates/persistence/src/runtime/**` pool builder, F028's `SignedCursor` in `crates/contracts/src/public-api/`, F003's `audit_events` table, F004's `outbox_events` table, F002's `users` schema
- Data: no migration; the story asserts F004's `outbox_events_tenant_idempotency_idx` on `(tenant_id, idempotency_key)` rather than creating it
- Production call path: `services/api/src/tenants/` uses `UserRepository` for `GET /api/v1/users`, `POST /api/v1/users`, and `PATCH /api/v1/users/{id}`
- Mocks/fixtures: `testing/fixtures/persistence/seed.rs` with tenants A and B, 3 and 100,000 users, fixed UUIDv7 sequence, fixed clock, fixed cursor HMAC key; one `postgres:18` container per test session with one database per worker

## TDD harness

- Test path: `testing/features/F068/{api,database}/`
- Feature flag: `F068_FEATURE`
- Targeted command: `cargo xtask test-feature F068`
- Full command: `cargo xtask test-all`
- First failing tests: `hand_written_repository_impl_does_not_compile`, `get_across_tenants_is_not_found`, `list_hides_soft_deleted_rows_by_default`, `update_with_stale_version_conflicts_and_writes_nothing`, `insert_writes_audit_and_outbox_rows_in_one_transaction`, `rollback_removes_write_audit_and_outbox_together`, `replayed_idempotency_key_returns_first_entity`, `cursor_from_other_tenant_is_rejected`, `purge_requires_a_verified_grant`, `unit_of_work_shares_one_transaction_across_two_repositories`

## Exit criteria

- [ ] Requirement tests SR-S135-01 through SR-S135-11 written first and observed failing
- [ ] Tasks T269 and T270 complete, with `UserRepository` wired into `services/api/src/tenants/` and proven by an integration test that asserts the audit and outbox rows
- [ ] Compile-fail, unit, and database lanes pass in targeted and full modes against a throwaway PostgreSQL 18
- [ ] Crate public surface contains no SQLx type and no generic query member, verified by `cargo xtask check-persistence` from S136
- [ ] All files ≤ 500 lines; handoff evidence recorded in the F068 ticket
