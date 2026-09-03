# F018 — Workflow builder harness

Feature-gated tests for `F018`. Keep test code in this directory.

- Gate: `F018_FEATURE`
- Targeted: `cargo xtask test-feature F018`
- Full: `cargo xtask test-all`
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
- Fixtures: `fixtures/definitions.rs` (one workflow per trigger kind plus invalid definitions), `fixtures/generator.rs` (5,000 published workflows, seed `0x0F18`), `fixtures/sample_events.json` (shared with F019).
