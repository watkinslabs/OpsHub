# F020 — Approvals and escalation harness

Feature-gated tests for `F020`. Keep test code in this directory.

- Gate: `F020_FEATURE`
- Targeted: `cargo xtask test-feature F020`
- Full: `cargo xtask test-all`
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
- Harness specifics: controllable clock with `advance()` for timers, in-memory F037 notification recorder, manager relation stub from `testing/fixtures/approvals.rs`, policies `fast-track` (escalate after 15 min) and `standard` (escalate to manager after 60 min, max 2).
