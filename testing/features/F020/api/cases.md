# F020 api cases

File: `testing/features/F020/api/{approval_tests.rs,quorum_tests.rs,escalation_tests.rs,reassign_tests.rs}`. Flag `F020_FEATURE`.

- `approval_create_expands_group_and_notifies` — FR-F020-01, FR-F020-02: 2 users + group of 4 → 6 approvers, 6 notifications, `approval.requested.v1`.
- `approval_create_twenty_one_approvers_invalid` — FR-F020-01: 21 references → 400 `field_errors.approvers`.
- `approval_create_count_above_approvers_invalid` — FR-F020-01: `count: 4` with 3 approvers → 400 `field_errors.quorum`.
- `approval_create_due_under_fifteen_minutes_invalid` — FR-F020-01: `due_at` now + 5 min → 400 `field_errors.due_at`.
- `approval_create_excludes_requester_notification` — FR-F020-02: requester not in set receives no `approval` notification.
- `decide_by_non_approver_denied` — FR-F020-03: reader of the row who is not an approver → 403 `denied`, no decision row.
- `reject_without_reason_invalid` — FR-F020-03: `rejected` with empty reason → 400 `field_errors.reason`.
- `second_decision_same_approver_conflicts` — FR-F020-03: same approver twice → 409 `conflict`.
- `any_quorum_completes_on_first_approval` — FR-F020-04: first `approved` → `approved`, `approval.decided.v1`.
- `all_quorum_waits_for_every_approver` — FR-F020-04: 2 of 3 approved → still `pending`; third → `approved`.
- `count_quorum_completes_on_nth_approval` — FR-F020-04: `count: 2`, second approval → `approved`, third approver's notification withdrawn.
- `single_rejection_rejects_under_all_rules` — FR-F020-04: one `rejected` under `any`, `all`, `count` → `rejected`.
- `completion_withdraws_pending_notifications` — FR-F020-04: pending approver notifications marked withdrawn on completion.
- `reassign_keeps_other_decisions` — FR-F020-05: Ana approved, Ben → Dee; Ana's decision retained, Dee notified, audit row written.
- `reassign_to_user_without_access_invalid` — FR-F020-05: target user lacks row read → 400 `field_errors.to_user_id`.
- `reassign_by_unrelated_user_denied` — FR-F020-05: non-requester, non-editor, non-replaced approver → 403.
- `cancel_emits_event_and_blocks_decide` — FR-F020-06: cancel → `approval.cancelled.v1`, timers voided; decide → 409.
- `policy_escalate_after_under_five_invalid` — FR-F020-07: `escalate_after_minutes: 3` → 400; `max_escalations: 4` → 400.
- `timers_scheduled_from_policy` — FR-F020-08: `standard` with reminders `[1440, 60]` → 2 reminder rows, 1 escalate, 1 expire.
- `sweeper_escalates_to_manager_once_per_level` — FR-F020-08: +61 min → manager at level 1; +121 min → level 2; `approval.escalated.v1` twice.
- `sweeper_stops_after_max_escalations` — FR-F020-08: `max_escalations: 2` → no level 3 timer scheduled.
- `reminder_sent_before_due` — FR-F020-08: sweep at `due_at - 60 min` → reminder notification per pending approver.
- `expiry_auto_reject_writes_system_decision` — FR-F020-09: past due with `auto_reject` → decision `system: true`, reason `expired`, `rejected`.
- `expiry_none_flags_overdue` — FR-F020-09: past due with `none` → `pending`, `overdue: true` in reads.
- `completion_voids_unfired_timers` — FR-F020-08: approval completes → remaining timers get `fired_at` with `voided` marker and never fire.
- `list_assigned_to_me_filters_by_membership` — FR-F020-10: 300 approvals, `filter[assigned_to_me]=true`, `sort=due_at`, pages of 100.
- `read_requires_target_access_or_membership` — FR-F020-11: outsider → 404; approver without target ACL → 200.
- `mutations_write_append_only_audit` — FR-F020-12: decide, reassign, escalate, expire, cancel → 5 audit rows with `correlation_id`; UPDATE attempt on audit fails.
- `stale_version_conflicts` — FR-F020-14: `If-Match: 1` against version 2 → 409 with `current_version`.
- `idempotent_replay_returns_original` — FR-F020-14: same `Idempotency-Key` twice → one decision, same body.
- `group_edit_after_creation_adds_no_approver` — NFR-F020-02: add user to group after create → approver set unchanged.
- `approval_cross_tenant_not_found` — NFR-F020-02: tenant B on every route → 404.
- `concurrent_sweepers_fire_timer_once` — NFR-F020-04: two sweepers over 100 due timers → each fired exactly once.
- `concurrent_count_decisions_resolve_once` — FR-F020-04: two approvers decide simultaneously under `count: 2` → one `approval.decided.v1`.

Evidence: JUnit output and request logs under `testing/evidence/F020/api/`.
