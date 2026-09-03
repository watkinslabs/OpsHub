---
id: T074
type: task
status: planned
parent_epic: E004
parent_feature: F019
parent_story: S037
depends_on: [T073]
owned_paths: [crates/domain/src/workflow-runtime/**, services/api/src/workflow-runtime/**, services/worker/src/workflow-runtime/**, testing/features/F019/api/**, testing/features/F019/requirements/**]
feature_flag: F019_FEATURE
branch: t074-idempotency
started_at: null
finished_at: null
---

# T074 — Idempotency

## Identity

- Parent story: `S037` Queued runs
- Owner: platform
- Branch: `t074-idempotency`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 7; `docs/capability-contracts.md` row F019

## Objective

Make every entry point into the runtime idempotent and expose the run history and inbound webhook routes so redelivered events, replayed webhooks, and repeated executor attempts never duplicate side effects.

## Specification

- Owned paths: `crates/domain/src/workflow-runtime/{idempotency.rs, correlation.rs, service_query.rs}`, `services/worker/src/workflow-runtime/executors/idempotent.rs`, `services/api/src/workflow-runtime/{mod.rs, routes.rs, handlers_runs.rs, handlers_webhook.rs, dto.rs}`
- Contract/input: run key `sha256(workflow_version_id || trigger_event_id)`; step key `(run_id, index, attempt)`; `POST /api/v1/webhooks/inbound/{token}` with headers `X-OpsHub-Signature` (HMAC-SHA256 of the raw body with the token secret from the F029 vault reference), `X-OpsHub-Delivery-Id`, JSON body ≤ 256 KB; list query `{ cursor?, limit? ≤ 200, filter[status]?, filter[workflow_id]?, filter[started_after]?, filter[started_before]?, sort? }`.
- Output/behavior: duplicate event delivery returns the existing run and inserts nothing; executor wrapper checks the step key before invoking any executor and records output once; webhook route validates the signature in constant time (`denied` on mismatch), stores `(webhook_id, delivery_id)` for 24 hours and returns the original `run_id` on replay, rate-limits 60 per minute per token (`rate_limited`), rejects oversized bodies (`invalid`); routes `GET /api/v1/workflow-runs`, `GET /api/v1/workflow-runs/{id}`, `GET /api/v1/workflows/{id}/runs` return `RunResponse { id, workflow_id, workflow_version_no, status, trigger, correlation_id, parent_run_id, started_at, finished_at, duration_ms, error }` and `RunDetailResponse` with steps; correlation chain carried in `correlation_id` and `parent_run_id`.
- Dependencies: T073 tables and consumer; F003 `authz::require(actor, Permission::WorkflowView, workspace)`; F028 signature helper crate.
- Feature flag: `F019_FEATURE` gates router mounting.

## TDD

- Failing test first: `testing/features/F019/api/idempotency_tests.rs::duplicate_event_delivery_creates_no_second_run`, `::executor_attempt_key_prevents_double_side_effect`, `::inbound_webhook_bad_signature_denied`, `::inbound_webhook_replayed_delivery_returns_original_run`, `::inbound_webhook_rate_limited_after_sixty`, `::inbound_webhook_body_over_256kb_invalid`; `testing/features/F019/api/run_query_tests.rs::run_list_filters_by_status_and_window`, `::run_detail_returns_ordered_steps`, `::run_cross_tenant_not_found`
- Targeted command: `cargo xtask test-feature F019`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/workflow_runtime.rs` tenants A and B, editor, viewer, inbound token; recording executors; embedded JetStream

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Router mounted in `services/api/src/router.rs` behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S037
- [ ] `finished_at` recorded
