---
id: S035
type: story
status: planned
parent_epic: E004
parent_feature: F018
depends_on: [F007, F035]
owned_paths: [crates/domain/src/workflows/**, services/api/src/workflows/**, services/api/migrations/*_workflows_*.sql, testing/features/F018/**]
feature_flag: F018_FEATURE
branch: s035-trigger-condition
started_at: null
finished_at: null
---

# S035 — Trigger/condition

## Identity

- Parent feature: `F018` Workflow builder
- Owner: platform
- Branch: `s035-trigger-condition`
- Decision references: `docs/architecture-decisions.md` sections 2–4; `docs/capability-contracts.md` row F018

## Vertical slice

As a workflow editor, I want to create a workflow with a typed trigger and a condition tree, validate it, and evaluate it against a sample row through the test endpoint, so that the definition that will later run is proven correct before any action exists.

## Requirements

- **SR-S035-01:** `POST /api/v1/workflows` with `{ name, sheet_id, trigger, condition?, actions }` writes `workflows` with `state: draft` and returns `WorkflowResponse` with version 1 (covers FR-F018-01).
- **SR-S035-02:** The eight trigger kinds parse into the `Trigger` enum with their required parameters; cron intervals under 5 minutes, unknown kinds, and `date_reached` offsets outside ±43,200 minutes return `400 invalid` with `field_errors.trigger.*` (FR-F018-02).
- **SR-S035-03:** `ConditionNode` trees up to depth 4 with `compare`, `changed`, `actor_in`, `exists`, and `formula` leaves validate operators against F007 column types; depth 5 or an operator/type mismatch returns `400 invalid` with the leaf path (FR-F018-03).
- **SR-S035-04:** `evaluate_condition(definition, event, row, actor)` returns a deterministic boolean and short-circuits `all`/`any` groups; formula leaves use F035 with the 2-second budget (FR-F018-03, FR-F018-09).
- **SR-S035-05:** `POST /api/v1/workflows/{id}/test` with `{ row_id }` returns `{ trigger_matched, condition_result, action_plan }` without executing actions (FR-F018-09).
- **SR-S035-06:** `GET /api/v1/workflows` and `GET /api/v1/workflows/{id}` page and filter by `sheet_id`, `state`, `trigger_kind` (FR-F018-10).
- **SR-S035-07:** Every mutation checks `Idempotency-Key`, writes an audit event, and enqueues `workflow.updated.v1`; a foreign-tenant actor receives `404 not_found` (FR-F018-13, NFR-F018-02).

## Surfaces

- Infrastructure/container: none beyond F004 baseline
- Rust service/API: `crates/domain/src/workflows/{workflow.rs, trigger.rs, condition.rs, evaluator.rs, errors.rs, service.rs}`; `services/api/src/workflows/{routes.rs, handlers_workflow.rs, handlers_test.rs, dto.rs}`
- Data/migration: `services/api/migrations/<ts>_workflows_create_tables.sql` creating `workflows`, `workflow_versions`, `workflow_steps` with indexes and the immutability trigger from ticket section 4
- React/UI: none in this story (S036 and T071 cover UI)
- Mocks/fixtures: `testing/fixtures/workflows.rs` tenant, sheet with typed columns, editor, viewer, foreign tenant; in-memory outbox recorder; F035 evaluator real

## TDD harness

- Test path: `testing/features/F018/api/`, `testing/features/F018/database/`, `testing/features/F018/requirements/`
- Feature flag: `F018_FEATURE`
- Targeted command: `cargo xtask test-feature F018`
- Full command: `cargo xtask test-all`
- First failing tests: `workflow_create_returns_draft_version_one`, `trigger_cron_under_five_minutes_invalid`, `condition_operator_type_mismatch_invalid`, `condition_depth_five_invalid`, `workflow_test_evaluates_without_side_effects`, `workflow_cross_tenant_not_found`

## Exit criteria

- [ ] Requirement tests SR-S035-01 through SR-S035-07 written first and failing
- [ ] Tasks T069 and T070 complete and wired through `services/api` router
- [ ] Unit, API, database, permission tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/workflows/routes.rs` mounted in `services/api/src/router.rs`
- [ ] Handoff evidence recorded in the F018 ticket
