# F003 frontend cases

File: `testing/features/F003/frontend/{PermissionMatrix.test.tsx,RoleEditor.test.tsx,AclEditor.test.tsx,AuditLogPage.test.tsx,DiffViewer.test.tsx}`. Vitest with MSW. Flag `F003_FEATURE`.

- `PermissionMatrix.test.tsx::toggles_with_keyboard_and_labels` — FR-F003-14, NFR-F003-03: arrow keys move focus; `Space` toggles; checkbox label reads `Reviewer can sheet:read`.
- `PermissionMatrix.test.tsx::system_role_locked` — FR-F003-01: `viewer` row shows lock icon and disabled slug.
- `RoleEditor.test.tsx::unknown_permission_shows_field_error` — FR-F003-02: 400 renders `field_errors.permissions`.
- `RoleEditor.test.tsx::shows_loading_and_empty_states` — FR-F003-14: skeleton then `No custom roles yet`.
- `AclEditor.test.tsx::renders_direct_and_inherited_entries` — FR-F003-04: inherited rows show the `From workspace Ops` label.
- `AclEditor.test.tsx::adds_deny_with_confirm` — FR-F003-14: adding a deny opens confirm naming the principal; save sends full entries.
- `AclEditor.test.tsx::read_only_without_acl_manage` — FR-F003-14: `usePermission` false → controls disabled with explanation.
- `AclEditor.test.tsx::rolls_back_on_conflict` — FR-F003-12: 409 restores entries and shows the stale banner with the diff.
- `AuditLogPage.test.tsx::filters_and_renders_diff` — FR-F003-11: filter by resource renders rows; expanding shows `DiffViewer`.
- `AuditLogPage.test.tsx::member_sees_denied` — FR-F003-11: member context renders the denied state.
- `AuditLogPage.test.tsx::copy_correlation_id_announces` — FR-F003-14: copy button writes to clipboard and announces `Copied`.
- `DiffViewer.test.tsx::exposes_changes_as_text` — NFR-F003-03: additions and removals rendered with text prefixes, not colour only.
- `AuditLogPage.test.tsx::error_banner_with_correlation_id` — NFR-F003-04: 500 shows banner with `correlation_id` and retry.

Evidence: Vitest JUnit under `testing/evidence/F003/frontend/`.
