---
id: T214
type: task
status: planned
parent_epic: E008
parent_feature: F054
parent_story: S107
depends_on: [T213]
owned_paths: [crates/domain/src/bridge/**, services/api/src/bridge/**, services/worker/src/bridge/**, testing/features/F054/api/**, testing/features/F054/requirements/**, testing/features/F054/performance/**]
feature_flag: F054_FEATURE
branch: t214-multi-step-runtime
started_at: null
finished_at: null
---

# T214 — Multi-step runtime

## Identity

- Parent story: `S107` Cross-system workflows
- Owner: platform
- Branch: `t214-multi-step-runtime`
- Decision references: `docs/architecture-decisions.md` sections 3, 4, 7, 9; `docs/capability-contracts.md` row F054

## Objective

Implement run enqueue and the worker executor that runs published flow versions step by step on the F019 runtime with timeouts, backoff retries, waits, branches, redaction, events, and audit.

## Specification

- Owned paths: `crates/domain/src/bridge/{run.rs, redact.rs, branch.rs, service_runs.rs}`, `services/api/src/bridge/handlers_run.rs`, `services/worker/src/bridge/{mod.rs, executor.rs, step_runner.rs, connector_step.rs, opshub_step.rs, transform_step.rs, wait_step.rs, resume.rs}`
- Contract/input: `POST /api/v1/bridge/flows/{id}/run` with `RunFlowRequest { input (≤ 256 KB), idempotency_key }`; JetStream subject `workflow-run.bridge` carrying `{ tenant_id, run_id, flow_id, flow_version, correlation_id }`; resume messages from the F004 scheduler (`wait.delay`) and `approval.decided.v1` (`wait.approval`); F030 `ActionInvoker::invoke(connection_id, action, input) -> Result<Value, ConnectorError>`.
- Output/behavior: enqueue inserts `bridge_runs` (`queued`) and the outbox event `bridge-run.started.v1` when the executor picks it up; idempotent by `(tenant_id, flow_id, idempotency_key)`; `429 rate_limited` above `max_runs_per_day`; executor pins `flow_version`, runs steps sequentially, per-step timeout 5–300 s (default 60), retries `unavailable`/`rate_limited` at 1 s, 4 s, 16 s then marks step and run `failed` with `bridge-run.failed.v1`; every attempt writes a `bridge_run_steps` row with redacted `input_snapshot`/`output_snapshot` (keys matching `authorization|token|secret|password` → `***`, payload truncated at 256 KB with `truncated: true`); `bridge-run.step-completed.v1` per successful step, `bridge-run.completed.v1` at the end; `branch` evaluates typed conditions in order and follows `otherwise`; `for_each` runs the sub-mapping over ≤ 1,000 items; `wait` sets `waiting`, releases the slot, and resumes; connection access re-checked per step; per-tenant quota and dead-letter behavior inherited from the F019 consumer middleware.
- Dependencies: T213 flow model and versions; F019 queue, quota, idempotency, and dead-letter middleware; F030 `ActionInvoker`; F018 action executor; F020 approvals; F035 restricted evaluator; F004 scheduler.
- Feature flag: `F054_FEATURE` gates the run route and the worker consumer registration.

## TDD

- Failing test first: `testing/features/F054/api/run_tests.rs::run_enqueue_is_idempotent_by_key`, `::run_unpublished_flow_conflicts`, `::run_quota_exceeded_rate_limited`, `::executor_runs_five_steps_in_order`, `::executor_retries_rate_limited_then_fails_step`, `::executor_redacts_secrets_in_snapshots`, `::executor_truncates_large_snapshot`, `::branch_follows_matching_condition`, `::for_each_rejects_over_1000_items`, `::wait_approval_resumes_on_decision`, `::step_rechecks_connection_access`; `testing/features/F054/performance/run_bench.rs::enqueue_ack_p95_under_2s`, `::ten_step_run_under_30s`
- Targeted command: `cargo xtask test-feature F054`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: scripted `ActionInvoker` mock (responses by call index, including `rate_limited` twice then success); in-process F019 queue; fixed clock advanced by the test for timeouts and delays; approval decision helper

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Executor registered in `services/worker/src/main.rs`; run route mounted; events verified in the outbox
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S107
- [ ] `finished_at` recorded
