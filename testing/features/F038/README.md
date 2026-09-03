# F038 — Authentication and MFA harness

Feature-gated tests for `F038`. Keep test code in this directory. The fixture `testing/fixtures/auth.rs` layers a mock OIDC provider, factors, and tokens over the F002 tenant fixture.

- Gate: `F038_FEATURE`
- Targeted: `cargo xtask test-feature F038`
- Full: `cargo xtask test-all`
- Fixture: `AuthFixture::seed(db)` adds `MockOidcServer` (Microsoft and Google claim shapes), a verified TOTP factor with a fixed secret, a software WebAuthn credential, one API token per tenant, and a tenant variant with `mfa_required = true`; clock fixed at `2026-09-03T00:00:00Z`.
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
