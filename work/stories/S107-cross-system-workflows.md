---
id: S107
type: story
status: planned
parent_epic: E008
parent_feature: F054
depends_on: [F019, F030, F048]
owned_paths: [crates/domain/src/bridge/**, services/api/src/bridge/**, services/worker/src/bridge/**, services/api/migrations/*_bridge_*.sql, testing/features/F054/**]
feature_flag: F054_FEATURE
branch: s107-cross-system-workflows
started_at: null
finished_at: null
---

# S107 — Cross-system workflows

## Identity

- Parent feature: `F054` Bridge
- Owner: platform
- Branch: `s107-cross-system-workflows`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 7, 10; `docs/capability-contracts.md` row F054

## Vertical slice

As a workflow editor, I want to define, validate, publish, and run a multi-step flow whose steps call F030 connector actions, OpsHub actions, transforms, waits, and branches on the F019 runtime, so that a cross-system process executes with idempotency, retries, redaction, and audit before any console UI exists.

## Requirements

- **SR-S107-01:** `POST /api/v1/bridge/flows` and `PATCH /api/v1/bridge/flows/{id}` accept 1–50 typed steps with a single leading trigger; 51 steps or an unknown step kind → `400 invalid` with `field_errors.steps` (covers FR-F054-01, FR-F054-02).
- **SR-S107-02:** `connector_action` steps resolve an F030 action schema and a connection the owner may use at publish time; a foreign or revoked connection → `403 denied` with `field_errors.steps[i].config.connection_id` (FR-F054-03).
- **SR-S107-03:** `POST /api/v1/bridge/flows/{id}/publish` runs `validate_graph` (cycle, reachability, `for_each` ≤ 1,000, transform ≤ 500 AST nodes) and writes an immutable `bridge_flow_versions` row; a cycle → `409 conflict` `field_errors.steps = "cycle"` (FR-F054-04, FR-F054-05).
- **SR-S107-04:** `POST /api/v1/bridge/flows/{id}/run` returns `202` with `run_id` within 2 seconds, is idempotent by key, refuses unpublished flows with `409`, and enforces `max_runs_per_day` with `429 rate_limited` (FR-F054-06, NFR-F054-01).
- **SR-S107-05:** `BridgeExecutor` in `services/worker/src/bridge/` executes steps sequentially with per-step timeout ≤ 300 s, backoff 1 s/4 s/16 s for `unavailable`/`rate_limited`, writes one `bridge_run_steps` row per attempt, and redacts secrets in snapshots (FR-F054-07, FR-F054-08, NFR-F054-02).
- **SR-S107-06:** `wait` steps with `delay` or `approval` park the run in `waiting`, release the worker slot, and resume from the F004 scheduler or `approval.decided.v1` (FR-F054-09).
- **SR-S107-07:** Run transitions publish `bridge-run.started.v1`, `bridge-run.step-completed.v1`, `bridge-run.completed.v1`, `bridge-run.failed.v1` through the outbox and write audit rows; the router is gated by `RequireModule(ModuleSlug::Bridge)` and entitlement limits `max_flows`, `max_steps_per_flow` (FR-F054-12, FR-F054-13).

## Surfaces

- Infrastructure/container: JetStream subject `workflow-run.bridge` on the F019 stream; scheduler entries for `wait.delay` resumes
- Rust service/API: `crates/domain/src/bridge/{mod.rs, flow.rs, step.rs, graph.rs, run.rs, redact.rs, errors.rs, service.rs}`; `services/api/src/bridge/{mod.rs, routes.rs, handlers_flow.rs, handlers_run.rs, dto.rs}`; `services/worker/src/bridge/{mod.rs, executor.rs, step_runner.rs, connector_step.rs, wait_step.rs, resume.rs}`
- Data/migration: `services/api/migrations/<ts>_bridge_create_tables.sql` creating `bridge_flows`, `bridge_flow_versions`, `bridge_runs`, `bridge_run_steps` with indexes from ticket section 4
- React/UI: none in this story (S108 covers builder and console)
- Mocks/fixtures: `testing/fixtures/bridge.rs` tenants A/B, editor, viewer, entitlement with limits, scripted `ActionInvoker` mock for `jira`, `slack`, `salesforce`; in-memory outbox; in-process F019 queue; approval decision helper

## TDD harness

- Test path: `testing/features/F054/api/`, `testing/features/F054/database/`, `testing/features/F054/performance/`
- Feature flag: `F054_FEATURE`
- Targeted command: `cargo xtask test-feature F054`
- Full command: `cargo xtask test-all`
- First failing tests: `flow_publish_rejects_cycle`, `flow_publish_denies_foreign_connection`, `run_enqueue_is_idempotent_by_key`, `executor_retries_rate_limited_then_fails_step`, `executor_redacts_secrets_in_snapshots`, `wait_approval_resumes_on_decision`, `bridge_route_denied_without_entitlement`

## Exit criteria

- [ ] Requirement tests SR-S107-01 through SR-S107-07 written first and failing
- [ ] Tasks T213 and T214 complete and wired through `services/api` router and the worker consumer registry
- [ ] Unit, API, worker, database, permission, and performance tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/bridge/routes.rs` mounted in `services/api/src/router.rs` behind `RequireModule(ModuleSlug::Bridge)`; `services/worker/src/bridge/executor.rs` registered in `services/worker/src/main.rs`
- [ ] Handoff evidence recorded in the F054 ticket
