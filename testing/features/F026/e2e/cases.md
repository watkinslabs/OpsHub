# F026 e2e cases

File: `testing/features/F026/e2e/sso.spec.ts`. Playwright against seeded tenant with the harness stub IdP at `/testing/idp`. Flag `F026_FEATURE`.

- `configure_connection_and_login_via_idp` — FR-F026-01, FR-F026-05, FR-F026-07, FR-F026-16: admin creates connection for `example.com`, tests, activates; Ana enters her email on the login page, is redirected to the stub IdP, returns with a session, lands on her workspace.
- `expired_assertion_shows_error_page` — FR-F026-04: stub IdP issues an assertion 10 minutes old; browser lands on `/auth/saml/error?code=expired` with the correlation ID.
- `scim_suspend_transfers_sheet_owner` — FR-F026-11: API client patches Ben `active: false`; Ben's open session is logged out on next navigation; Ana's sheet list shows Ben's sheet with Ana as owner.
- `rotate_certificate_without_downtime` — FR-F026-06: admin adds the new certificate, stub IdP switches keys, login still succeeds, admin retires the old certificate.
- `group_mapping_grants_admin_role` — FR-F026-14: admin maps `opshub-admins`; SCIM adds Ana; Ana reloads and sees the admin navigation.
- `member_cannot_open_sso_admin` — NFR-F026-02: member visits `/admin/sso` and sees the denied page.

Evidence: Playwright traces and videos under `testing/evidence/F026/e2e/`.
