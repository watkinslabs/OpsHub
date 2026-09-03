---
id: T069
type: task
status: planned
parent_epic: E004
parent_feature: F018
parent_story: S035
depends_on: [S035]
owned_paths: [services/api/migrations/*_workflows_*.sql, crates/domain/src/workflows/**, testing/features/F018/database/**]
feature_flag: F018_FEATURE
branch: t069-workflow-schema
started_at: null
finished_at: null
---

# T069 — Workflow schema

## Identity

- Parent story: `S035` Trigger/condition
- Owner: platform
- Branch: `t069-workflow-schema`
- Decision references: `docs/architecture-decisions.md` section 2; `docs/capability-contracts.md` row F018

## Objective

Create the `workflows`, `workflow_versions`, and `workflow_steps` tables with the immutability trigger, constraints, indexes, and rollback, plus the typed Rust definition model that both the API and the runtime deserialize.

## Specification

- Owned paths: `services/api/migrations/<ts>_workflows_create_tables.sql`, `services/api/migrations/<ts>_workflows_create_tables.down.sql`, `crates/domain/src/workflows/{mod.rs, schema.rs, workflow.rs, trigger.rs, condition.rs, action.rs}`
- Contract/input: DDL per F018 ticket section 4 PostgreSQL: three tables with tenant/UUIDv7/version/audit/soft-delete columns on `workflows`; `state` check constraint; unique `(workflow_id, version_no)`; unique `(version_id, index)`; unique lower-cased name per sheet while not deleted; `workflow_versions_immutable` trigger raising `workflow_version_immutable` on `UPDATE`/`DELETE`; `published_version_id` foreign key. Rust: `WorkflowDefinition`, `Trigger`, `ConditionNode`, `ActionSpec`, `ActionKind` with `serde` tagged enums matching the JSON schema exported from `crates/contracts`.
- Output/behavior: `sqlx migrate run` applies on an empty database and on a database with F006/F007 tables; `sqlx migrate revert` drops the tables and trigger; `WorkflowDefinition` round-trips through JSON without loss and the definition hash (`sha256` of canonical JSON) is stable across serialization order.
- Dependencies: F006 `sheets` and F007 `columns` tables exist for foreign keys.
- Feature flag: `F018_FEATURE` (migration runs regardless; API routes are gated)
- Large-table note: no existing data; `draft` and `definition` are `jsonb` so future action kinds are additive.

## TDD

- Failing test first: `testing/features/F018/database/migration_tests.rs::workflow_tables_exist_with_constraints`, `::published_version_update_rejected`, `::duplicate_version_no_rejected`, `::duplicate_workflow_name_same_sheet_rejected`, `::rollback_drops_tables`; `crates/domain/src/workflows/schema.rs` unit `definition_hash_is_order_independent`
- Targeted command: `cargo xtask test-feature F018`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: schema-per-worker database from `testing/harness/db.rs`; no external mocks

## Exit criteria

- [ ] Tests written before the migration and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S035
- [ ] `finished_at` recorded
