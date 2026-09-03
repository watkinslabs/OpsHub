---
id: T150
type: task
status: planned
parent_epic: E001
parent_feature: F038
parent_story: S075
depends_on: [T149]
owned_paths: [crates/domain/src/auth/**, services/api/src/auth/**, apps/web/src/features/auth/**, testing/features/F038/api/**, testing/features/F038/frontend/**, testing/features/F038/accessibility/**]
feature_flag: F038_FEATURE
branch: t150-webauthn-totp
started_at: null
finished_at: null
---

# T150 — WebAuthn/TOTP

## Identity

- Parent story: `S075` OIDC login and sessions
- Owner: platform
- Branch: `t150-webauthn-totp`

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 4, 6
- Canonical contract: `docs/capability-contracts.md` row F038

## Objective

Implement TOTP and WebAuthn factor enrolment, verification, and removal with the five MFA routes, and the login, callback, and security-settings pages that drive sessions and factors.

## Specification

- Owned paths: `crates/domain/src/auth/{factor.rs, totp.rs, webauthn.rs, service_mfa.rs}`, `services/api/src/auth/handlers_mfa.rs`, `apps/web/src/features/auth/{LoginPage.tsx, TenantSlugForm.tsx, CallbackPage.tsx, MfaInterstitial.tsx, SecuritySettingsPage.tsx, SessionsList.tsx, RevokeSessionDialog.tsx, MfaEnrollTotpDialog.tsx, MfaWebAuthnButton.tsx, FactorsList.tsx, AuthProvider.tsx, api.ts, hooks.ts, routes.ts}`
- Contract/input: `TotpVerifyRequest { factor_id, code: 6 digits }`, `WebAuthnRegisterRequest` (first call empty, second call `{ challenge_id, attestation }`), `WebAuthnAssertRequest { challenge_id, assertion }`; RP id and origin from `RuntimeConfig`; challenges stored 5 minutes in `mfa_factors` pending rows.
- Output/behavior: routes `POST /api/v1/mfa/totp/enroll`, `POST /api/v1/mfa/totp/verify`, `POST /api/v1/mfa/webauthn/register`, `POST /api/v1/mfa/webauthn/assert`, `DELETE /api/v1/mfa/factors/{id}`; TOTP RFC 6238 SHA-1 30 s window ±1 step, secret envelope-encrypted with `SecretCipher`; WebAuthn verifies origin, RP id hash, user presence, and strictly increasing `sign_count`; 5-factor cap and last-factor rule; sets `sessions.mfa_verified_at`; events `mfa.enrolled.v1`, `mfa.removed.v1`; pages implement the flows and states from ticket section 3 including the QR code with copyable secret and the `AuthProvider` refresh-once retry.
- Dependencies: T149 session store, extractor, routes, and migration; F001 web shell.
- Feature flag: `F038_FEATURE` gates routes and the `/login` route registration.

## TDD

- Failing test first: `testing/features/F038/api/mfa_tests.rs::totp_enroll_returns_secret_once`, `::totp_verify_within_one_step`, `::totp_verify_two_steps_off_invalid`, `::webauthn_register_and_assert_sets_mfa_verified`, `::webauthn_counter_replay_rejected`, `::sixth_factor_rejected`, `::last_factor_removal_under_required_policy_invalid`; `testing/features/F038/frontend/MfaEnrollTotpDialog.test.tsx::shows_qr_and_copyable_secret`, `LoginPage.test.tsx::redirects_to_provider_with_return_to`, `SessionsList.test.tsx::marks_current_session`; `testing/features/F038/accessibility/auth.a11y.spec.ts::login_page_keyboard_and_axe`
- Targeted command: `cargo xtask test-feature F038`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: fixed TOTP secret and clock; software authenticator with deterministic key pair; MSW handlers

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] MFA routes mounted behind the flag; pages registered in `routes.ts`; OpenAPI regenerated
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S075
- [ ] `finished_at` recorded
