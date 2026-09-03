---
id: T005
type: task
status: planned
parent_epic: E001
parent_feature: F002
parent_story: S003
depends_on: [S003]
owned_paths: [services/api/migrations/*_tenants_*.sql, crates/domain/src/tenants/**, testing/features/F002/database/**]
feature_flag: F002_FEATURE
branch: t005-tenant-schema
started_at: null
finished_at: null
---

# T005 — Tenant schema

## Identity

- Parent story: `S003` Tenant lifecycle
- Owner: platform
- Branch: `t005-tenant-schema`

## Decision references

- Architecture: `docs/architecture-decisions.md` section 2
- Canonical contract: `docs/capability-contracts.md` row F002

## Objective

Create the `tenants`, `users`, `groups`, and `group_members` tables with the `citext` extension, unique indexes, check constraints, the same-tenant membership trigger, and a verified rollback.

## Specification

- Owned paths: `services/api/migrations/<ts>_tenants_create_tables.sql`, `services/api/migrations/<ts>_tenants_create_tables.down.sql`, `crates/domain/src/tenants/schema.rs` (typed column and index names)
- Contract/input: DDL per F002 ticket section 4 PostgreSQL: `create extension if not exists citext`; four tables with UUIDv7 ids, `tenant_id`, `version`, audit columns, `deleted_at`; check constraints on `plan`, `status`, and `region`; unique partial indexes `tenants_slug_idx`, `users_tenant_email_idx`, `groups_tenant_lower_name_idx`; `group_members` primary key `(group_id, user_id)` with `on delete cascade` from groups and `on delete restrict` from users; trigger `group_members_same_tenant` raising `tenant_mismatch`.
- Output/behavior: `sqlx migrate run` applies on an empty database; `sqlx migrate revert` drops the trigger, tables, and the extension; `cargo xtask check-migrations` passes; `schema.rs` constants are used by every query in S003 and S004 so column renames fail at compile time.
- Dependencies: F001 workspace and CI PostgreSQL 18 service; no prior tables.
- Feature flag: `F002_FEATURE` (migration runs regardless; routes are gated)
- Large-table note: `users` is designed for 1,000,000 rows; all later additions must be nullable or defaulted to avoid full rewrites.

## TDD

- Failing test first: `testing/features/F002/database/migration_tests.rs::tenants_tables_exist_with_constraints`, `::duplicate_slug_rejected`, `::duplicate_email_same_tenant_rejected_case_insensitive`, `::cross_tenant_group_member_rejected_by_trigger`, `::invalid_region_rejected_by_check`, `::rollback_drops_tables_and_extension`
- Targeted command: `cargo xtask test-feature F002`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: schema-per-worker database from `testing/harness/db.rs`; no external mocks

## Exit criteria

- [ ] Tests written before the migration and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S003
- [ ] `finished_at` recorded
