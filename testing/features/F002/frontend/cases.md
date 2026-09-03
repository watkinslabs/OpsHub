# F002 frontend cases

File: `testing/features/F002/frontend/{UsersTable.test.tsx,InviteUserDialog.test.tsx,GroupMembersEditor.test.tsx,TenantSettingsForm.test.tsx}`. Vitest with MSW. Flag `F002_FEATURE`.

- `UsersTable.test.tsx::renders_status_badges` — FR-F002-14: fixture users render `Invited`, `Active`, `Suspended`, `Deactivated` badges with text, not colour only.
- `UsersTable.test.tsx::shows_loading_skeleton_then_rows` — FR-F002-14: pending query shows skeleton rows; resolves to 5 rows.
- `UsersTable.test.tsx::shows_empty_state_with_invite_cta` — FR-F002-14: zero users shows `No users yet` and the invite button.
- `UsersTable.test.tsx::shows_denied_for_member` — FR-F002-14: member context renders the denied state and no invite or deactivate controls.
- `UsersTable.test.tsx::shows_error_banner_with_correlation_id` — NFR-F002-04: 500 response shows banner containing `correlation_id` and retry.
- `InviteUserDialog.test.tsx::validates_email_and_name` — FR-F002-05: empty or malformed email blocks submit; 409 shows `field_errors.email`.
- `DeactivateUserDialog.test.tsx::last_admin_button_disabled_with_reason` — FR-F002-08: sole admin row shows disabled deactivate with the `last_admin` explanation.
- `GroupMembersEditor.test.tsx::toggles_members_and_saves_full_set` — FR-F002-10: toggling sends the complete `user_ids` array once.
- `GroupMembersEditor.test.tsx::rolls_back_on_invalid` — FR-F002-10: 400 `field_errors.user_ids` restores previous set and highlights offending users.
- `TenantSettingsForm.test.tsx::stale_version_shows_reload_banner` — FR-F002-03: 409 shows `This record changed` with `Reload`.
- `TenantSettingsForm.test.tsx::suspended_tenant_notice` — FR-F002-04: `status: suspended` renders the full-page notice with the operator contact.
- `UsersTable.test.tsx::offline_disables_mutations` — FR-F002-14: `navigator.onLine=false` disables invite and deactivate with the offline badge.

Evidence: Vitest JUnit under `testing/evidence/F002/frontend/`.
