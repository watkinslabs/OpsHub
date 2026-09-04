---
id: T269
type: task
status: planned
parent_epic: E001
parent_feature: F068
parent_story: S135
depends_on: [S135]
owned_paths: [crates/persistence/src/lib.rs, crates/persistence/src/repository/**, crates/persistence/src/users/**, testing/features/F068/api/**]
feature_flag: F068_FEATURE
branch: t269-repository-base-contract
started_at: null
finished_at: null
---

# T269 — Repository base contract

## Identity

- Parent story: `S135` Repository contract and unit of work
- Owner: platform
- Branch: `t269-repository-base-contract`
- Decision references: `docs/architecture-decisions.md` sections 2 and 2.1; `docs/capability-contracts.md` row F068 (aggregate `repository`, module `persistence`)

## Objective

Implement the sealed `Repository` contract, the `RepositorySpec` declaration surface, and the single `BaseRepository` implementation that applies the tenant predicate, soft-delete filter, optimistic version check, audit row, and outbox row, together with the worked `UserRepository` over F002's `users` table.

## Specification

- Owned paths: `crates/persistence/src/lib.rs`; `crates/persistence/src/repository/{mod.rs, spec.rs, filter.rs, base.rs, audit.rs, outbox.rs, error.rs}`; `crates/persistence/src/users/{mod.rs, spec.rs, queries.rs}`
- Contract: the seven signatures of FR-F068-01 over `async_trait` with associated types `Entity`, `Id`, `Filter`, `New`, `Patch`; `Version` a `NonZeroI64` newtype; `Deleted { id, version, deleted_at }`; `Purged { id, rows_removed }`; `TenantCtx { tenant_id, actor_id, correlation_id }`; `WriteCtx { tenant, idempotency_key, db }`; `PurgeCtx::new(tenant, grant)` with `PurgeGrant::verify(scopes, aggregate)`.
- Sealing: a private `sealed` module, `Repository: sealed::Sealed`, and the only `impl<S: RepositorySpec> Repository for BaseRepository<'_, S>`; `RepositorySpec` exposes `TABLE`, `AGGREGATE`, `COLUMNS`, `SORTABLE`, `CO_TABLES`, `map_row`, `bind_new`, `bind_patch`, `payload`, and `event`, and no member returning SQL text or an executor.
- Behavior: reads bind `tenant_id = $1` and add `and deleted_at is null` unless `Visibility::Deleted` or `Visibility::Any`; `update`, `soft_delete`, and `restore` are the single statement of FR-F068-05 with `version = $expected`, bumping the version and returning the entity, with one scoped re-read on zero rows to separate `VersionConflict { expected, actual }` from `NotFound`; each mutation writes the `audit_events` row with `before`, `after`, and `field_diff` derived from `COLUMNS` and the `outbox_events` row with `S::event(op)` and `S::payload(&entity)` on the same connection before returning; a replayed idempotency key hits the `(tenant_id, idempotency_key)` unique index and returns the first entity; `purge` deletes the row and its `CO_TABLES` children, audits the full pre-image, and publishes nothing.
- Worked example: `UserSpec` with `TABLE = "users"`, `AGGREGATE = "user"`, the thirteen `COLUMNS` of F002's `users` table, `SORTABLE = ["display_name", "created_at", "updated_at"]`, `CO_TABLES = []`, events `user.created.v1`, `user.updated.v1`, `user.deactivated.v1`; `UserFilter { status, email, group_id, created_after }`; `pub type UserRepository = BaseRepository<'static, UserSpec>;` with `find_by_email` over `users_tenant_email_idx`, `list_active_in_group`, and `count_by_status`, each built from `select` or `select_page`.
- Error mapping: `RepoError { NotFound, VersionConflict, InvalidCursor, InvalidSort, Forbidden, Constraint, Unavailable }` with the HTTP mapping recorded in F068 section 4; `Display` never carries a row value or a bound parameter.
- Dependencies: F001 workspace member and toolchain; F004's `crates/persistence/src/runtime/**` pool builder, read only; F003's `audit_events` and F004's `outbox_events` tables, written but not owned; F002's `users` schema.
- Feature flag: `F068_FEATURE` gates the `services/api/src/tenants/` call path that consumes `UserRepository`; the crate itself compiles unconditionally.

## TDD

- Failing test first: `testing/features/F068/api/ui/hand_written_repository.rs::hand_written_repository_impl_does_not_compile`, `testing/features/F068/api/ui/spec_returning_sql.rs::spec_cannot_return_sql_text`, `testing/features/F068/api/ui/purge_without_grant.rs::purge_ctx_requires_a_grant`; `testing/features/F068/api/base_tests.rs::select_always_binds_tenant_predicate`, `::select_adds_soft_delete_filter_by_default`, `::update_statement_carries_expected_version`, `::field_diff_covers_changed_columns_only`, `::event_mapping_is_total_over_mutations`; `testing/features/F068/api/user_repository_tests.rs::find_by_email_is_case_insensitive`, `::list_active_in_group_scopes_to_tenant`, `::count_by_status_excludes_deleted`
- Targeted command: `cargo xtask test-feature F068`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/persistence/seed.rs` tenants A and B with fixed UUIDv7 sequence and fixed clock `2026-09-03T00:00:00Z`; statement-shape assertions capture the built SQL from `QueryBuilder` without a connection; `trybuild` for the three compile-fail cases

## Exit criteria

- [ ] Tests written before implementation and observed failing, including the three `trybuild` expectations
- [ ] `UserRepository` consumed by `services/api/src/tenants/` for `GET /api/v1/users`, `POST /api/v1/users`, and `PATCH /api/v1/users/{id}`
- [ ] No SQLx type re-exported from `crates/persistence/src/lib.rs`; no `query`, `execute`, `raw`, `sql`, or `pool` public member
- [ ] Owned-path check passes; every file ≤ 500 lines; lint and format gates pass
- [ ] Handoff evidence recorded in S135
- [ ] `finished_at` recorded
