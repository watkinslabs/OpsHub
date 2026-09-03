---
id: T032
type: task
status: planned
parent_epic: E002
parent_feature: F008
parent_story: S016
depends_on: [T031]
owned_paths: [testing/features/F008/api/**, testing/features/F008/e2e/**, testing/features/F008/performance/**, testing/features/F008/requirements/**]
feature_flag: F008_FEATURE
branch: t032-conflict-tests
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 4, 9
- Capability contract: `docs/capability-contracts.md` row F008

# T032 — Conflict tests

## Identity

- Parent story: `S016` Bulk operations
- Owner: platform
- Branch: `t032-conflict-tests`
- Decision references: `docs/architecture-decisions.md` sections 2, 4, 9; `docs/capability-contracts.md` row F008

## Objective

Prove concurrent-edit safety, permission boundaries, and scale targets for the grid with a concurrency harness, two-session browser tests, and load tests, and complete the requirements traceability table.

## Specification

- Owned paths: `testing/features/F008/api/{concurrency_tests.rs, permission_tests.rs}`, `testing/features/F008/e2e/grid.spec.ts`, `testing/features/F008/performance/{cell_write_bench.rs, bulk_bench.rs, concurrent_editors.rs, scroll_bench.spec.ts}`, `testing/features/F008/requirements/cases.md`
- Contract/input: the seven F008 routes from T029 and T030; `testing/fixtures/grid.rs` with editor A, editor B, commenter, viewer, foreign tenant; a 100,000-row generator with fixed seed; a 1,000-editor simulator using `tokio` tasks with unique actor IDs.
- Output/behavior: `concurrency_tests.rs` runs 1,000 simulated editors patching disjoint and overlapping cells and asserts no lost update (final raw equals the last applied version's value and every loser received `conflict`), asserts undo across users returns `conflict`, and asserts bulk batches roll back entirely on outbox failure; `permission_tests.rs` asserts viewer and commenter `denied` on every mutation, foreign-tenant `not_found` on every route including history, and that a client-supplied value violating F007 rules is rejected server-side; `grid.spec.ts` drives two browser contexts to reproduce the conflict outline and reload, plus type, paste, fill, undo, layout persistence, and bulk edit; performance lane records p95 for single-cell writes, 5,000-cell bulk time, feed latency, and scroll frame times; `requirements/cases.md` maps FR-F008-01 through FR-F008-16 and NFR-F008-01 through NFR-F008-04 to lanes.
- Dependencies: T031 grid UI for browser lanes; T029 and T030 routes; `testing/harness/load.rs` k6 wrapper from F001.
- Feature flag: `F008_FEATURE` enabled by the harness for every lane.

## TDD

- Failing test first: `testing/features/F008/api/concurrency_tests.rs::thousand_editors_no_lost_updates`, `::overlapping_edits_losers_get_conflict`, `::bulk_rolls_back_on_outbox_failure`; `testing/features/F008/api/permission_tests.rs::viewer_and_commenter_mutations_denied`, `::cross_tenant_all_routes_not_found`, `::server_rejects_client_bypassed_validation`; `testing/features/F008/e2e/grid.spec.ts::two_sessions_conflict_outline_and_reload`, `::layout_persists_after_reload`; `testing/features/F008/performance/concurrent_editors.rs::thousand_editors_p95_under_800ms`
- Targeted command: `cargo xtask test-feature F008`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: real API against a seeded tenant; outbox failure injected through the in-memory publisher's fail-once switch

## Exit criteria

- [ ] Tests written before implementation and observed failing where behavior is missing
- [ ] Concurrency, permission, E2E, and performance lanes pass with evidence under `testing/evidence/F008/`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S016
- [ ] `finished_at` recorded
