# F036 frontend cases

File: `testing/features/F036/frontend/{ShareDialog.test.tsx,AddPeopleSearch.test.tsx,LinkSection.test.tsx,PublicShareLanding.test.tsx}`. Vitest with MSW. Flag `F036_FEATURE`.

- `ShareDialog.test.tsx::renders_direct_then_inherited_grants` — FR-F036-05, FR-F036-14: seeded sheet shows `dana` viewer as direct and `Contractors` editor labelled `Inherited from Ops` with disabled controls.
- `ShareDialog.test.tsx::shows_loading_skeleton_then_people` — FR-F036-14: pending query shows skeleton rows.
- `ShareDialog.test.tsx::shows_empty_state_only_you` — FR-F036-14: single owner grant shows `Only you have access`.
- `ShareDialog.test.tsx::shows_error_banner_with_correlation_id` — NFR-F036-04: 500 response shows banner with `correlation_id` and retry.
- `ShareDialog.test.tsx::share_dialog_role_change_rolls_back_on_conflict` — FR-F036-02: role select applies optimistically; 409 restores the prior role and shows the stale banner.
- `ShareDialog.test.tsx::editor_sees_read_only_list` — FR-F036-15: `canShare=false` hides add, role, and revoke controls and shows the owners-only message.
- `ShareDialog.test.tsx::last_owner_error_shown_inline` — FR-F036-03: 409 `last_owner` renders `Add another owner before removing this one`.
- `ShareDialog.test.tsx::deny_option_visible_only_to_admin` — FR-F036-04: `isAdmin=false` hides `Deny`; admin selecting it sends `effect: deny` and emits `share_denied_set`.
- `AddPeopleSearch.test.tsx::search_lists_users_and_groups_max_20` — FR-F036-01: query `co` lists `Contractors` and users, capped at 20, tenant-scoped.
- `AddPeopleSearch.test.tsx::selecting_person_creates_grant_with_default_viewer` — FR-F036-01: selection calls `createShare` with `role: viewer`, `effect: allow`.
- `LinkSection.test.tsx::create_link_rejects_expiry_over_30_days` — FR-F036-09: date picker caps at +30 days and shows `max_30_days` from the API.
- `LinkSection.test.tsx::copy_link_announces_and_hides_url_after_close` — FR-F036-14, NFR-F036-03: `Copy link` writes to the clipboard, live region says `Link copied`, reopening the dialog shows no URL.
- `LinkSection.test.tsx::revoke_link_removes_row_and_restores_on_error` — FR-F036-10: revoke removes the row; 500 restores it with an error toast.
- `LinkSection.test.tsx::guest_invite_form_limits_roles_and_days` — FR-F036-06: role select lacks owner and admin; days input caps at 14.
- `PublicShareLanding.test.tsx::renders_target_without_navigation` — FR-F036-12: landing renders the sheet grid read-only with the expiry banner and no workspace navigation, search, or `Share` button.
- `PublicShareLanding.test.tsx::revoked_link_shows_not_found_message` — FR-F036-10: 404 renders `This link is no longer valid`.
- `PublicShareLanding.test.tsx::scoped_token_kept_in_memory_only` — NFR-F036-02: no `localStorage` or cookie write after resolution.

Evidence: Vitest JUnit under `testing/evidence/F036/frontend/`.
