# F041 — Work-item schema harness

Feature-gated tests for `F041`. Keep test code in this directory.

- Gate: `F041_FEATURE`
- Targeted: `cargo xtask test-feature F041`
- Full: `cargo xtask test-all`
- Subject under test: the `xtask` binary built from `automation/xtask` (`backlog.rs`, `support.rs`, `content.rs`), run against scratch repositories under `fixtures/`.
- Lanes: `requirements/` (traceability), `api/` (CLI command tests), `database/` (file-system persistence), `frontend/` (no UI; CLI output), `e2e/` (hooks and CI job), `accessibility/` (CLI output), `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
