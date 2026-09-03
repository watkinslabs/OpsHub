---
id: S036
type: story
status: planned
parent_epic: E004
parent_feature: F018
depends_on: [S035]
owned_paths: [crates/domain/src/workflows/**, services/api/src/workflows/**, apps/web/src/features/workflows/**, testing/features/F018/**]
feature_flag: F018_FEATURE
branch: s036-actions
started_at: null
finished_at: null
---

# S036 — Actions

## Identity

- Parent feature: `F018` Workflow builder
- Owner: platform
- Branch: `s036-actions`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 6; `docs/capability-contracts.md` row F018

## Vertical slice

As a workflow editor, I want to add typed actions with placeholders, publish an immutable version, disable and re-enable a workflow, and do all of it in the builder UI, so that the runtime has a complete, validated definition to execute.

## Requirements

- **SR-S036-01:** The twelve action kinds (`update_fields`, `create_row`, `move_row`, `copy_row`, `assign`, `comment`, `request_approval`, `send_email`, `send_in_app`, `send_push`, `call_webhook`, `invoke_integration`) validate typed `params`; `call_webhook` rejects non-`https` URLs and inline secrets with `400 invalid` (FR-F018-04).
- **SR-S036-02:** `resolve_placeholders(template, row, event, actor)` substitutes `{{row.<column_id>}}`, `{{event.<field>}}`, `{{actor.<field>}}` using display values; unknown column IDs fail validation with the placeholder text in `field_errors.actions[i].params` (FR-F018-05).
- **SR-S036-03:** `POST /api/v1/workflows/{id}/publish` writes `workflow_versions` and `workflow_steps` in one transaction, sets `published_version_id`, emits `workflow.published.v1`; a later `PATCH` edits only `workflows.draft` (FR-F018-06, FR-F018-07).
- **SR-S036-04:** `POST /api/v1/workflows/{id}/disable` sets `state: disabled` and emits `workflow.disabled.v1`; `DELETE` soft deletes and leaves published versions readable by ID (FR-F018-08, FR-F018-11).
- **SR-S036-05:** Publishing the 101st workflow on a sheet or the 5,001st in a tenant returns `409 conflict` with `field_errors.limit` (FR-F018-12).
- **SR-S036-06:** `WorkflowBuilderPage` renders trigger, condition tree, and action list steps, mirrors server validation, runs the test panel, and shows loading, empty, error, denied, stale, and offline states; viewers see read-only (FR-F018-14, NFR-F018-03).
- **SR-S036-07:** Validation of a 25-action, depth-4 definition meets NFR-F018-01.

## Surfaces

- Infrastructure/container: none
- Rust service/API: `crates/domain/src/workflows/{action.rs, placeholders.rs, publish.rs, service_versions.rs}`; `services/api/src/workflows/{handlers_publish.rs}`
- Data/migration: none new; uses tables from S035
- React/UI: `apps/web/src/features/workflows/{WorkflowListPage.tsx, WorkflowBuilderPage.tsx, TriggerStep.tsx, ConditionTree.tsx, ConditionLeafEditor.tsx, ActionList.tsx, ActionEditor.tsx, PlaceholderPicker.tsx, TestPanel.tsx, PublishDialog.tsx, DisableDialog.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: 6 sample workflows; 5,000-workflow generator for the performance lane; MSW handlers for component tests; F029 vault stub for secret references

## TDD harness

- Test path: `testing/features/F018/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F018_FEATURE`
- Targeted command: `cargo xtask test-feature F018`
- Full command: `cargo xtask test-all`
- First failing tests: `action_webhook_inline_secret_invalid`, `placeholder_unknown_column_invalid`, `publish_writes_immutable_version`, `patch_after_publish_keeps_version`, `builder_publish_disabled_until_valid`, `validation_25_actions_p95`

## Exit criteria

- [ ] Requirement tests SR-S036-01 through SR-S036-07 written first and failing
- [ ] Tasks T071 and T072 complete; UI wired to real API through generated client
- [ ] Unit, API, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `apps/web/src/features/workflows/WorkflowBuilderPage.tsx` mounted at `/w/:workspaceId/sheets/:sheetId/workflows/:workflowId`
- [ ] Handoff evidence recorded in the F018 ticket
