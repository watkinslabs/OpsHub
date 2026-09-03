# F047 e2e cases

File: `testing/features/F047/e2e/mcp.spec.ts`. Playwright against the seeded tenant while the stub MCP client plays the conformance script server-side. Flag `F047_FEATURE`.

- `approve_pending_mutation_and_retry_succeeds` — FR-F047-08, FR-F047-09, FR-F047-10, FR-F047-15: the client proposes `update_record` on task `Ship beta`; the member opens `/admin/mcp`, reads `due_date 2026-09-10 → 2026-09-24`, clicks `Approve` and confirms; the client retries and the task page shows the new due date with one version increment.
- `expired_confirmation_shows_expired_and_disables_approve` — FR-F047-15: the clock advances past `expires_at`; the row greys out in place as `Expired`, `Approve` is disabled, and the client's retry surfaces the conflict.
- `activity_table_shows_confirmation_required_then_allowed` — FR-F047-11, FR-F047-14: after the approved flow the activity table lists a `confirmation_required` row and an `allowed` row for `update_record` sharing one `correlation_id`.
- `read_only_client_sees_no_mutating_tools` — FR-F047-06: a token without `records:write` lists five tools and any `update_record` attempt returns `denied`; `/admin/mcp` shows no pending approvals.
- `second_member_cannot_approve` — FR-F047-09: another member opening `/admin/mcp` does not see the proposal, and a direct approve request returns the denied state.
- `document_resource_appears_and_updates_over_sse` — FR-F047-04, FR-F047-13: the client reads `opshub://document/<id>`, an editor saves a new revision, and the client receives `notifications/resources/updated` for that URI within 5 seconds.

Evidence: Playwright traces and stub-client frame logs under `testing/evidence/F047/e2e/`.
