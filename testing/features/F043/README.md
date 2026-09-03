# F043 — Fanout orchestration harness

Feature-gated tests for `F043`. Keep test code in this directory.

- Gate: `F043_FEATURE`
- Targeted: `cargo xtask test-feature F043`
- Full: `cargo xtask test-all`
- Subject under test: `automation/xtask/src/lanes.rs` through the `xtask` binary, exercised in scratch git repositories that have a `main` branch, a bare `origin`, a `work/` tree from `fixtures/graph`, and artifact samples from `fixtures/artifacts`. `XTASK_NOW` and `XTASK_OWNER` are fixed.
- Lanes: `requirements/` (traceability), `api/` (CLI command tests), `database/` (lane-file, slot, evidence persistence), `frontend/` (no UI; CLI output), `e2e/` (two concurrent lanes end to end), `accessibility/` (eval-safe plain output), `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
