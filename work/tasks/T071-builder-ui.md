---
id: T071
type: task
status: planned
parent_epic: E004
parent_feature: F018
parent_story: S036
depends_on: [S036]
owned_paths: [crates/domain/src/workflows/**, crates/persistence/src/workflows/**, services/api/src/workflows/**, apps/web/src/features/workflows/**, testing/features/F018/api/**, testing/features/F018/frontend/**]
feature_flag: F018_FEATURE
branch: t071-builder-ui
started_at: null
finished_at: null
---

# T071 — Builder UI

## Identity

- Parent story: `S036` Actions
- Owner: platform
- Branch: `t071-builder-ui`
- Decision references: `docs/architecture-decisions.md` sections 3, 6; `docs/capability-contracts.md` row F018

## Objective

Implement action validation, placeholder resolution, the publish/disable/delete routes, and the React builder so an editor can author, test, and publish a complete workflow from the browser.

## Specification

- Owned paths: `crates/domain/src/workflows/{placeholders.rs, publish.rs, service_versions.rs}`, `crates/persistence/src/workflows/workflow_version_repository.rs`, `services/api/src/workflows/handlers_publish.rs`, `apps/web/src/features/workflows/{WorkflowListPage.tsx, WorkflowBuilderPage.tsx, TriggerStep.tsx, ConditionTree.tsx, ConditionLeafEditor.tsx, ActionList.tsx, ActionEditor.tsx, PlaceholderPicker.tsx, TestPanel.tsx, PublishDialog.tsx, DisableDialog.tsx, api.ts, hooks.ts, routes.ts}`
- Contract/input: routes `POST /api/v1/workflows/{id}/publish`, `POST /api/v1/workflows/{id}/disable`, `DELETE /api/v1/workflows/{id}` with `Idempotency-Key` and `If-Match`; generated `WorkflowsApi`; route params `workspaceId`, `sheetId`, `workflowId`; JSON schema for `WorkflowDefinition` from `crates/contracts`.
- Output/behavior: publish validates the full definition, then `WorkflowVersionRepository::publish(workflow_id, definition)` inserts `workflow_versions`, `workflow_steps`, and `workflow_step_column_refs` and repoints `workflows.published_version_id` in one `UnitOfWork`, enforces the 100-per-sheet and 5,000-per-tenant limits, and emits `workflow.published.v1`; `find_by_definition_hash(workflow_id, hash)` makes a republish of an unchanged definition idempotent; `list_workflows_using_column(column_id)` answers F007's column-delete guard; disable emits `workflow.disabled.v1`; delete calls `WorkflowRepository::soft_delete`. The handler and the domain publish path contain no SQL. UI: stepper with `TriggerStep`, `ConditionTree` (aria tree with `aria-level`), `ActionList` with `Alt+Arrow` reorder, `ActionEditor` per kind with `PlaceholderPicker`, `TestPanel` calling `testWorkflow`, `Publish` disabled until client validation passes; states loading, empty, error with correlation ID, denied read-only, not-found, stale banner, offline badge; telemetry `workflow_created`, `workflow_tested`, `workflow_published`, `workflow_disabled`, `workflow_action_added`.
- Dependencies: T070 routes and evaluator; F005 workspace shell; F006 sheet toolbar entry point.
- Feature flag: `F018_FEATURE` read through the flag hook; routes are not registered when off.

## TDD

- Failing test first: `testing/features/F018/api/publish_tests.rs::publish_writes_immutable_version`, `::patch_after_publish_keeps_version`, `::action_webhook_inline_secret_invalid`, `::placeholder_unknown_column_invalid`, `::sheet_limit_101_conflict`, `::publish_projects_column_refs_for_trigger_condition_and_actions`; `testing/features/F018/frontend/WorkflowBuilderPage.test.tsx::builder_publish_disabled_until_valid`, `::shows_denied_read_only_for_viewer`, `ConditionTree.test.tsx::nested_groups_expose_aria_level`, `ActionList.test.tsx::keyboard_reorder_updates_indexes`
- Targeted command: `cargo xtask test-feature F018`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: MSW handlers from the 6-workflow fixture; F029 vault stub returning fixed secret references

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Publish/disable/delete routes mounted; component lane passes
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S036
- [ ] `finished_at` recorded
