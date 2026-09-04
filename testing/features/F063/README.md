# F063 — Microsoft Entra integration harness

Feature-gated tests for `F063`. Keep test code in this directory.

- Gate: `F063_FEATURE`, off by default; with the gate off `/login`, the F037 channel registry and the worker registry are unchanged.
- Targeted: `cargo xtask test-feature F063`
- Full: `cargo xtask test-all`
- Fixtures: `testing/fixtures/entra.rs` (tenants A and B, an identity-admin, a member, a deactivated user, a suspended tenant, one connection per cloud `global`/`us_gov`/`china`, a mail-capable connection with `sender_mailbox`, 500 directory groups with 50,000 members, manual and directory-sourced group members, a mapped 100-member group whose delta page returns 70).
- Mock provider: `testing/harness/providers/entra/` serves the Entra authority (authorize, token, JWKS with a rotation fixture and an unlisted signing key) and Graph (`organization`, `groups` delta with an expirable token, `users/{sender}/sendMail`) with programmable `429`, `503` and `Retry-After`. No real Microsoft endpoint is contacted in any lane; the F037 channel registry and the F029 vault run in memory.
- Determinism: fixed UUIDv7 seeds, fixed PKCE verifier and nonce, fixed clock `2026-09-03T00:00:00Z` in UTC, one schema and one mock provider port per worker.
- Lanes: `requirements/` (traceability for FR-F063-01..13 and NFR-F063-01..04), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
- Evidence: `testing/evidence/F063/`.
