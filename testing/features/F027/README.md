# F027 — Governance/compliance harness

Feature-gated tests for `F027`. Keep test code in this directory.

- Gate: `F027_FEATURE`
- Targeted: `cargo xtask test-feature F027`
- Full: `cargo xtask test-all`
- Fixtures: `testing/fixtures/compliance.rs` (tenants A and B, two compliance-admins and one tenant-admin each, 12,400 soft-deleted rows of mixed ages with 310 under hold, 40 principals including 3 stale guests, fixture secrets for redaction checks, MinIO bucket prefix per test, fixed clock `2026-09-03T00:00:00Z`).
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
