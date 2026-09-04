---
id: S038
type: story
status: planned
parent_epic: E004
parent_feature: F019
depends_on: [S037]
owned_paths: [crates/domain/src/workflow-runtime/**, crates/persistence/src/workflow-runtime/**, services/api/src/workflow-runtime/**, services/worker/src/workflow-runtime/**, apps/web/src/features/workflow-runtime/**, testing/features/F019/**]
feature_flag: F019_FEATURE
branch: s038-retries-dead-letters
started_at: null
finished_at: null
---

# S038 — Retries/dead letters

## Identity

- Parent feature: `F019` Workflow runtime
- Owner: platform
- Branch: `s038-retries-dead-letters`
- Decision references: `docs/architecture-decisions.md` sections 3, 6, 7; `docs/capability-contracts.md` row F019

## Vertical slice

As a workflow editor, I want failed steps to retry with exponential backoff, time out predictably, land in a dead-letter state I can retry or cancel from the runs UI, and stop cleanly when a workflow is disabled, so that failures are recoverable and never silent.

## Requirements

- **SR-S038-01:** A failed step schedules the next attempt at `min(2^attempt * 5 s, 15 min)` plus 0–20 % jitter through JetStream delayed redelivery, with the retry scan reading `WorkflowRunRepository::claim_due_retries`; after attempt 5 `transition_status` moves the run to `dead_lettered` and emits `workflow-run.dead-lettered.v1` in the same `UnitOfWork` (FR-F019-06).
- **SR-S038-02:** A step exceeding 30 seconds or a run exceeding 120 seconds is aborted with `error_code: timeout` and `error_message` naming the elapsed budget, and counted as a failed attempt (FR-F019-07).
- **SR-S038-03:** `POST /api/v1/workflow-runs/{id}/retry` re-queues a `failed` or `dead_lettered` run from the first failed step with the same pinned version; `POST /api/v1/workflow-runs/{id}/cancel` cancels `queued` or `running` runs at the next step boundary; other states return `409 conflict` (FR-F019-12).
- **SR-S038-04:** `workflow.disabled.v1` and workflow deletion stop new runs and cancel running ones after the current step with `error_code: workflow_disabled`; history stays readable (FR-F019-13).
- **SR-S038-05:** Every transition emits its `workflow-run.*.v1` event and an audit row naming the automation actor and the originating human actor; a reaper marks runs without a heartbeat for 5 minutes as failed attempts with `error_code: heartbeat_lost`; the reaper, retry scan, and dead-letter transition are named repository queries and hold no SQL (FR-F019-14, NFR-F019-04).
- **SR-S038-06:** `RunListPage` and `RunDetailPage` render status badges with text and icon, a failure-class filter over `error_code`, the step timeline showing each step's `error_code`, `error_message`, and provider `error_detail` snapshot, retry and cancel dialogs for editors, read-only for viewers, and loading, empty, error, denied, stale, and offline states (FR-F019-14, NFR-F019-03).
- **SR-S038-07:** Run start latency under 1,000 events per minute and `page_runs` over 1,000,000 runs, including the `error_code` failure-class filter, meet NFR-F019-01.

## Surfaces

- Infrastructure/container: none beyond S037 stream declarations
- Rust service/API: `crates/domain/src/workflow-runtime/{backoff.rs, transitions.rs, service_control.rs}` (repository traits only, no SQL); `crates/persistence/src/workflow-runtime/{mod.rs, workflow_run_repository.rs}` for `claim_due_retries` and `transition_status`; `services/worker/src/workflow-runtime/{retry.rs, timeout.rs, reaper.rs, disable_listener.rs}`; `services/api/src/workflow-runtime/handlers_control.rs`
- Data/migration: none new; uses the tables, typed `error_code` columns, and `workflow_runs(tenant_id, error_code)` index from S037
- React/UI: `apps/web/src/features/workflow-runtime/{RunListPage.tsx, RunTable.tsx, RunStatusBadge.tsx, RunDetailPage.tsx, StepTimeline.tsx, StepErrorPanel.tsx, RetryRunDialog.tsx, CancelRunDialog.tsx, InboundWebhookCard.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: failing webhook executor with configurable failure count; controllable clock; 1,000,000-run generator for the performance lane; MSW handlers for component tests

## TDD harness

- Test path: `testing/features/F019/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F019_FEATURE`
- Targeted command: `cargo xtask test-feature F019`
- Full command: `cargo xtask test-all`
- First failing tests: `backoff_schedule_caps_at_fifteen_minutes`, `fifth_failure_dead_letters_run`, `step_timeout_counts_as_failed_attempt`, `retry_dead_lettered_run_requeues_from_failed_step`, `cancel_completed_run_conflicts`, `run_detail_retry_rolls_back_on_conflict`, `run_start_latency_p95`

## Exit criteria

- [ ] Requirement tests SR-S038-01 through SR-S038-07 written first and failing
- [ ] Tasks T075 and T076 complete; UI wired to real API through generated client
- [ ] Unit, API, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `apps/web/src/features/workflow-runtime/RunListPage.tsx` mounted at `/w/:workspaceId/automation/runs`; `services/worker/src/workflow-runtime/retry.rs` registered in `services/worker/src/main.rs`
- [ ] Handoff evidence recorded in the F019 ticket
