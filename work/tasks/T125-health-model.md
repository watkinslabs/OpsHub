---
id: T125
type: task
status: planned
parent_epic: E007
parent_feature: F032
parent_story: S063
depends_on: [S063]
owned_paths: [services/api/migrations/*_governance_*.sql, crates/domain/src/governance/**, services/api/src/governance/**, services/worker/src/governance/**, testing/features/F032/database/**, testing/features/F032/api/**]
feature_flag: F032_FEATURE
branch: t125-health-model
started_at: null
finished_at: null
---

# T125 — Health model

## Identity

- Parent story: `S063` Health indicators
- Owner: platform
- Branch: `t125-health-model`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 7; `docs/capability-contracts.md` row F032

## Objective

Create the governance schema and implement health models, indicator scoring, weighted health computation, the override endpoint, and the debounced recompute worker.

## Specification

- Owned paths: `services/api/migrations/<ts>_governance_create_tables.sql`, `services/api/migrations/<ts>_governance_create_tables.down.sql`, `crates/domain/src/governance/{mod.rs, schema.rs, model.rs, scoring.rs, health.rs, errors.rs, service_health.rs}`, `services/api/src/governance/{mod.rs, routes.rs, handlers_health.rs, dto.rs}`, `services/worker/src/governance/{mod.rs, health_recompute.rs}`
- Contract/input: DDL for `health_models`, `project_health`, `stage_gates`, `stage_gate_decisions`, `project_intake_requests` per ticket section 4 with checks, unique indexes, and insert-only decisions; `UpsertHealthModelRequest { name, scope, weights { schedule, budget, scope, risk, resource }, thresholds { green_min, amber_min }, rules }`; `HealthOverrideRequest { colour | null, reason, expires_at? }`; headers `Idempotency-Key`, `If-Match`; recompute trigger events `row.updated.v1`, `baseline.captured.v1`, `allocation.*.v1`, `workload-conflict.detected.v1`.
- Output/behavior: `sqlx migrate run` and `revert` apply cleanly after F006, F015, F020, F031 migrations; routes `PUT /api/v1/health-models/{id}`, `GET /api/v1/projects/{id}/health`, `PUT /api/v1/projects/{id}/health-override` return `ProjectHealthResponse` and model responses per ticket section 4; `scoring.rs` implements the linear indicator rules with defaults; `health.rs` renormalizes weights over available indicators, sets `confidence`, applies thresholds, and returns `unknown` with no indicators; the worker debounces per project for 60 s, batches the nightly run in groups of 50, is idempotent by `(project_sheet_id, source_version)`, retries 3 times, dead-letters with `last_error`, and publishes `project-health.computed.v1`; override writes audit and `health-override.set.v1`; errors map per ticket section 4.
- Dependencies: F015 `baselines` and variance for schedule and scope inputs; F031 `portfolio_projects` for portfolio-scoped nightly runs; F003 `authz::require(actor, Permission::PortfolioAdmin, workspace)`; F004 outbox and JetStream; F034 conflict counts through the `ConflictCounter` trait (stubbed until F034 ships).
- Feature flag: `F032_FEATURE` gates router mounting and consumer registration; migration runs regardless.

## TDD

- Failing test first: `testing/features/F032/database/migration_tests.rs::governance_tables_exist_with_constraints`, `::second_tenant_default_model_rejected`, `::decision_rows_are_insert_only`, `::rollback_drops_tables`; `testing/features/F032/api/health_tests.rs::health_model_weights_must_sum_to_hundred`, `::health_score_renormalizes_missing_indicator`, `::health_unknown_when_no_indicators`, `::health_override_requires_reason`, `::health_override_expiry_ignored_in_effective_colour`, `::recompute_debounced_and_publishes_event`, `::health_cross_tenant_not_found`
- Targeted command: `cargo xtask test-feature F032`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: schema-per-worker database from `testing/harness/db.rs`; `testing/fixtures/governance.rs` project with baseline 15 days behind and 10 percent budget overrun; stubbed `ConflictCounter`; in-memory outbox recorder

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; router and consumer registered behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S063
- [ ] `finished_at` recorded
