---
id: T250
type: task
status: planned
parent_epic: E006
parent_feature: F063
parent_story: S125
depends_on: [T249]
owned_paths: [crates/domain/src/entra/**, services/api/src/entra/**, apps/web/src/features/entra/**, testing/features/F063/api/**, testing/features/F063/frontend/**, testing/features/F063/accessibility/**]
feature_flag: F063_FEATURE
branch: t250-oidc-sign-in-and-claims
started_at: null
finished_at: null
---

# T250 — OIDC sign-in and claims

## Identity

- Parent story: `S125` Entra sign-in and directory
- Owner: platform
- Branch: `t250-oidc-sign-in-and-claims`
- Decision references: `docs/architecture-decisions.md` sections 3, 7; `docs/capability-contracts.md` row F063

## Objective

Implement the Microsoft sign-in path — authorize redirect with PKCE, callback validation against the cached JWKS, claim-to-user matching with bounded just-in-time provisioning — issuing a session through F038's existing session service, and the admin and login UI that exposes it as one more option beside the methods a tenant already has.

## Specification

- Owned paths: `crates/domain/src/entra/{sign_in.rs, jwks.rs, matching.rs, state.rs}`; `services/api/src/entra/{handlers_auth.rs, dto.rs}`; `apps/web/src/features/entra/{EntraPage.tsx, ConnectionForm.tsx, RedirectUriField.tsx, TestResultPanel.tsx, CapabilitySwitches.tsx, DisconnectDialog.tsx, MicrosoftSignInButton.tsx, api.ts, hooks.ts, routes.ts}`
- Contract/input: `GET /auth/entra/login?tenant_slug=` builds the authorize URL with `response_type=code`, `code_challenge_method=S256`, `state` stored with `tenant_id` and a 10-minute expiry, `nonce`, and `scope=openid profile email`. `GET /auth/entra/callback?code&state&error?` consumes `state` once.
- Output/behavior: the callback validates `state` binding and expiry, `nonce`, `iss` against the cloud's issuer, `aud` against `client_id`, and the token signature against the JWKS cache with rotation, then matches `email`, or `preferred_username` when `email` is absent, case-insensitively against `users.email` in that tenant. An unmatched claim provisions only when its domain is in `allowed_email_domains` and just-in-time provisioning is on; otherwise `403 denied` with `reason: no_matching_user`. A deactivated or suspended user is `reason: user_inactive`. The `oid` claim is written to `users.external_id`. Success issues a session through F038's session service — no second session store — and writes `entra.signin`; every rejection writes `entra.signin-rejected` and returns `400 invalid` for state, nonce, `iss`, `aud` or signature failures. A suspended F002 tenant and F003 deny rules are evaluated before a session is issued. UI: `/admin/entra` renders the form, the copyable redirect URI, `Test connection` with granted and missing scopes announced in a polite live region, the capability switches and the `Disconnect` dialog naming what stops; `MicrosoftSignInButton` renders on `/login` only when the F038 provider list reports `sign_in` active, carries a text label, and never displaces another method. Query keys `['entra-connection']`; telemetry `entra_connection_saved`, `entra_connection_tested`, `entra_capability_toggled`, `entra_signin_clicked`; icons `Building2`, `KeyRound`, `Unplug` through `apps/web/src/ui/icons.ts`.
- Dependencies: T249 connection row, `graph.rs` and vault; F038 session service and login provider list; F002 tenant state; F003 deny rules; F062 tokens and icons.
- Feature flag: `F063_FEATURE` gates the auth routes and the login button; with the flag off `/login` is unchanged.

## TDD

- Failing test first: `testing/features/F063/api/sign_in_tests.rs::login_redirect_carries_s256_pkce_and_nonce`, `::state_expires_after_ten_minutes`, `::callback_rejects_reused_state`, `::callback_rejects_foreign_tenant_state`, `::callback_rejects_bad_nonce`, `::callback_rejects_unknown_jwks_key`, `::callback_rejects_wrong_aud_and_iss`, `::callback_issues_f038_session_for_matched_user`, `::jwks_rotation_accepts_new_key`, `::callback_writes_signin_rejected_audit`; `testing/features/F063/api/matching_tests.rs::email_match_is_case_insensitive`, `::preferred_username_used_when_email_absent`, `::unmatched_domain_is_denied_no_matching_user`, `::jit_provision_stores_oid_as_external_id`, `::deactivated_user_is_denied_user_inactive`, `::suspended_tenant_cannot_sign_in_through_entra`; `testing/features/F063/frontend/ConnectionForm.test.tsx::shows_field_errors_for_malformed_guid`, `testing/features/F063/frontend/TestResultPanel.test.tsx::lists_missing_scopes_against_capability`, `testing/features/F063/frontend/MicrosoftSignInButton.test.tsx::renders_only_when_sign_in_active`, `::login_page_still_offers_password_and_saml`; `testing/features/F063/accessibility/entra.a11y.spec.ts::admin_entra_has_no_serious_violations`, `::test_result_announced_once`, `::disconnect_dialog_traps_and_returns_focus`
- Targeted command: `cargo xtask test-feature F063`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: mock Entra authority in `testing/harness/providers/entra/` serving authorize, token and JWKS with a rotation fixture and a signing key not in the set; fixed PKCE verifier and nonce; `testing/fixtures/entra.rs` deactivated user, suspended tenant, tenant B; MSW handlers for the React lane

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Auth routes registered behind the flag and the button wired into the F038 login provider list; OpenAPI regenerated without drift
- [ ] Password, TOTP, WebAuthn, generic OIDC and SAML verified still working with Entra enabled and after disconnect
- [ ] axe reports zero serious violations on `/admin/entra` and `/login`
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S125
- [ ] `finished_at` recorded
