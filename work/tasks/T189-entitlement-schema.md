---
id: T189
type: task
status: planned
parent_epic: E008
parent_feature: F048
parent_story: S095
depends_on: [S095]
owned_paths: [services/api/migrations/*_entitlements_*.sql, crates/domain/src/entitlements/**, testing/features/F048/database/**]
feature_flag: F048_FEATURE
branch: t189-entitlement-schema
started_at: null
finished_at: null
---

# T189 — Entitlement schema

## Identity

- Parent story: `S095` Entitlement records
- Owner: platform
- Branch: `t189-entitlement-schema`
- Decision references: `docs/architecture-decisions.md` section 2; `docs/capability-contracts.md` row F048

## Objective

Create the `entitlements`, `feature_flags`, and `flag_overrides` tables with constraints, indexes, seed rows, and rollback, plus the typed `ModuleSlug` and limit schemas the service validates against.

## Specification

- Owned paths: `services/api/migrations/<ts>_entitlements_create_tables.sql`, `services/api/migrations/<ts>_entitlements_create_tables.down.sql`, `crates/domain/src/entitlements/{schema.rs, module.rs}`
- Contract/input: DDL per F048 ticket section 4 PostgreSQL: `entitlements` with unique `(tenant_id, module)` and trial check; platform-scoped `feature_flags` keyed by `key` with rollout-state and percent checks and the retired check; `flag_overrides` with unique `(tenant_id, flag_key)`, `on delete cascade`, and the partial `expires_at` index. Seed rows: `F039_FEATURE`, `F040_FEATURE`, `F050_FEATURE` through `F057_FEATURE`, and `F048_FEATURE`, all `rollout_state = 'draft'`, `owner = 'platform'`, `default_enabled = false`. `module.rs` defines `ModuleSlug` with the ten slugs, `gate_flag()`, and `limit_schema()` (for example `data-shuttle`: `max_flows`, `max_rows_per_run`, `max_file_mb`; `bridge`: `max_flows`, `max_steps_per_flow`, `max_runs_per_day`; `workapps`: `max_apps`, `max_pages_per_app`; `dynamic-views`: `max_views`, `max_external_editors`; `calendar-app`: `max_calendars`, `max_sources_per_calendar`).
- Output/behavior: `sqlx migrate run` applies on an empty database and on a database with F002/F003 tables; `sqlx migrate revert` drops the three tables and the seed rows; `cargo xtask check-migrations` and `check-flags` pass with the seed list matching the E008 feature IDs in `work/plan.md`.
- Dependencies: F002 `tenants` table for the `tenant_id` foreign key; F003 `audit_events` for later writes.
- Feature flag: `F048_FEATURE` (migration runs regardless; API routes are gated)
- Large-table note: `feature_flags` is tiny and platform-wide; `flag_overrides` grows per tenant and is pruned nightly.

## TDD

- Failing test first: `testing/features/F048/database/migration_tests.rs::entitlement_tables_exist_with_constraints`, `::duplicate_entitlement_per_module_rejected`, `::trial_without_end_date_rejected`, `::retired_flag_requires_cleanup_ticket`, `::override_cascades_on_flag_delete`, `::seed_registry_matches_plan`, `::rollback_drops_tables`
- Targeted command: `cargo xtask test-feature F048`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: schema-per-worker database from `testing/harness/db.rs`; no external mocks

## Exit criteria

- [ ] Tests written before the migration and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S095
- [ ] `finished_at` recorded
