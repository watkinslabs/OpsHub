# F038 e2e cases

File: `testing/features/F038/e2e/auth.spec.ts`. Playwright over `https://localhost` with the mock OIDC provider and a CDP virtual authenticator. Flag `F038_FEATURE`.

- `login_through_mock_provider_lands_on_return_to` — FR-F038-01, FR-F038-03: open `/w/1` unauthenticated, sign in as `pat@acme.test`, land back on `/w/1` with the session cookie.
- `login_enroll_totp_under_required_policy` — FR-F038-07, FR-F038-10: required-MFA tenant routes to enrolment; scanning the secret and entering the code unlocks the app.
- `register_passkey_and_assert` — FR-F038-08: virtual authenticator registers; sign-out and sign-in asserts the passkey.
- `revoke_session_from_second_context` — FR-F038-06: second browser context revokes the first; first context's next navigation lands on `/login`.
- `create_token_and_call_api` — FR-F038-11, FR-F038-12: create `sheets:read` token, call `GET /api/v1/sessions` with bearer → 200; revoke → 401.
- `unprovisioned_user_sees_reason` — FR-F038-02: provider returns an email not in the tenant; callback page shows `user_not_provisioned`.
- `admin_saves_policy_member_denied` — FR-F038-14: admin enables MFA; member's next request shows the interstitial; member opening `/admin/security-policy` sees denied.

Evidence: Playwright traces and videos under `testing/evidence/F038/e2e/`.
