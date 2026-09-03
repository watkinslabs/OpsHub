# F050 — Dynamic View harness

Feature-gated tests for `F050`. Keep test code in this directory.

- Gate: `F050_FEATURE` (module entitlement `dynamic-views` must be active in the fixture tenant)
- Targeted: `cargo xtask test-feature F050`
- Full: `cargo xtask test-all`
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
- Fixture: `testing/fixtures/dynamic_views.rs` (tenant A owner, vendor 1, vendor 2, unshared sheet viewer; tenant B; 200-row sheet with `Vendor` person column and `Vendor status` select column; view with `assigned_rows` policy; live and revoked tokens).
