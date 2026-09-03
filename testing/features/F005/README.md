# F005 — Workspace navigation harness

Feature-gated tests for `F005`. Keep test code in this directory.

- Gate: `F005_FEATURE`
- Targeted: `cargo xtask test-feature F005`
- Full: `cargo xtask test-all`
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
- Fixtures: `testing/fixtures/workspaces.rs` (tenant A/B, owner, admin, editor, commenter, viewer, group, non-member, 12-folder tree with one folder deny, 2,000-folder generator).
