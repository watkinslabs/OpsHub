# F048 — Entitlements and feature flags harness

Feature-gated tests for `F048`. Keep test code in this directory.

- Gate: `F048_FEATURE`
- Targeted: `cargo xtask test-feature F048`
- Full: `cargo xtask test-all`
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
- Fixture: `testing/fixtures/entitlements.rs` (tenant A admin/member, tenant B, internal tenant, platform operator, seeded flag registry, `data-shuttle` active, `bridge` trial expired).
