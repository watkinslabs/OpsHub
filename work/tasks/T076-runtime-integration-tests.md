---
id: T076
type: task
status: planned
parent_epic: E004
parent_feature: F019
parent_story: S038
depends_on: [T075]
owned_paths: [apps/web/src/features/workflow-runtime/**, testing/features/F019/frontend/**, testing/features/F019/e2e/**, testing/features/F019/accessibility/**, testing/features/F019/performance/**]
feature_flag: F019_FEATURE
branch: t076-runtime-integration-tests
started_at: null
finished_at: null
---

# T076 — Runtime integration tests

## Identity

- Parent story: `S038` Retries/dead letters
- Owner: platform
- Branch: `t076-runtime-integration-tests`
- Decision references: `docs/architecture-decisions.md` sections 6, 9; `docs/capability-contracts.md` row F019

## Objective

Build the runs UI and the end-to-end, accessibility, and performance lanes that prove a row edit becomes a completed run, a failing run can be retried from the browser, and the runtime meets its latency targets.

## Specification

- Owned paths: `apps/web/src/features/workflow-runtime/{RunListPage.tsx, RunTable.tsx, RunStatusBadge.tsx, RunDetailPage.tsx, StepTimeline.tsx, StepErrorPanel.tsx, RetryRunDialog.tsx, CancelRunDialog.tsx, InboundWebhookCard.tsx, api.ts, hooks.ts, routes.ts}`, `testing/features/F019/e2e/runs.spec.ts`, `testing/features/F019/accessibility/runs.a11y.spec.ts`, `testing/features/F019/performance/{start_latency_bench.rs, run_list_bench.rs, scheduler_bench.rs}`
- Contract/input: generated `WorkflowRuntimeApi` returning `trigger_kind`, `trigger`, `error_code`, and `error_message` per run and `output`, `error_code`, `error_message`, `error_detail` per step; route params `workspaceId`, `sheetId`, `workflowId`, `runId`; query keys `['workflow-runs', ...]`, `['workflow-run', runId]` with `refetchInterval: 5000` while active and visible.
- Output/behavior: list with status and failure-class (`error_code`) filter chips, text-plus-icon badges, card layout under 768 px; detail with `StepTimeline`, `StepErrorPanel` rendering the step's `error_code` label, `error_message`, and `error_detail` provider snapshot, retry and cancel dialogs (editors only), optimistic retry rolled back on `conflict`; states loading, empty, error with correlation ID, denied read-only, not-found, offline; keyboard `R`/`C`/`Enter`/`Escape`; telemetry `run_list_opened`, `run_detail_opened`, `run_retried`, `run_cancelled`, `webhook_token_rotated`. Playwright drives the real API and worker; benches assert start latency p95 < 2 s at 1,000 events per minute, list p95 < 500 ms over 1,000,000 runs, 10,000 due triggers per tick < 30 s.
- Dependencies: T075 control routes and repository-backed run queries (the E2E and performance lanes drive the API and the repository traits against an isolated tenant fixture and contain no SQL); F018 builder for the workflow entry point; `testing/harness/` Playwright, axe, and criterion runners.
- Feature flag: `F019_FEATURE` read through the flag hook; routes are not registered when off.

## TDD

- Failing test first: `testing/features/F019/frontend/RunTable.test.tsx::renders_status_badges_with_text_and_icon`, `RunDetailPage.test.tsx::run_detail_retry_rolls_back_on_conflict`, `::viewer_hides_retry_and_cancel`, `::step_error_panel_renders_error_code_and_message`; `testing/features/F019/e2e/runs.spec.ts::row_edit_triggers_completed_run`, `::failed_run_retry_from_browser`, `::cancel_running_run`, `::viewer_read_only_runs`; `testing/features/F019/accessibility/runs.a11y.spec.ts::runs_have_no_serious_axe_violations`; `testing/features/F019/performance/start_latency_bench.rs::run_start_latency_p95`, `run_list_bench.rs::run_list_1m_p95`
- Targeted command: `cargo xtask test-feature F019`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: MSW handlers from the run fixture; Playwright against seeded tenant with worker running; 1,000,000-run generator with fixed seed `0x0F19`

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Component, E2E, accessibility, and performance lanes pass with evidence under `testing/evidence/F019/`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S038
- [ ] `finished_at` recorded
