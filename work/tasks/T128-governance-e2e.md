---
id: T128
type: task
status: planned
parent_epic: E007
parent_feature: F032
parent_story: S064
depends_on: [T127]
owned_paths: [testing/features/F032/e2e/**, testing/features/F032/performance/**, testing/features/F032/api/**, testing/features/F032/requirements/**]
feature_flag: F032_FEATURE
branch: t128-governance-e2e
started_at: null
finished_at: null
---

# T128 — Governance E2E

## Identity

- Parent story: `S064` Stage gates and intake
- Owner: platform
- Branch: `t128-governance-e2e`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 4, 9; `docs/capability-contracts.md` row F032

## Objective

Prove the full governance path in the browser and under load: override with reason, gate submission and approval synchronized with F020, intake through provisioning, permission negatives, and the health and decision performance targets.

## Specification

- Owned paths: `testing/features/F032/e2e/{governance.spec.ts, intake.spec.ts, governance_permissions.spec.ts}`, `testing/features/F032/performance/governance_bench.rs`, `testing/features/F032/api/{permission_tests.rs, governance_constraint_tests.rs}`, `testing/features/F032/requirements/cases.md`
- Contract/input: seeded tenant A with portfolio-admin, approver, sheet-editor, sheet-viewer sessions, a provisioned project with three template gates, tenant-default health model, `project_intake` approval policy, a clean scanned file; tenant B admin; generated 1,000-project tenant with fixed seed for the nightly benchmark.
- Output/behavior: Playwright flows: administrator overrides health to red with a reason and the banner shows author and reason; editor submits gate 2 before gate 1 and sees the sequence message, then submits gate 1 with complete evidence; approver approves it from the governance page and the timeline shows approver and date; approving the linked F020 approval from the approvals page instead yields the same gate state without a second decision row; requester submits intake, approver approves, status page reaches `Provisioned` with a working project link and the project appears in the chosen portfolio; viewer sees no override, submit, or decide controls; tenant B receives 404 on every governance route; non-approver decide is denied. Benchmarks: `GET /health` and `GET /stage-gates` p95 < 500 ms over 200 requests; override, submit, decide, intake writes p95 < 800 ms; single-project recompute < 5 s; nightly recompute of 1,000 projects < 20 minutes.
- Data access: no test opens a connection or issues SQL; every fixture write and every assertion about stored state goes through the `crates/persistence/src/governance/` repositories, and `governance_constraint_tests.rs` proves the child-table constraints by driving those repositories — a sixth `health_model_weights` row and a weight set summing to 99 are rejected, `health_model_thresholds` requires `green.min_score > amber.min_score`, a duplicate `project_health_indicators` `display_order` and a second `project_health_overrides` row are rejected, a second `stage_gate_evidence` row for the same `(gate_id, attempt, requirement_id)` is rejected, a `stage_gate_evidence_checklist` row without a matching `stage_gate_requirement_items` row is rejected, and `stage_gate_decision_evidence` rows are unchanged by a later attempt (decision sections 2 and 2.1).
- Dependencies: T126 routes and consumers; T127 pages; F020 approvals page for the cross-path check; F015 provisioning fixture.
- Feature flag: `F032_FEATURE`

## TDD

- Failing test first: `testing/features/F032/e2e/governance.spec.ts::override_health_with_reason`, `::submit_and_approve_gate_with_evidence`, `::out_of_sequence_submit_shows_message`, `::approval_page_decision_syncs_gate`; `testing/features/F032/e2e/intake.spec.ts::intake_to_provisioned_project`; `testing/features/F032/e2e/governance_permissions.spec.ts::viewer_has_no_governance_controls`; `testing/features/F032/api/permission_tests.rs::cross_tenant_all_routes_not_found`, `::viewer_all_mutations_denied`, `::non_approver_decide_denied`; `testing/features/F032/api/governance_constraint_tests.rs::weight_rows_must_sum_to_hundred`, `::threshold_rows_must_be_ordered`, `::indicator_display_order_unique_per_project`, `::second_override_row_rejected`, `::duplicate_evidence_for_attempt_rejected`, `::checklist_tick_requires_requirement_item`, `::decision_snapshot_rows_survive_next_attempt`; `testing/features/F032/performance/governance_bench.rs::health_read_p95`, `::governance_writes_p95`, `::nightly_recompute_1000_projects_under_20m`
- Targeted command: `cargo xtask test-feature F032`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: Playwright uses the real API, worker, and F020 engine against the seeded tenant; 1,000-project generator with fixed seed; real authz engine

## Exit criteria

- [ ] Tests written before any fix and observed failing where behavior is missing
- [ ] E2E, permission-negative, and performance lanes green in targeted and full modes
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S064
- [ ] `finished_at` recorded
