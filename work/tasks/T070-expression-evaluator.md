---
id: T070
type: task
status: planned
parent_epic: E004
parent_feature: F018
parent_story: S035
depends_on: [T069]
owned_paths: [crates/domain/src/workflows/**, services/api/src/workflows/**, testing/features/F018/api/**, testing/features/F018/requirements/**]
feature_flag: F018_FEATURE
branch: t070-expression-evaluator
started_at: null
finished_at: null
---

# T070 — Expression evaluator

## Identity

- Parent story: `S035` Trigger/condition
- Owner: platform
- Branch: `t070-expression-evaluator`
- Decision references: `docs/architecture-decisions.md` sections 2–4; `docs/capability-contracts.md` row F018

## Objective

Implement trigger matching, condition-tree validation and evaluation, the workflow CRUD service, and the create/get/list/patch/test routes so a draft workflow can be defined and dry-run against a row.

## Specification

- Owned paths: `crates/domain/src/workflows/{evaluator.rs, validate.rs, errors.rs, service.rs}`, `services/api/src/workflows/{mod.rs, routes.rs, handlers_workflow.rs, handlers_test.rs, dto.rs}`
- Contract/input: `CreateWorkflowRequest { name, sheet_id, trigger, condition?, actions }`, `UpdateWorkflowRequest { name?, trigger?, condition?, actions? }`, `TestWorkflowRequest { row_id? , sample_event? }`, list query `{ cursor?, limit?, filter[sheet_id]?, filter[state]?, filter[trigger_kind]?, sort? }`; headers `Idempotency-Key`, `If-Match`.
- Output/behavior: routes `GET/POST /api/v1/workflows`, `GET/PATCH /api/v1/workflows/{id}`, `POST /api/v1/workflows/{id}/test` return `WorkflowResponse { id, sheet_id, name, state, draft, published_version: { id, version_no, published_at } | null, last_run_at, version, created_at, updated_at }` and `TestWorkflowResponse { trigger_matched, condition_result, action_plan }`; `validate_definition` checks operator/column-type pairs from F007 metadata, depth ≤ 4, leaves ≤ 200, cron ≥ 5 minutes, offsets within ±43,200; `evaluate_condition` short-circuits groups, evaluates `formula` leaves through F035 with a 2-second budget, and never executes actions; errors map per ticket section 4; event `workflow.updated.v1` and audit rows written in the same transaction.
- Dependencies: T069 schema and types; F003 `authz::require(actor, Permission::WorkflowEdit, workspace)`; F004 outbox writer; F007 column metadata reader; F035 `evaluate_expression`.
- Feature flag: `F018_FEATURE` gates router mounting.

## TDD

- Failing test first: `testing/features/F018/api/workflow_tests.rs::workflow_create_returns_draft_version_one`, `::trigger_cron_under_five_minutes_invalid`, `::condition_operator_type_mismatch_invalid`, `::condition_depth_five_invalid`, `::workflow_test_evaluates_without_side_effects`, `::workflow_list_filters_by_state_and_trigger`, `::workflow_cross_tenant_not_found`, `::workflow_viewer_mutation_denied`; unit `evaluator_all_any_short_circuit`, `evaluator_formula_budget_exceeded_invalid`
- Targeted command: `cargo xtask test-feature F018`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/workflows.rs` tenants A and B, typed sheet, editor, viewer; in-memory outbox recorder; real F035 evaluator

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Router mounted in `services/api/src/router.rs` behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S035
- [ ] `finished_at` recorded
