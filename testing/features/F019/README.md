# F019 — Workflow runtime harness

Feature-gated tests for `F019`. Keep test code in this directory.

- Gate: `F019_FEATURE`
- Targeted: `cargo xtask test-feature F019`
- Full: `cargo xtask test-all`
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
- Harness specifics: embedded NATS JetStream per worker, controllable clock with `advance()`, recording executors for notification, approval, webhook, and integration actions; workflow definitions come from `testing/features/F018/fixtures/definitions.rs`.
