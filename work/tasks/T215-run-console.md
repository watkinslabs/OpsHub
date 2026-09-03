---
id: T215
type: task
status: planned
parent_epic: E008
parent_feature: F054
parent_story: S108
depends_on: [S108]
owned_paths: [crates/domain/src/bridge/**, services/api/src/bridge/**, services/worker/src/bridge/**, apps/web/src/features/bridge/**, testing/features/F054/api/**, testing/features/F054/frontend/**]
feature_flag: F054_FEATURE
branch: t215-run-console
started_at: null
finished_at: null
---

# T215 — Run console

## Identity

- Parent story: `S108` Run operations
- Owner: platform
- Branch: `t215-run-console`
- Decision references: `docs/architecture-decisions.md` sections 3, 4, 6; `docs/capability-contracts.md` row F054

## Objective

Implement run listing, run detail, per-step retry, and cancellation on the backend, and the flow builder and run console pages wired to the real Bridge API.

## Specification

- Owned paths: `crates/domain/src/bridge/{retry.rs, cancel.rs, query.rs}`, `services/api/src/bridge/{handlers_run.rs, handlers_retry.rs}`, `services/worker/src/bridge/{retry.rs, cancel_observer.rs}`, `apps/web/src/features/bridge/{BridgeListPage.tsx, FlowBuilderPage.tsx, StepCanvas.tsx, StepCard.tsx, StepForm.tsx, forms/TriggerForm.tsx, forms/ConnectorActionForm.tsx, forms/OpshubActionForm.tsx, forms/TransformForm.tsx, forms/WaitForm.tsx, forms/BranchForm.tsx, PublishDialog.tsx, RunNowDialog.tsx, RunConsolePage.tsx, RunList.tsx, RunFilters.tsx, StepTimeline.tsx, PayloadViewer.tsx, RetryStepButton.tsx, CancelRunDialog.tsx, api.ts, hooks.ts, routes.ts}`
- Contract/input: `GET /api/v1/bridge/runs` query `{ cursor?, limit? (≤ 100), flow_id?, status?, from?, to? }`; `GET /api/v1/bridge/runs/{id}`; `POST /api/v1/bridge/runs/{id}/retry-step` with `RetryStepRequest { step_id }`, `Idempotency-Key`, `If-Match`; cancel through the F019 route `POST /api/v1/workflow-runs/{id}/cancel`; generated `BridgeApi` client; route params `workspaceId`, `flowId`, `runId`.
- Output/behavior: list returns `Page<RunResponse>` ordered by `created_at desc` using the `(tenant_id, status, created_at)` index; detail returns run, pinned version, ordered steps with redacted snapshots; retry re-executes a `failed` step from its `input_snapshot`, resumes downstream, emits `bridge-run.step-completed.v1`, writes audit `bridge.run.retry-step`; non-failed step → `409 conflict`; viewer → `403 denied`; foreign tenant → `404`; `cancel_observer` marks pending steps `cancelled`; builder renders step canvas and typed forms with publish and run-now dialogs; console renders filters, step timeline, payload viewer with `***` markers, `Retry step` on failed steps, `Cancel run` on active runs, polling every 5 s while active; states: loading skeleton, empty, error banner with correlation ID, denied affordances for viewers, not-found page, stale banner, offline badge, `ModuleNotEntitled` via `useModuleAllowed('bridge')`; telemetry `bridge_flow_created`, `bridge_flow_published`, `bridge_run_started`, `bridge_step_retried`, `bridge_run_cancelled`, `bridge_console_opened`.
- Dependencies: T214 executor and events; F048 hooks from `apps/web/src/features/entitlements`; F005 workspace shell navigation entry.
- Feature flag: `F054_FEATURE` read through the flag hook; routes are not registered when off.

## TDD

- Failing test first: `testing/features/F054/api/retry_tests.rs::retry_step_resumes_downstream`, `::retry_non_failed_step_conflicts`, `::retry_viewer_denied`, `::run_list_filters_by_status_and_flow`, `::run_cross_tenant_not_found`, `::cancel_marks_pending_steps_cancelled`; `testing/features/F054/frontend/FlowBuilderPage.test.tsx::builder_rejects_second_trigger`, `::connector_form_lists_owner_connections`; `RunConsolePage.test.tsx::console_retry_button_only_on_failed_step`, `::payload_viewer_shows_redaction_markers`, `::polls_while_run_active`, `::shows_not_entitled_panel`
- Targeted command: `cargo xtask test-feature F054`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: seeded flow with 200 runs including a failed Slack step; MSW handlers from the fixture; role-switching session helper

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] API and component lanes pass; console and builder mounted on their routes
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S108
- [ ] `finished_at` recorded
