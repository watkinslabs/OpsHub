# F051 — WorkApps harness

Feature-gated tests for `F051`. Keep test code in this directory.

- Gate: `F051_FEATURE` (module entitlement `workapps` must be active in the fixture tenant)
- Targeted: `cargo xtask test-feature F051`
- Full: `cargo xtask test-all`
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
- Fixture: `testing/fixtures/workapps.rs` (tenant A app admin, procurement user, vendor user in group `Vendors`, no-role member; tenant B; one sheet, draft and published forms, report, dashboard, dynamic view; app `vendor-onboarding` with four pages and roles `Procurement` and `Vendor`; `large_app` with 50 pages and 20 roles).
