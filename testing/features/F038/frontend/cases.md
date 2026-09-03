# F038 frontend cases

File: `testing/features/F038/frontend/{LoginPage.test.tsx,CallbackPage.test.tsx,SessionsList.test.tsx,MfaEnrollTotpDialog.test.tsx,CreateApiTokenDialog.test.tsx,SecurityPolicyForm.test.tsx,AuthProvider.test.tsx}`. Vitest with MSW. Flag `F038_FEATURE`.

- `LoginPage.test.tsx::redirects_to_provider_with_return_to` — FR-F038-01: slug submit navigates to `/auth/oidc/start?tenant=acme&return_to=/w/1`.
- `LoginPage.test.tsx::offline_disables_sign_in` — NFR-F038-03: `navigator.onLine=false` disables the button with the offline badge.
- `CallbackPage.test.tsx::shows_reason_and_correlation_on_error` — FR-F038-02: `user_not_provisioned` renders reason text, `correlation_id`, and `Try again`.
- `AuthProvider.test.tsx::retries_once_through_refresh_then_redirects` — FR-F038-04: 401 → `POST /auth/refresh` → retry; second 401 → `/login`.
- `AuthProvider.test.tsx::mfa_required_routes_to_interstitial` — FR-F038-10: 403 `mfa_required` renders `MfaInterstitial` linking to `/settings/security?enroll=1`.
- `SessionsList.test.tsx::marks_current_session` — FR-F038-06: current session shows the `This device` label and no revoke button.
- `SessionsList.test.tsx::revoke_confirms_and_removes_row` — FR-F038-06: confirm dialog names the device; row disappears after 204.
- `MfaEnrollTotpDialog.test.tsx::shows_qr_and_copyable_secret` — FR-F038-07, NFR-F038-03: QR image has `alt`; secret shown in monospace with copy button.
- `MfaEnrollTotpDialog.test.tsx::six_digit_input_paste_and_error` — FR-F038-07: paste fills six cells; 400 shows `field_errors.code`.
- `FactorsList.test.tsx::last_factor_remove_disabled_under_policy` — FR-F038-09: required policy disables remove on the only factor with explanation.
- `CreateApiTokenDialog.test.tsx::reveals_token_once_with_copy` — FR-F038-11: token panel shown once; reopening the list never shows plaintext.
- `SecurityPolicyForm.test.tsx::validates_ranges_and_stale_version` — FR-F038-14: 100 seconds blocks submit; 409 shows the reload banner.
- `SecurityPolicyForm.test.tsx::member_sees_denied` — FR-F038-14: member context renders the denied state.

Evidence: Vitest JUnit under `testing/evidence/F038/frontend/`.
