# F028 — API/webhooks harness

Feature-gated tests for `F028`. Keep test code in this directory.

- Gate: `F028_FEATURE`
- Targeted: `cargo xtask test-feature F028`
- Full: `cargo xtask test-all`
- Fixtures: `testing/fixtures/public_api.rs` (tenants A and B, tenant-admin, member, one application with `rows:read` and `rows:write` limited to 60 requests per minute, one webhook per tenant, 120 seeded deliveries in mixed states, harness HTTP receiver with 200/500/hang modes and a rebinding DNS stub, fixed webhook secret for signature vectors, fixed clock `2026-09-03T00:00:00Z`).
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
