# F002 e2e cases

File: `testing/features/F002/e2e/admin.spec.ts`. Playwright against the seeded tenant fixture. Flag `F002_FEATURE`.

- `invite_user_create_group_edit_members` — FR-F002-05, FR-F002-09, FR-F002-10, FR-F002-14: admin invites `pat@acme.test`, creates `Finance`, adds 5 members, reload shows 5 members and the invited row.
- `duplicate_email_shows_field_error` — FR-F002-05: inviting an existing email shows the inline email error.
- `deactivate_user_revokes_access` — FR-F002-08: admin deactivates a member; the member's open session gets the logged-out state on next navigation; member no longer appears in group.
- `last_admin_cannot_be_deactivated` — FR-F002-08: sole admin sees the disabled action and explanation.
- `member_sees_denied_on_admin_pages` — FR-F002-14: member visits `/admin/users` → denied state; own profile card still opens.
- `suspended_tenant_shows_notice` — FR-F002-04: operator suspends tenant; admin's next page load shows `Tenant suspended`.
- `concurrent_tenant_edit_shows_stale_banner` — FR-F002-03: second session renames the tenant; first session's save shows the stale banner and reload.

Evidence: Playwright traces and videos under `testing/evidence/F002/e2e/`.
