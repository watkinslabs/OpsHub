# F042 — xtask audit/gates harness

Feature-gated tests for `F042`. Keep test code in this directory.

- Gate: `F042_FEATURE`
- Targeted: `cargo xtask test-feature F042`
- Full: `cargo xtask test-all`
- Subject under test: `automation/xtask/src/policy.rs` through the `xtask` binary, plus the `.githooks/*` scripts, exercised in scratch git repositories with a bare remote. Blocked tokens are generated from character arrays at test time so no fixture file contains one.
- Lanes: `requirements/` (traceability), `api/` (CLI command tests), `database/` (git index and hook persistence), `frontend/` (no UI; CLI output), `e2e/` (real hooks and CI scripts), `accessibility/` (masked, plain output), `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
