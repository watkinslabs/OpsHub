# F020 e2e cases

File: `testing/features/F020/e2e/approvals.spec.ts`. Playwright against seeded tenant with worker and clock-control endpoint. Flag `F020_FEATURE`.

- `request_from_row_and_approve_from_inbox` — FR-F020-01, FR-F020-02, FR-F020-04, FR-F020-13: requester opens row "Vendor contract", requests approval from Ana and Ben with `any`; Ana opens the inbox from the notification, approves; status `Approved`; requester notified.
- `reject_with_reason_records_audit` — FR-F020-03, FR-F020-12: Ben rejects with reason "Budget exceeded"; detail shows the reason; activity feed shows the audit entry.
- `reassign_records_audit_and_notifies` — FR-F020-05: Ben reassigns to Dee; Dee sees the approval in her inbox; audit entry present.
- `overdue_escalates_to_manager` — FR-F020-08: approval with `standard` policy; clock advanced 61 min; manager's inbox shows the approval at level 1 with escalation trail.
- `expired_auto_reject_visible` — FR-F020-09: `auto_reject` policy past due; detail shows system decision `expired`.
- `non_approver_read_only` — FR-F020-13: reader opens detail; no decision controls.
- `workflow_reacts_to_decision` — FR-F020-04: published workflow with `approval_decided` trigger sets `Status` to `Approved` after Ana approves.
- `keyboard_only_approve` — NFR-F020-03: no mouse; arrow to item, `Enter`, `A`, confirm; approval announced.

Evidence: Playwright traces and videos under `testing/evidence/F020/e2e/`.
