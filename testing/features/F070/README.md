# F070 — Trash and recovery harness

Feature-gated tests for `F070`. Keep test code in this directory.

- Gate: `F070_FEATURE`
- Targeted: `cargo xtask test-feature F070`
- Full: `cargo xtask test-all`
- Fixtures: `testing/fixtures/trash.rs` (tenants A and B; an editor; a member with no access to workspace `Procurement`; a compliance administrator; the three live kinds `sheet`, `row` and `folder` plus an in-memory test-double kind; a deleted sheet `Cutover plan` with 40 rows; a deleted folder `Procurement` holding the deleted sheet `Vendor scorecard`; a deleted document under an active legal hold; a 200,000-entry generator; fixed clock `2026-09-03T00:00:00Z`).
- Ports under test as doubles: `TrashTarget` recording restore and purge calls, `LegalHoldPort` with a programmable held set, `RetentionPolicyPort` returning 30 days and null, and a `PurgeExecutorPort` spy that fails a test if a purge bypassed the shared F027 path.
- Event scripts: `api/fixtures/streams/` holds the declared out-of-order permutations the projector must survive — replayed deletion, restoration before deletion, and a lower `version` after a higher one.
- Lanes: `requirements/` (traceability for every FR and NFR id), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the ids they prove.
- The load-bearing case is `rebuild_matches_incremental_projection`: it is what keeps `trash_entries` a projection rather than a second source of truth, and it must never be skipped.
