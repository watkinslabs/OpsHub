# F034 — Workload/actuals harness

Feature-gated tests for `F034` (workload query, over-allocation conflicts with shift and reassign suggestions, native time entries, external timesheet import with pending reconciliation, audited reconciliation, and planned versus actual effort). Keep test code in this directory.

- Gate: `F034_FEATURE`
- Targeted: `cargo xtask test-feature F034`
- Full: `cargo xtask test-all`
- Fixtures: `testing/fixtures/workload.rs` — tenants A and B, `resource-admin`, `resource-viewer`, two users linked to resources, F033 resources with capacity and Ana over-allocated in the week of 2026-10-12 (16 h available against 22 h allocated), F012 `schedule_results` giving `Design API` 4 days of float, Ben with a matching skill and 12 h remaining, native entries, and a 2,000-entry external timesheet payload with colliding rows; `large_tenant()` scales this to 1,000 resources, 12 weeks, and 40,000 entries for the performance lane.
- Determinism: fixed UUIDv7 seeds, clock `2026-09-03T00:00:00Z`, tenant time zone UTC, in-memory outbox recorder, in-process job runner, one schema per test worker.
- Lanes: `requirements/` (FR-F034-01…14 and NFR-F034-01…04 traceability), `api/` (eight routes plus the conflict detector), `database/` (migration, checks, external-ref uniqueness, reconciliation-immutability trigger, rollback), `frontend/` (heatmap, conflicts panel, time sheet, reconcile queue, effort panel), `e2e/` (shift a conflict, record time, import and reconcile, planned versus actual), `accessibility/` (axe, grid keyboard, meter semantics, dialog focus), `performance/` (read, detection, write, import, and summary-lag budgets). Each `cases.md` names the tests implemented in that lane and the FR/NFR ids they prove.
- Evidence: `testing/evidence/F034/<lane>/`.
