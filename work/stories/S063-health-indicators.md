---
id: S063
type: story
status: planned
parent_epic: E007
parent_feature: F032
depends_on: [F031, F020]
owned_paths: [crates/domain/src/governance/**, services/api/src/governance/**, services/worker/src/governance/**, services/api/migrations/*_governance_*.sql, testing/features/F032/**]
feature_flag: F032_FEATURE
branch: s063-health-indicators
started_at: null
finished_at: null
---

# S063 — Health indicators

## Identity

- Parent feature: `F032` Project health/governance
- Owner: platform
- Branch: `s063-health-indicators`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 7; `docs/capability-contracts.md` row F032

## Vertical slice

As a portfolio administrator, I want a configurable weighted health model, computed project health with confidence and an auditable override, and the gate and intake state machines behind the governance API, so that health and governance decisions are consistent before any screen renders them.

## Requirements

- **SR-S063-01:** `PUT /api/v1/health-models/{id}` upserts a model whose five weights sum to 100 and whose thresholds satisfy `100 ≥ green_min > amber_min ≥ 0`; weights summing to 99 return `400 invalid` with `field_errors.weights`; a second `tenant_default` model returns `409 conflict` (covers FR-F032-01).
- **SR-S063-02:** `score_indicators` maps schedule, budget, scope, risk, and resource inputs to 0–100 by the linear rules with the defaults `late_days_for_zero 30`, `over_pct_for_zero 25`, `creep_pct_for_zero 20`, `risk_points_for_zero 12`, `conflicts_for_zero 5`; `compute_project_health` renormalizes weights over `ok` indicators, sets `confidence`, and returns `unknown` when none are available (FR-F032-02, FR-F032-03).
- **SR-S063-03:** The worker debounces recompute per project to one run per 60 seconds after `row.updated.v1`, `baseline.captured.v1`, `allocation.*.v1`, or `workload-conflict.detected.v1`, writes `project_health`, and publishes `project-health.computed.v1` naming moved indicators (FR-F032-04, NFR-F032-04).
- **SR-S063-04:** `GET /api/v1/projects/{id}/health` returns computed, override, and `effective_colour`; `PUT /health-override` requires a 10–1,000 character reason, supports clearing and `expires_at`, writes audit, publishes `health-override.set.v1`, and reports `expired: true` past expiry (FR-F032-05, FR-F032-06).
- **SR-S063-05:** `submit_stage_gate` and `decide_stage_gate` enforce the transitions `pending → submitted → approved | rejected → pending | deferred`, reject missing evidence with `field_errors.evidence[i]`, reject out-of-sequence submission with `conflict` `gate_sequence`, write insert-only `stage_gate_decisions` with `evidence_snapshot`, and publish `stage-gate.submitted.v1` and `stage-gate.decided.v1` (FR-F032-07, FR-F032-08, FR-F032-09).
- **SR-S063-06:** `submit_intake` and `advance_intake` move a request through `submitted → approved → provisioning → provisioned | failed` or `submitted → rejected`, open the F020 approval with policy key `project_intake`, and publish `project-intake.submitted.v1` (FR-F032-11, FR-F032-12).
- **SR-S063-07:** A `sheet-viewer` receives `403 denied` on override, model, submit, and decide; a foreign-tenant actor receives `404 not_found` on every route (FR-F032-13).

## Surfaces

- Infrastructure/container: worker consumer registration in `services/worker/src/governance/mod.rs` (F004 JetStream)
- Rust service/API: `crates/domain/src/governance/{mod.rs, model.rs, scoring.rs, health.rs, gates.rs, intake.rs, errors.rs, service_health.rs, service_gates.rs, service_intake.rs}`; `services/api/src/governance/{mod.rs, routes.rs, handlers_health.rs, handlers_gates.rs, handlers_intake.rs, dto.rs}`; `services/worker/src/governance/{health_recompute.rs, gate_provisioning.rs, approval_sync.rs, intake_provisioning.rs}`
- Data/migration: `services/api/migrations/<ts>_governance_create_tables.sql` creating the five tables with indexes from ticket section 4
- React/UI: none in this story (S064 and T127 cover UI)
- Mocks/fixtures: `testing/fixtures/governance.rs` tenants A and B, admin, approver, editor, viewer, provisioned project with baseline and risk rows, template version with three gates, `project_intake` approval policy; in-memory outbox recorder; stubbed F034 conflict counter

## TDD harness

- Test path: `testing/features/F032/api/` and `testing/features/F032/database/`
- Feature flag: `F032_FEATURE`
- Targeted command: `cargo xtask test-feature F032`
- Full command: `cargo xtask test-all`
- First failing tests: `health_model_weights_must_sum_to_hundred`, `health_score_renormalizes_missing_indicator`, `health_override_requires_reason`, `gate_submit_missing_evidence_invalid`, `gate_submit_out_of_sequence_conflicts`, `gate_decide_records_snapshot_and_event`, `intake_submit_opens_approval`

## Exit criteria

- [ ] Requirement tests SR-S063-01 through SR-S063-07 written first and failing
- [ ] Tasks T125 and T126 complete and wired through `services/api` router and worker consumers
- [ ] Unit, API, database, worker, permission tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/governance/routes.rs` mounted in `services/api/src/router.rs` behind `F032_FEATURE`; `services/worker/src/governance/health_recompute.rs` registered in `services/worker/src/main.rs`
- [ ] Handoff evidence recorded in the F032 ticket
