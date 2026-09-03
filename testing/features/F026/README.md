# F026 — SSO/SCIM harness

Feature-gated tests for `F026`. Keep test code in this directory.

- Gate: `F026_FEATURE`
- Targeted: `cargo xtask test-feature F026`
- Full: `cargo xtask test-all`
- Fixtures: `testing/fixtures/sso.rs` (tenants A and B, tenant-admin, member, active SAML connection with two certificates, SCIM token, three groups, stub IdP signer with RSA-2048 and P-256 keys, Microsoft and Google assertion shapes, fixed clock `2026-09-03T00:00:00Z`).
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
