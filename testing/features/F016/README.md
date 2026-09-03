# F016 — Comments and activity harness

Feature-gated tests for `F016`. Keep test code in this directory.

- Gate: `F016_FEATURE`
- Targeted: `cargo xtask test-feature F016`
- Full: `cargo xtask test-all`
- Fixture: `testing/fixtures/comments.rs` (tenant A with sheet, row "Kickoff", users `ana` commenter, `dana` commenter, `vic` viewer, `adm` resource-admin, group `ops`; tenant B foreign user; seeded row with 5 threads and 40 comments)
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
- Consumers under test: the activity projector uses the embedded JetStream from `testing/harness/nats.rs`; `mention.created.v1` payloads are asserted against the F037 consumer stub.
