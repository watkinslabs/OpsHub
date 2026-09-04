# F063 frontend cases

File: `testing/features/F063/frontend/{ConnectionForm.test.tsx,RedirectUriField.test.tsx,TestResultPanel.test.tsx,CapabilitySwitches.test.tsx,GroupMapTable.test.tsx,GroupPickerDialog.test.tsx,SyncResultBanner.test.tsx,DisconnectDialog.test.tsx,MicrosoftSignInButton.test.tsx}`. Vitest with MSW. Flag `F063_FEATURE`.

- `shows_field_errors_for_malformed_guid` — FR-F063-02: a non-GUID `client_id` renders the `field_errors.client_id` message and blocks submit.
- `cloud_select_offers_three_clouds` — FR-F063-02: `global`, `us_gov` and `china` are selectable and `global` is the default.
- `redirect_uri_is_copyable_and_read_only` — FR-F063-12: `RedirectUriField` shows the deployment redirect URI with a copy control and no editable input.
- `lists_missing_scopes_against_capability` — FR-F063-03: `missing_scopes: ["GroupMember.Read.All"]` renders against the `Group sync` switch with the consent explanation.
- `capability_switch_disabled_until_consent` — FR-F063-03: a capability with missing scopes cannot be turned on and says which consent is required.
- `disconnected_state_offers_connect` — FR-F063-13: `status: disconnected` renders the explanatory empty state with `Connect` and no mapping table.
- `renders_only_when_sign_in_active` — FR-F063-12: `MicrosoftSignInButton` is absent when `sign_in` is inactive and present with its text label when active.
- `login_page_still_offers_password_and_saml` — FR-F063-01: with the button present, the password form and the SAML option are still rendered.
- `shows_last_counts_and_needs_review_text` — FR-F063-07: `GroupMapTable` shows `Added 24, removed 2`, and a `needs_review` row explains the halted removal in text plus icon.
- `searches_directory_groups` — FR-F063-12: `GroupPickerDialog` queries `['entra-directory-groups', search]` and lists matching directory groups.
- `disconnect_dialog_names_what_stops` — FR-F063-10: the confirmation lists Entra sign-in, group sync and Graph mail stopping and states no user or group is deleted.
- `shows_denied_page_for_non_identity_admin` — FR-F063-11: a non-`identity-admin` loading `/admin/entra` sees the denied state.
- `shows_error_banner_with_correlation_id` — NFR-F063-04: a `502` renders the error-class banner with `correlation_id` and a retry.

Evidence: Vitest JUnit under `testing/evidence/F063/frontend/`.
