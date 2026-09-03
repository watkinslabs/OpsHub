# F040 — AI insights/automation harness

Feature-gated tests for `F040`. Keep test code in this directory.

- Gate: `F040_FEATURE`
- Targeted: `cargo xtask test-feature F040`
- Full: `cargo xtask test-all`
- Fixtures: `testing/fixtures/ai_insights.rs` (tenants A and B, a program manager with `workflow-editor`, a viewer, a service-token principal, the F048 `ai_insights` entitlement, sheet `Launch plan` with 200 rows of which 12 slip within 7 days and 8 have been quiet for 14 days and 30 have a null required column, 8 ISO weeks of completion history, 3 over-allocated resources, 5 approvals pending over 3 days, one private sheet readable only by the manager, a 20,000-row generator, a tenant whose monthly AI ceiling has 100 micros remaining, fixed clock `2026-09-03T00:00:00Z`, prompt version `v7`).
- Provider stub: the F039 boundary stub at `testing/harness/ai/provider_stub.rs` with narrations keyed by candidate hash, forced consecutive errors for the circuit breaker, token accounting, and an echo mode that relays injected instructions verbatim.
- Target recorders: F008 row update, F018 workflow draft, F020 approval, F037 notification — all in-process, asserting that a proposal writes nothing and a confirmed run writes exactly its targets.
- Injection corpus: `api/fixtures/injection/{exfiltration,escalation,allowlist,fabrication,markup,schema_break}.json`, 40 payloads carried in row text, comment bodies, column names, file names, approval notes, and workflow step names.
- Lanes: `requirements/` (traceability for every FR-F040 and NFR-F040 id), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the requirement ids they prove.
- Evidence: `testing/evidence/F040/` holds JUnit output, provider stub transcripts, migration and `EXPLAIN` logs, axe JSON, criterion summaries, and the red-team positive-control record.
