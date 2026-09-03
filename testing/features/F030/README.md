# F030 — Jira/Salesforce/files harness

Feature-gated tests for `F030`, the general connector framework: sync definitions, field mappings and transforms, cursor and checkpoint state, error classification and retry, run history, replay, and the conflict queue. Keep test code in this directory.

- Gate: `F030_FEATURE`
- Targeted: `cargo xtask test-feature F030`
- Full: `cargo xtask test-all`
- Fixtures: `testing/fixtures/connectors.rs` (tenants A and B, an integration-admin, a member, an admin without edit rights on the target sheet, one F029 active connection per connector, sheet `Delivery board` with text, date, single-select, person, checkbox, and attachment columns, syncs in `paused`, `active`, and `error` states, a partial run with 40 failed records out of 500, three open conflicts, 10,000-record Jira and Salesforce generators, a Box folder of 20 files including an EICAR sample, a read-only PostgreSQL fixture database, fixed clock `2026-09-03T00:00:00Z`, and a deterministic backoff jitter seed).
- Mock connectors: `testing/harness/connectors/` for Jira REST v3, Salesforce v61.0 (`getUpdated`, `getDeleted`, composite), Box 2.0 events, Dropbox v2 `list_folder`, and Tableau REST 3.21 publish, each with programmable page sizes, clock skew, mid-page disconnects, and injectable 429/503 responses; the F029 `TokenSource` stub supplies tokens so no OAuth flow runs here.
- Recorded responses: `api/fixtures/{jira,salesforce,box,dropbox,tableau}/` versioned by the pinned connector API version.
- Lanes: `requirements/` (traceability for FR-F030-01..21 and NFR-F030-01..05), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
