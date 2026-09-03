# F046 — Live collaboration harness

Feature-gated tests for `F046`. Keep test code in this directory.

- Gate: `F046_FEATURE`
- Targeted: `cargo xtask test-feature F046`
- Full: `cargo xtask test-all`
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
- Harness specifics: WebSocket test client `testing/harness/ws.rs`, two in-process realtime nodes with embedded JetStream, controllable clock for lease expiry, deterministic Automerge change corpus in `fixtures/change_corpus.rs`, load generator in `fixtures/load_generator.rs`.
