---
id: T213
type: task
status: planned
parent_epic: E008
parent_feature: F054
parent_story: S107
depends_on: [S107]
owned_paths: [services/api/migrations/*_bridge_*.sql, crates/domain/src/bridge/**, crates/persistence/src/bridge/**, services/api/src/bridge/**, testing/features/F054/database/**, testing/features/F054/api/**]
feature_flag: F054_FEATURE
branch: t213-connector-actions
started_at: null
finished_at: null
---

# T213 — Connector actions

## Identity

- Parent story: `S107` Cross-system workflows
- Owner: platform
- Branch: `t213-connector-actions`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 7, 10; `docs/capability-contracts.md` row F054

## Objective

Create the Bridge schema and the flow domain model with typed step kinds, graph validation, connector-action schema resolution, and the flow routes so a flow can be defined and published before the executor exists.

## Specification

- Owned paths: `services/api/migrations/<ts>_bridge_create_tables.sql`, `services/api/migrations/<ts>_bridge_create_tables.down.sql`, `crates/domain/src/bridge/{mod.rs, flow.rs, step.rs, graph.rs, actions.rs, errors.rs, service.rs, schema.rs}`, `crates/persistence/src/bridge/{mod.rs, flow_repository.rs, flow_step_repository.rs, version_repository.rs}`, `services/api/src/bridge/{mod.rs, routes.rs, handlers_flow.rs, dto.rs}`
- Data access: `BridgeFlowRepository` owns `bridge_flows`, `bridge_flow_steps`, the five per-kind config tables, `bridge_flow_step_mappings`, and `bridge_flow_step_branches`; `BridgeFlowVersionRepository` owns `bridge_flow_versions`. `flow.rs`, `step.rs`, `graph.rs`, `service.rs`, and the handlers hold no SQL: they call `find_flow_with_steps`, `replace_draft_steps`, `count_flows_for_tenant`, `count_steps_for_flow`, `find_flow_by_name`, and `insert_version`, and a create, patch, or publish writes the flow row, all step and child rows, the version row, the audit row, and the outbox row in one `UnitOfWork` with the deferred graph constraints checked at commit (decision section 2.1).
- Contract/input: DDL per F054 ticket section 4 (twelve tables, unique name per workspace, unique `(flow_id, step_id)` and `(flow_id, step_order)`, one `trigger` row per flow, per-kind config keyed `(flow_id, step_id)`, mapping primary key `(flow_id, step_id, target_field)`, branch primary key `(flow_id, step_id, branch_order)`, deferred self-referencing `next_step_id` and branch target foreign keys, unique `(flow_id, version)`, unique `(tenant_id, flow_id, idempotency_key)`, status and kind checks, indexes); `CreateFlowRequest { name, description?, steps[] }`, `UpdateFlowRequest { name?, description?, steps? }` with `If-Match` and `Idempotency-Key`; `StepConfig` variants per ticket; `actions.rs` defines `ActionRef` for `jira.create_issue`, `jira.transition_issue`, `salesforce.update_record`, `slack.post_message`, `box.upload_file`, `dropbox.upload_file`, `google_drive.create_file` and resolves input/output schemas from the F030 action registry.
- Output/behavior: routes `GET /api/v1/bridge/flows`, `POST /api/v1/bridge/flows`, `PATCH /api/v1/bridge/flows/{id}`, `POST /api/v1/bridge/flows/{id}/publish` return `FlowResponse { id, name, description, draft_steps, published_version, version, audit fields }` and `PublishResponse { version }`; `validate_graph` rejects missing or duplicate trigger, unreachable steps, cycles, `for_each` over 1,000, more than 50 steps, transform over 500 AST nodes; publish checks connection access through the F029 ACL and inserts `bridge_flow_versions` with the frozen `steps_snapshot`; router mounted behind `RequireModule(ModuleSlug::Bridge)`; `max_flows` and `max_steps_per_flow` enforced from the entitlement limits; audit rows `bridge.flow.create|update|publish`; errors per ticket section 4.
- Dependencies: F048 guard and limits; F030 action registry and connection ACL; F035 parser for AST-node counting; F003 audit writer.
- Feature flag: `F054_FEATURE` gates router mounting; migration runs regardless.
- Large-table note: no existing data; the draft graph is relational (`bridge_flow_steps` and its config, mapping, and branch children), and the only `jsonb` here is the immutable `bridge_flow_versions.steps_snapshot`, capped at 512 KB by validation and never queried by key.

## TDD

- Failing test first: `testing/features/F054/database/migration_tests.rs::bridge_tables_exist_with_constraints`, `::duplicate_flow_name_rejected`, `::run_idempotency_key_unique`, `::step_order_unique_per_flow`, `::second_trigger_step_row_rejected`, `::step_config_row_must_match_kind`, `::duplicate_mapping_target_field_rejected`, `::duplicate_branch_order_rejected`, `::next_step_id_foreign_key_enforced`, `::run_flow_version_pin_foreign_key_enforced`, `::step_count_limit_enforced`, `::rollback_drops_tables_children_first`; `testing/features/F054/api/flow_tests.rs::flow_create_requires_single_trigger`, `::flow_rejects_51_steps`, `::flow_publish_rejects_cycle`, `::flow_publish_denies_foreign_connection`, `::flow_publish_creates_immutable_version`, `::flow_limit_exceeded_conflicts`, `::bridge_route_denied_without_entitlement`
- Targeted command: `cargo xtask test-feature F054`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: schema-per-worker database from `testing/harness/db.rs`; `testing/fixtures/bridge.rs` entitlement and mocked connections; F030 action registry stub with fixed schemas

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; router mounted in `services/api/src/router.rs`; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S107
- [ ] `finished_at` recorded
