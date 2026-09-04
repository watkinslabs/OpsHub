---
id: T189
type: task
status: planned
parent_epic: E006
parent_feature: F048
parent_story: S095
depends_on: [S095]
owned_paths: [services/api/migrations/*_entitlements_*.sql, crates/domain/src/entitlements/**, crates/persistence/src/entitlements/**, testing/features/F048/database/**]
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
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1; `docs/capability-contracts.md` row F048

## Objective

Create the `entitlements`, `entitlement_limits`, `modules`, `module_limit_keys`, `feature_flags`, `flag_rollout_transitions`, and `flag_overrides` tables with foreign keys, constraints, indexes, seed rows, and rollback, plus the typed `ModuleSlug`, the limit schemas the service validates against, and the `ModuleCatalogRepository` that is the only reader of the catalog tables.

## Specification

- Owned paths: `services/api/migrations/<ts>_entitlements_create_tables.sql`, `services/api/migrations/<ts>_entitlements_create_tables.down.sql`, `crates/domain/src/entitlements/{schema.rs, module.rs}`, `crates/persistence/src/entitlements/{mod.rs, module_catalog_repository.rs}`
- Contract/input: DDL per F048 ticket section 4 PostgreSQL, created parents first: platform-scoped `feature_flags` keyed by `key` with rollout-state, percent, cleanup-ticket-format and retired checks; `modules(slug, display_name, gate_flag_key unique references feature_flags(key) on delete restrict)`; `module_limit_keys(module references modules(slug) on delete cascade, limit_key, max_allowed, primary key (module, limit_key))`; `flag_rollout_transitions(from_state, to_state, primary key (from_state, to_state))` with both columns check-constrained to the six states; `entitlements` with `tenant_id references tenants(id) on delete cascade`, `module references modules(slug) on delete restrict`, the state/source checks, unique `(tenant_id, module)`, unique `(id, module)`, and the trial check; `entitlement_limits(entitlement_id, module, limit_key, limit_value, primary key (entitlement_id, limit_key), foreign key (entitlement_id, module) references entitlements(id, module) on delete cascade, foreign key (module, limit_key) references module_limit_keys(module, limit_key) on delete restrict)` replacing the former `entitlements.limits jsonb`; `flag_overrides` with `tenant_id references tenants(id) on delete cascade`, unique `(tenant_id, flag_key)`, `flag_key ... on delete cascade`, and the partial `expires_at` index. Seed rows: flags `F039_FEATURE`, `F040_FEATURE`, `F050_FEATURE` through `F057_FEATURE`, and `F048_FEATURE`, all `rollout_state = 'draft'`, `owner = 'platform'`, `default_enabled = false`; the ten `modules` rows with their gate flags per FR-F048-09; the `module_limit_keys` rows per module; the nine `flag_rollout_transitions` pairs. `module.rs` defines `ModuleSlug` with the ten slugs, `gate_flag()`, and `limit_schema()` (for example `data-shuttle`: `max_flows`, `max_rows_per_run`, `max_file_mb`; `bridge`: `max_flows`, `max_steps_per_flow`, `max_runs_per_day`; `workapps`: `max_apps`, `max_pages_per_app`; `dynamic-views`: `max_views`, `max_external_editors`; `calendar-app`: `max_calendars`, `max_sources_per_calendar`), each mirroring a seeded row.
- Output/behavior: `sqlx migrate run` applies on an empty database and on a database with F002/F003 tables; `sqlx migrate revert` drops the seven tables children first (`entitlement_limits`, `flag_overrides`, `entitlements`, `module_limit_keys`, `modules`, `flag_rollout_transitions`, `feature_flags`) with their seed rows; `cargo xtask check-migrations` and `check-flags` pass with the seed list matching the E008 feature IDs in `work/plan.md`.
- Data access: `crates/persistence/src/entitlements/module_catalog_repository.rs` is the only class that reads or writes `modules` and `module_limit_keys`, exposing `list_modules`, `find_module`, `list_limit_keys_for_module`, and `gate_flag_for_module`; `mod.rs` declares the four repository traits and wires them to the shared `Repository` and `UnitOfWork` contracts; `schema.rs` and `module.rs` hold no SQL, and the startup check that compares `ModuleSlug::limit_schema()` with the seeded rows calls `ModuleCatalogRepository` (decision section 2.1).
- Dependencies: F002 `tenants` and `users` tables for the `tenant_id` and actor foreign keys; F003 `audit_events` for later writes.
- Feature flag: `F048_FEATURE` (migration runs regardless; API routes are gated)
- Large-table note: `feature_flags`, `modules`, `module_limit_keys`, and `flag_rollout_transitions` are tiny and platform-wide; `entitlement_limits` is bounded by ten modules times a handful of keys per tenant; `flag_overrides` grows per tenant and is pruned nightly.

## TDD

- Failing test first: `testing/features/F048/database/migration_tests.rs::entitlement_tables_exist_with_constraints`, `::duplicate_entitlement_per_module_rejected`, `::trial_without_end_date_rejected`, `::retired_flag_requires_cleanup_ticket`, `::override_cascades_on_flag_delete`, `::limit_row_requires_declared_limit_key`, `::duplicate_limit_key_per_entitlement_rejected`, `::limit_rows_cascade_with_entitlement`, `::entitlement_module_must_exist_in_catalog`, `::module_gate_flag_is_unique`, `::seed_registry_matches_plan`, `::seed_catalog_matches_module_slug_enum`, `::rollback_drops_tables_children_first`
- Targeted command: `cargo xtask test-feature F048`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: schema-per-worker database from `testing/harness/db.rs`; constraint cases insert through `ModuleCatalogRepository` and `EntitlementRepository` and assert the rejections the database raises; no external mocks

## Exit criteria

- [ ] Tests written before the migration and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S095
- [ ] `finished_at` recorded
