---
id: T017
type: task
status: planned
parent_epic: E002
parent_feature: F005
parent_story: S009
depends_on: [S009]
owned_paths: [services/api/migrations/*_workspaces_*.sql, crates/domain/src/workspaces/**, services/api/src/workspaces/**, testing/features/F005/database/**, testing/features/F005/api/**]
feature_flag: F005_FEATURE
branch: t017-workspace-migration-api
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4
- Capability contract: `docs/capability-contracts.md` row F005

# T017 — Workspace migration/API

## Identity

- Parent story: `S009` Create workspace
- Owner: platform
- Branch: `t017-workspace-migration-api`
- Decision references: `docs/architecture-decisions.md` sections 2–4; `docs/capability-contracts.md` row F005

## Objective

Create the `workspaces`, `workspace_members`, and `folders` schema with the cycle trigger and implement the workspace domain service and six workspace routes with authorization, idempotency, optimistic concurrency, audit, and outbox publication.

## Specification

- Owned paths: `services/api/migrations/<ts>_workspaces_create_tables.sql`, `services/api/migrations/<ts>_workspaces_create_tables.down.sql`, `crates/domain/src/workspaces/{mod.rs, schema.rs, workspace.rs, member.rs, errors.rs, service_workspace.rs}`, `services/api/src/workspaces/{mod.rs, routes.rs, handlers_workspace.rs, dto.rs}`
- Contract/input: DDL per F005 ticket section 4 PostgreSQL (three tables, tenant/UUIDv7/version/audit/soft-delete columns, `workspaces_tenant_name_idx`, `folders_sibling_name_idx`, depth check 1–10, `folders_check_cycle` trigger, path and position indexes); `CreateWorkspaceRequest { name, description? }`, `UpdateWorkspaceRequest { name?, description?, settings? }`, list query `{ cursor?, limit? ≤ 100, name_prefix?, deleted?, sort? }`; headers `Idempotency-Key`, `If-Match`.
- Output/behavior: `sqlx migrate run` applies on an empty database and on a database with F002/F003 tables, `sqlx migrate revert` drops the tables and trigger; routes `GET/POST /api/v1/workspaces`, `GET/PATCH/DELETE /api/v1/workspaces/{id}`, `POST /api/v1/workspaces/{id}/restore` return `WorkspaceResponse { id, name, description, settings, version, tree_version, my_role, created_at, updated_at, deleted_at }`; create inserts the creator as `owner`; list is restricted to member or tenant-admin workspaces; delete cascades `deleted_at` to folders and restore clears it; events `workspace.created.v1`, `workspace.updated.v1`, `workspace.deleted.v1`, `workspace.restored.v1` written to `outbox_events` in the same transaction; errors map per ticket section 4.
- Dependencies: F002 `users` and `groups` tables for member subjects; F003 `authz::require(actor, Permission::WorkspaceAdmin, workspace)` and audit writer; F004 outbox writer and tracing.
- Feature flag: `F005_FEATURE` gates router mounting; the migration runs regardless.
- Large-table note: no existing data; future columns must be additive and nullable.

## TDD

- Failing test first: `testing/features/F005/database/migration_tests.rs::workspace_tables_exist_with_constraints`, `::duplicate_workspace_name_rejected`, `::folder_depth_above_ten_rejected`, `::cycle_trigger_rejects_descendant_parent`, `::rollback_drops_tables`; `testing/features/F005/api/workspace_tests.rs::workspace_create_returns_version_one_and_owner`, `::workspace_duplicate_name_conflicts`, `::workspace_list_only_member_workspaces`, `::workspace_stale_version_conflicts`, `::workspace_restore_keeps_ids_and_folders`, `::workspace_cross_tenant_not_found`
- Targeted command: `cargo xtask test-feature F005`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: schema-per-worker database from `testing/harness/db.rs`; `testing/fixtures/workspaces.rs` tenants A and B, owner, admin, viewer, non-member; in-memory outbox recorder

## Exit criteria

- [ ] Tests written before the migration and service and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18
- [ ] Router mounted in `services/api/src/router.rs` behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S009
- [ ] `finished_at` recorded
