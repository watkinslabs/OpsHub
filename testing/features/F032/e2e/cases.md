# F032 e2e cases

File: `testing/features/F032/e2e/{governance.spec.ts,intake.spec.ts,governance_permissions.spec.ts}`. Playwright against seeded tenant. Flag `F032_FEATURE`.

- `override_health_with_reason` — FR-F032-06, FR-F032-14: admin overrides to red with reason; banner shows author and reason; reload persists.
- `submit_and_approve_gate_with_evidence` — FR-F032-08, FR-F032-09: editor attaches file and completes checklist on gate 1, submits; approver approves; timeline shows approver and date.
- `out_of_sequence_submit_shows_message` — FR-F032-08: editor opens gate 2 first and sees `Gate 1 must be approved first`.
- `approval_page_decision_syncs_gate` — FR-F032-10: approver approves from the F020 approvals page; governance page shows gate approved with one decision.
- `rejected_gate_can_be_resubmitted` — FR-F032-09: reject with reason; gate returns to pending; resubmission shows attempt 2.
- `intake_to_provisioned_project` — FR-F032-11, FR-F032-12: requester submits intake with a portfolio; approver approves; status reaches `Provisioned`; project link opens and the portfolio lists it.
- `viewer_has_no_governance_controls` — FR-F032-13: viewer sees health and gates read-only without override, submit, or decide.
- `non_member_sees_not_found` — FR-F032-13: user outside the workspace opens the governance URL → not-found page.

Evidence: Playwright traces and videos under `testing/evidence/F032/e2e/`.
