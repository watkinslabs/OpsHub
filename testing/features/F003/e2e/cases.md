# F003 e2e cases

File: `testing/features/F003/e2e/authz.spec.ts`. Playwright against the seeded fixture. Flag `F003_FEATURE`.

- `create_role_set_deny_inspect_audit` — FR-F003-02, FR-F003-04, FR-F003-11, FR-F003-14: admin creates `Reviewer`, opens the sheet ACL, adds QA/Reviewer and a guest deny, then finds `acl.replace` in `/admin/audit` and copies the correlation id.
- `denied_user_sees_not_found` — FR-F003-05, FR-F003-08: after the deny, the guest's session opening the sheet URL lands on not-found.
- `commenter_acl_editor_read_only` — FR-F003-14: commenter opens `Permissions` and sees the read-only drawer.
- `member_admin_pages_denied` — FR-F003-14: member visits `/admin/roles` and `/admin/audit` → denied state.
- `owner_sees_resource_history_tab` — FR-F003-11: owner opens the sheet `History` tab and sees only that sheet's rows.
- `concurrent_acl_edit_shows_stale_banner` — FR-F003-12: second session replaces the ACL; first session's save shows the stale banner with the diff.

Evidence: Playwright traces and videos under `testing/evidence/F003/e2e/`.
