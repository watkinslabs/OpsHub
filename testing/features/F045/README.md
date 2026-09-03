# F045 — Documents/folders harness

Feature-gated tests for `F045`. Keep test code in this directory.

- Gate: `F045_FEATURE`
- Targeted: `cargo xtask test-feature F045`
- Full: `cargo xtask test-all`
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
- Fixtures: `testing/fixtures/documents.rs` seeds a 4-folder tree (depth 3) with 25 documents carrying 3 revisions each, plus editor, viewer, guest, link, and foreign-tenant principals; revisions go to an in-memory object store keyed by test ID.
