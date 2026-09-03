# F020 frontend cases

File: `testing/features/F020/frontend/{ApprovalInboxPage.test.tsx,ApprovalDetailPage.test.tsx,DecideDialog.test.tsx,ReassignDialog.test.tsx,RequestApprovalDialog.test.tsx,PolicyEditor.test.tsx}`. Vitest with MSW. Flag `F020_FEATURE`.

- `inbox_lists_assigned_with_due_badges` — FR-F020-13: 12 approvals render with `DueBadge` text `Due in 2 days` / `Overdue` plus icon.
- `inbox_empty_state` — FR-F020-13: no assigned approvals shows `Nothing waiting for you`.
- `detail_shows_approvers_decisions_and_trail` — FR-F020-10: detail renders approver states, decision history, and escalation levels.
- `reject_dialog_requires_reason` — FR-F020-03: `Reject` disabled until reason typed; empty submit focuses the reason error.
- `decide_rolls_back_on_conflict` — FR-F020-14: 409 restores pending state and shows `This approval was already decided`.
- `non_approver_sees_read_only` — FR-F020-13: reader role hides `Approve`, `Reject`, `Reassign` and shows explanation.
- `reassign_dialog_validates_target_access` — FR-F020-05: 400 `field_errors.to_user_id` shows inline error on the user picker.
- `request_dialog_builds_quorum_payload` — FR-F020-01: choosing `At least 2 of 3` sends `quorum: { count: 2 }`.
- `policy_editor_validates_minimums` — FR-F020-07: `escalate_after_minutes` below 5 shows inline error; `max_escalations` limited to 1–3.
- `pending_count_refreshes_on_notification` — FR-F020-13: incoming `approval` notification invalidates `['approvals-pending-count']`.
- `shows_not_found_for_foreign_approval` — FR-F020-11: 404 renders not-found page.
- `offline_disables_decisions` — FR-F020-13: `navigator.onLine=false` disables approve/reject with offline badge.
- `keyboard_shortcuts_open_dialogs` — NFR-F020-03: `A`, `R`, `S` open the matching dialogs; `Escape` closes.

Evidence: Vitest JUnit under `testing/evidence/F020/frontend/`.
