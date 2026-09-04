---
id: S108
type: story
status: planned
parent_epic: E008
parent_feature: F054
depends_on: [S107]
owned_paths: [crates/domain/src/bridge/**, crates/persistence/src/bridge/**, services/api/src/bridge/**, services/worker/src/bridge/**, apps/web/src/features/bridge/**, testing/features/F054/**]
feature_flag: F054_FEATURE
branch: s108-run-operations
started_at: null
finished_at: null
---

# S108 — Run operations

## Identity

- Parent feature: `F054` Bridge
- Owner: platform
- Branch: `s108-run-operations`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 6, 7, 9; `docs/capability-contracts.md` row F054

## Vertical slice

As a workflow editor, I want to build flows in a step builder, list and inspect runs in a console with a step timeline and redacted payloads, retry a failed step, and cancel a run, so that I can operate cross-system processes without reading worker logs.

## Requirements

- **SR-S108-01:** `GET /api/v1/bridge/runs` pages by cursor with `flow_id`, `status`, `from`, `to` filters through `BridgeRunRepository::list_runs_by_filters` and responds under 500 ms p95 with 100,000 runs; `GET /api/v1/bridge/runs/{id}` returns run, pinned `flow_version`, and the steps returned by `BridgeRunStepRepository::list_steps_for_run` ordered by `started_at` with redacted snapshots (covers FR-F054-11, NFR-F054-01).
- **SR-S108-02:** `POST /api/v1/bridge/runs/{id}/retry-step` re-executes a `failed` step from the input snapshot returned by `BridgeRunStepRepository::latest_attempt_for_step`, resumes downstream steps read from the pinned version snapshot, appends the new attempt row through the repository, and emits `bridge-run.step-completed.v1`; a non-failed step → `409 conflict` (FR-F054-10).
- **SR-S108-03:** Cancel through the F019 route marks pending Bridge steps `cancelled` with `BridgeRunStepRepository::mark_pending_steps_cancelled` and the run `cancelled` with `BridgeRunRepository::mark_run_status` in one `UnitOfWork`; a `workflow-viewer` calling retry or cancel → `403 denied`; foreign tenant → `404 not_found` (FR-F054-14).
- **SR-S108-04:** `FlowBuilderPage` renders the step canvas with typed forms for the six step kinds — reorder writes `step_order` and branch rows keep `branch_order`, both round-tripped through the unchanged `steps[]` JSON shape — publish and run-now dialogs, and loading, empty, error, denied, stale, offline, and not-entitled states (FR-F054-15, FR-F054-13).
- **SR-S108-05:** `RunConsolePage` shows filters, a keyboard-navigable step timeline with status text, a payload viewer showing `***` for redacted keys, `Retry step` on failed steps, `Cancel run` on active runs, and polls every 5 s while the run is active (FR-F054-15, NFR-F054-03).
- **SR-S108-06:** Failure suites prove dead-lettering after quota or timeout exhaustion, connection revoked between publish and run yielding a per-step `denied`, and snapshot truncation at 256 KB (NFR-F054-04, NFR-F054-02).
- **SR-S108-07:** Builder and console pass axe with zero serious violations and expose live status through a polite live region (NFR-F054-03).

## Surfaces

- Infrastructure/container: none new
- Data access: `crates/persistence/src/bridge/{run_repository.rs, run_step_repository.rs, version_repository.rs}` gain the named queries this slice needs — `list_runs_by_filters` (cursor, `flow_id`, `status`, `from`, `to`), `find_run_for_update`, `mark_run_status`, `list_steps_for_run`, `latest_attempt_for_step`, `append_step_attempt`, `mark_pending_steps_cancelled`, `load_version_snapshot`; `query.rs`, `retry.rs`, `cancel.rs`, the API handlers, the worker retry and cancel observer, and every test fixture call these traits and contain no SQL (decision section 2.1)
- Rust service/API: `crates/domain/src/bridge/{retry.rs, cancel.rs, query.rs}`; `services/api/src/bridge/{handlers_run.rs, handlers_retry.rs}`; `services/worker/src/bridge/{retry.rs, cancel_observer.rs}`
- Data/migration: none new; uses tables from S107
- React/UI: `apps/web/src/features/bridge/{BridgeListPage.tsx, FlowBuilderPage.tsx, StepCanvas.tsx, StepCard.tsx, StepForm.tsx, forms/TriggerForm.tsx, forms/ConnectorActionForm.tsx, forms/OpshubActionForm.tsx, forms/TransformForm.tsx, forms/WaitForm.tsx, forms/BranchForm.tsx, PublishDialog.tsx, RunNowDialog.tsx, RunConsolePage.tsx, RunList.tsx, RunFilters.tsx, StepTimeline.tsx, PayloadViewer.tsx, RetryStepButton.tsx, CancelRunDialog.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: seeded 5-step flow with 200 runs in mixed states including one failed Slack step; MSW handlers; Playwright against real API with scripted connector mocks; 100,000-run generator for the performance lane

## TDD harness

- Test path: `testing/features/F054/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F054_FEATURE`
- Targeted command: `cargo xtask test-feature F054`
- Full command: `cargo xtask test-all`
- First failing tests: `retry_step_resumes_downstream`, `retry_non_failed_step_conflicts`, `run_list_filters_by_status_and_flow`, `console_retry_button_only_on_failed_step`, `builder_rejects_second_trigger`, `run_list_100k_p95`

## Exit criteria

- [ ] Requirement tests SR-S108-01 through SR-S108-07 written first and failing
- [ ] Tasks T215 and T216 complete; UI wired to real API through generated client
- [ ] Unit, API, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `apps/web/src/features/bridge/RunConsolePage.tsx` mounted at `/w/:workspaceId/bridge/runs/:runId`; `FlowBuilderPage.tsx` at `/w/:workspaceId/bridge/:flowId`
- [ ] Handoff evidence recorded in the F054 ticket
