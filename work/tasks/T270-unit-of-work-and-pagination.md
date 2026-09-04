---
id: T270
type: task
status: planned
parent_epic: E001
parent_feature: F068
parent_story: S135
depends_on: [S135]
owned_paths: [crates/persistence/src/uow/**, crates/persistence/src/repository/**, testing/features/F068/database/**]
feature_flag: F068_FEATURE
branch: t270-unit-of-work-and-pagination
started_at: null
finished_at: null
---

# T270 — Unit of work and pagination

## Identity

- Parent story: `S135` Repository contract and unit of work
- Owner: platform
- Branch: `t270-unit-of-work-and-pagination`
- Decision references: `docs/architecture-decisions.md` section 2.1 (one transaction owned by the unit of work) and section 3 (opaque signed cursors, mutation responses return the new version); `docs/capability-contracts.md` row F068

## Objective

Implement `UnitOfWork`, the pool-versus-transaction connection handle that decides whether a repository opens its own transaction, and the keyset pagination built on F028's signed cursor, and prove that the write, the audit row, and the outbox row are atomic on both paths.

## Specification

- Owned paths: `crates/persistence/src/uow/mod.rs`; `crates/persistence/src/repository/{cursor.rs, base.rs}` paging helpers
- Unit of work: `UnitOfWork::begin(db: &Database, ctx: TenantCtx)`, `fn repo<S: RepositorySpec>(&mut self) -> BaseRepository<'_, S>`, `async fn commit(self) -> Result<Committed { events, audits }, RepoError>`, `async fn rollback(self)`. `repo` borrows `&mut self` so one handle is live at a time and handles are used in sequence; `commit` and `rollback` take `self` by value so no handle outlives the transaction.
- Connection handle: private `Db<'a> { Pool(&'a PgPool), Tx(&'a mut PgConnection) }`. `Database::repo::<S>()` yields a `Db::Pool` handle whose every mutating method opens one transaction, writes the row, the audit row, and the outbox row, and commits before returning. `UnitOfWork::repo::<S>()` yields a `Db::Tx` handle that uses the caller's transaction. `BaseRepository` declares no `begin`, `commit`, `rollback`, or `savepoint`, so a handed transaction is never nested and the outbox insert is in the caller's transaction by construction.
- Pagination: `PageRequest { cursor, limit, sort, order }` with `Limit` clamped to 1–200 default 50; cursor payload `{ table, tenant_id, sort_value, id, order, filter_hash, issued_at }` encoded through F028's `SignedCursor` with HMAC-SHA256 and a 24-hour expiry; predicate `and (sort_col, id) > ($k, $id)` with `sort_col` required to be in `S::SORTABLE`; result `Page { items, next_cursor, has_more }`. A mismatch of `table`, `tenant_id`, `order`, or `filter_hash`, or an expired signature, is `RepoError::InvalidCursor`; an unknown sort key is `RepoError::InvalidSort`. `offset` appears nowhere.
- Observability: span `persistence.{aggregate}.{op}` with `tenant_id`, `correlation_id`, `version`, and `rows_affected`; counter `repository_operations_total{aggregate,op,outcome}`; histogram `repository_operation_duration_seconds{aggregate,op}`.
- Schema expectation, not a migration: F004's `outbox_events_tenant_idempotency_idx on outbox_events (tenant_id, idempotency_key) where idempotency_key is not null` is asserted at test time so its absence fails this task rather than silently disabling idempotency.
- Dependencies: T269's base contract; F028's `SignedCursor`; F004's pool builder and `outbox_events`; F003's `audit_events`; PostgreSQL 18 for the database lane.
- Feature flag: `F068_FEATURE` gates the harness lane; the crate compiles unconditionally.

## TDD

- Failing test first: `testing/features/F068/database/uow_tests.rs::unit_of_work_shares_one_transaction_across_two_repositories`, `::rollback_removes_write_audit_and_outbox_together`, `::pool_handle_commits_its_own_single_write`, `::repository_never_begins_a_nested_transaction`; `testing/features/F068/database/version_tests.rs::update_with_stale_version_conflicts_and_writes_nothing`, `::concurrent_updates_leave_exactly_one_conflict`, `::replayed_idempotency_key_returns_first_entity`; `testing/features/F068/database/pagination_tests.rs::keyset_paging_is_stable_under_concurrent_insert`, `::cursor_from_other_tenant_is_rejected`, `::cursor_with_changed_filter_is_rejected`, `::expired_cursor_is_rejected`, `::unknown_sort_key_is_invalid_sort`; `testing/features/F068/database/schema_expectations_tests.rs::outbox_idempotency_index_exists`
- Targeted command: `cargo xtask test-feature F068`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: one `postgres:18` container per test session with database `opshub_f068_w{worker}` per worker, F002, F003, and F004 migrations applied at setup and dropped at teardown; `testing/fixtures/persistence/seed.rs` tenants A and B with 3 and 100,000 users; fixed cursor HMAC key and fixed clock `2026-09-03T00:00:00Z`

## Exit criteria

- [ ] Tests written before implementation and observed failing against a throwaway PostgreSQL 18
- [ ] Atomicity proven on both the pool path and the unit-of-work path, with row counts unchanged after a rollback
- [ ] Page 2,000 over 100,000 users measured at the same cost as page 2, with no `offset` in any generated statement
- [ ] Owned-path check passes; every file ≤ 500 lines; lint and format gates pass
- [ ] Handoff evidence recorded in S135
- [ ] `finished_at` recorded
