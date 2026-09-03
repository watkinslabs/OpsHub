# F047 frontend cases

File: `testing/features/F047/frontend/{PendingApprovalsTable.test.tsx,ChangeSummaryDiff.test.tsx,ApproveDialog.test.tsx,ExpiryCountdown.test.tsx,McpActivityTable.test.tsx,McpCallDrawer.test.tsx,ConnectClientPanel.test.tsx}`. Vitest with MSW. Flag `F047_FEATURE`.

- `renders_diff_and_countdown_for_pending_row` — FR-F047-15: a pending `update_record` row shows the tool, the linked task, `due_date 2026-09-10 → 2026-09-24`, and a 14-minute countdown.
- `create_summary_renders_proposed_record` — FR-F047-08: a `create_record` proposal renders every proposed field with an empty `before`.
- `long_values_collapse_with_show_more` — FR-F047-15: a 40-line description collapses at 5 lines and expands on `Show more`.
- `expired_row_disables_approve_in_place` — FR-F047-15: the countdown reaching zero greys the row, labels it `Expired`, and disables `Approve` without removing it.
- `approve_conflict_renders_expired_not_error_toast` — FR-F047-15: a `409` from `approveConfirmation` sets the row to `Expired` and raises no error toast.
- `approve_dialog_names_the_resource` — FR-F047-15: the confirm dialog text includes the tool and the target record title.
- `filters_by_decision_and_opens_drawer` — FR-F047-14: `McpActivityTable` filters to `confirmation_required` and `Enter` on a row opens `McpCallDrawer`.
- `drawer_shows_correlation_id_and_copy_action` — FR-F047-14: the drawer renders method, tool, decision, outcome, duration, redacted field count, and a copy-correlation-id button.
- `member_sees_only_own_rows_and_no_actor_filter` — FR-F047-14: a non-admin session hides the actor filter and requests the audit list without `actor_id`.
- `connect_panel_shows_endpoint_and_required_scope` — FR-F047-15: the panel renders the `/mcp/v1` URL, `mcp:access`, and a link to the API token page.
- `shows_error_banner_with_correlation_id` — NFR-F047-04: a `503` on the audit list renders a banner with `correlation_id` and retry.
- `empty_states_render_for_both_tables` — FR-F047-15: no pending rows renders `No pending approvals`; no audit rows renders `No MCP calls yet`.

Evidence: Vitest JUnit under `testing/evidence/F047/frontend/`.
