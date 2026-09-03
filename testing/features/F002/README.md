# F002 — Tenant, users, and groups harness

Feature-gated tests for `F002`. Keep test code in this directory; the shared fixture `testing/fixtures/tenants.rs` is documented here and reused by F038, F003, and every later feature.

- Gate: `F002_FEATURE`
- Targeted: `cargo xtask test-feature F002`
- Full: `cargo xtask test-all`
- Fixture: `TenantFixture::seed(db)` builds tenants A and B, admins, members, an invited and a deactivated user, and three groups per tenant with fixed UUIDv7 seeds and clock `2026-09-03T00:00:00Z`.
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
