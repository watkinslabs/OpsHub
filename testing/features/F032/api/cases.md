# F032 api cases

File: `testing/features/F032/api/{health_tests.rs,gate_tests.rs,intake_tests.rs,permission_tests.rs}`. Flag `F032_FEATURE`.

- `health_model_weights_must_sum_to_hundred` — FR-F032-01: weights 40/30/10/10/9 → 400 `field_errors.weights`; 40/30/10/10/10 → 200 with version 1.
- `health_model_thresholds_must_be_ordered` — FR-F032-01: `green_min 40, amber_min 70` → 400 `field_errors.thresholds`.
- `health_model_second_default_conflicts` — FR-F032-01: second `tenant_default` model → 409 `conflict`.
- `health_indicators_score_by_linear_rules` — FR-F032-02: 15 days late → 50; 10 percent over → 60; two medium risks (4 of 12 points) → 67; zero conflicts → 100.
- `health_score_renormalizes_missing_indicator` — FR-F032-03: resource `missing` → score over weights 90, `confidence: 90`, colour from thresholds.
- `health_unknown_when_no_indicators` — FR-F032-03: project with no baseline, budget, risk, or allocations → `colour: unknown`, `confidence: 0`.
- `recompute_debounced_and_publishes_event` — FR-F032-04: three `row.updated.v1` in 10 s → one `project_health` write and one `project-health.computed.v1` naming `schedule`.
- `health_read_requires_project_access` — FR-F032-05: viewer denied on the project sheet → 404; sheet-viewer → 200 with `effective_colour`.
- `health_override_requires_reason` — FR-F032-06: reason "too short" → 400 `field_errors.reason`; 10 chars → 200, audit row, `health-override.set.v1`.
- `health_override_expiry_ignored_in_effective_colour` — FR-F032-06: `expires_at` passed → `effective_colour` equals computed, `override.expired: true`.
- `health_override_clear_records_reason` — FR-F032-06: `colour: null` with reason → override null, audit diff shows previous colour.
- `gates_created_from_template_on_provision` — FR-F032-07: consuming `project.provisioned.v1` → three `stage_gates` rows in sequence, `pending`.
- `gate_submit_missing_evidence_invalid` — FR-F032-08: file provided, checklist absent → 400 `field_errors.evidence[1]`.
- `gate_submit_out_of_sequence_conflicts` — FR-F032-08: gate 2 while gate 1 pending → 409 with `code_detail: gate_sequence`.
- `gate_submit_opens_approval_and_publishes` — FR-F032-08: complete evidence → `submitted`, `attempt: 1`, F020 approval created, `stage-gate.submitted.v1`.
- `gate_decide_records_snapshot_and_event` — FR-F032-09: approve → decision row with approver, server `decided_at`, `evidence_snapshot` checksums, `stage-gate.decided.v1`.
- `gate_decide_on_pending_conflicts` — FR-F032-09: decide a `pending` gate → 409.
- `gate_reject_requires_reason` — FR-F032-09: `rejected` without reason → 400 `field_errors.reason`.
- `gate_rejected_returns_to_pending_with_next_attempt` — FR-F032-09: reject then resubmit → `attempt: 2`, prior decision row retained.
- `approval_decision_applied_once_per_approval_id` — FR-F032-10: `approval.decided.v1` twice → one decision row, gate approved.
- `intake_submit_opens_approval` — FR-F032-11: POST intake → `submitted`, `approval_id` set with policy `project_intake`, `project-intake.submitted.v1`.
- `intake_approval_provisions_project_and_joins_portfolio` — FR-F032-12: approved → `provisioning` → `provisioned`, `project_sheet_id` set, `portfolio_projects` row exists.
- `intake_rejection_sets_reason` — FR-F032-12: rejected approval → `rejected` with reason.
- `intake_provisioning_failure_sets_failed` — FR-F032-12: provision use case error → `failed` with `error`.
- `governance_mutations_write_audit` — FR-F032-13: override, submit, decide, intake → one audit row each with diff.
- `health_cross_tenant_not_found` — FR-F032-13: tenant B on health, override, gates, intake → 404.
- `cross_tenant_all_routes_not_found` — NFR-F032-02: tenant B admin on all eight routes → 404, no audit read event.
- `viewer_all_mutations_denied` — FR-F032-13: sheet-viewer on override, model, submit, decide → 403, no audit mutation.
- `non_approver_decide_denied` — NFR-F032-02: editor outside approver set → 403 on decide.
- `evidence_snapshot_has_no_file_bodies` — NFR-F032-02: snapshot contains `file_id` and `checksum` only.
- `recompute_retries_then_dead_letters` — NFR-F032-04: scoring input failure four times → dead letter, `project_health.last_error` set.
- `request_span_carries_ids` — NFR-F032-04: span has `tenant_id`, `project_sheet_id`, `gate_id`, `correlation_id`.

Evidence: JUnit output and request logs under `testing/evidence/F032/api/`.
