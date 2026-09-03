# F029 — Microsoft/Google/Slack harness

Feature-gated tests for `F029`. Keep test code in this directory.

- Gate: `F029_FEATURE`
- Targeted: `cargo xtask test-feature F029`
- Full: `cargo xtask test-all`
- Fixtures: `testing/fixtures/integrations.rs` (tenants A and B, integration-admin, member, one active connection per provider, sheet `Launch plan` with date columns and 50 rows, 1,000-row generator, mock provider servers in `testing/harness/providers/` for Microsoft Graph, Google APIs, and Slack Web API with consent pages and programmable 429 responses, secret manager stub with two key versions, fixed clock `2026-09-03T00:00:00Z`).
- Recorded responses: `api/fixtures/{microsoft,google,slack}/` versioned by provider API date.
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
