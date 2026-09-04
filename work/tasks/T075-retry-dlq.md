---
id: T075
type: task
status: planned
parent_epic: E004
parent_feature: F019
parent_story: S038
depends_on: [S038]
owned_paths: [crates/domain/src/workflow-runtime/**, crates/persistence/src/workflow-runtime/**, services/api/src/workflow-runtime/**, services/worker/src/workflow-runtime/**, testing/features/F019/api/**]
feature_flag: F019_FEATURE
branch: t075-retry-dlq
started_at: null
finished_at: null
---

# T075 — Retry/DLQ

## Identity

- Parent story: `S038` Retries/dead letters
- Owner: platform
- Branch: `t075-retry-dlq`
- Decision references: `docs/architecture-decisions.md` sections 3, 7; `docs/capability-contracts.md` row F019

## Objective

Implement exponential retry, timeouts, dead-letter transitions, the reaper, disable handling, and the retry and cancel control routes so every failure path is bounded and recoverable.

## Specification

- Owned paths: `crates/domain/src/workflow-runtime/{backoff.rs, transitions.rs, service_control.rs}`, `crates/persistence/src/workflow-runtime/workflow_run_repository.rs`, `services/worker/src/workflow-runtime/{retry.rs, timeout.rs, reaper.rs, disable_listener.rs}`, `services/api/src/workflow-runtime/handlers_control.rs`
- Contract/input: `backoff(attempt) = min(2^attempt * 5 s, 15 min) + jitter(0–20 %)` with attempts 1–5; step timeout 30 s, run timeout 120 s enforced with `tokio::time::timeout`; `POST /api/v1/workflow-runs/{id}/retry` and `POST /api/v1/workflow-runs/{id}/cancel` with `Idempotency-Key` and `If-Match`; `workflow.disabled.v1` and `workflow.updated.v1` (deleted) consumed by `disable_listener.rs`.
- Output/behavior: failed attempt sets `next_attempt_at` with the typed `error_code`, `error_message`, and `error_detail` provider snapshot, and uses JetStream delayed redelivery over `claim_due_retries`; fifth failure moves the run to `dead_lettered` through `transition_status`, emits `workflow-run.dead-lettered.v1`, keeps the run retryable for 30 days; timeout aborts with `error_code: timeout` and counts as an attempt; `transitions.rs` is the single state machine (`queued → running → completed|failed|cancelled`, `failed → running|dead_lettered`, `dead_lettered → queued` on retry) and rejects anything else with `InvalidTransition → 409 conflict`; retry re-queues from the first failed step with a fresh attempt series; cancel takes effect at the next step boundary; disable cancels running runs after the current step with `error_code: workflow_disabled`; reaper marks runs without heartbeat for 5 minutes as failed attempts with `error_code: heartbeat_lost`; the retry scan, dead-letter transition, and reaper are named repository queries, so `services/worker/src/workflow-runtime/` and `services/api/src/workflow-runtime/` hold no SQL string, `sqlx::query*` call, or connection; every transition emits its event and audit row with automation actor plus originating actor; metrics `workflow_run_total{status}`, `workflow_run_duration_ms`, `workflow_dead_letter_total`, `workflow_queue_depth{tenant}`.
- Dependencies: T074 routes, repositories, and idempotent executors; F004 metrics exporter; F018 `workflow.disabled.v1` event.
- Feature flag: `F019_FEATURE`

## TDD

- Failing test first: `testing/features/F019/api/retry_tests.rs::backoff_schedule_caps_at_fifteen_minutes`, `::fifth_failure_dead_letters_run`, `::step_timeout_counts_as_failed_attempt`, `::run_timeout_aborts_after_120s`, `::retry_dead_lettered_run_requeues_from_failed_step`, `::cancel_running_run_stops_at_step_boundary`, `::cancel_completed_run_conflicts`, `::disable_cancels_running_run_after_step`, `::reaper_fails_stale_heartbeat_run`, `::dead_letter_list_filters_by_error_code`, `::viewer_retry_denied`; unit `transitions_reject_invalid_edges`
- Targeted command: `cargo xtask test-feature F019`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: failing webhook executor with configurable failure count and latency; controllable clock; embedded JetStream

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Retry, timeout, reaper, and disable listener registered in `services/worker/src/main.rs` behind the flag
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S038
- [ ] `finished_at` recorded
