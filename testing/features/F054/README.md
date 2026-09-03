# F054 — Bridge harness

Feature-gated tests for `F054`. Keep test code in this directory.

- Gate: `F054_FEATURE`
- Targeted: `cargo xtask test-feature F054`
- Full: `cargo xtask test-all`
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
- Fixture: `testing/fixtures/bridge.rs` (tenant A editor/viewer, tenant B, active `bridge` entitlement with limits, scripted Jira/Slack/Salesforce connector mocks, seeded 5-step flow, 200 historical runs).
