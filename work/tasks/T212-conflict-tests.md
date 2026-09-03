---
id: T212
type: task
status: planned
parent_epic: E008
parent_feature: F053
parent_story: S106
depends_on: [T211]
owned_paths: [testing/features/F053/**]
feature_flag: F053_FEATURE
branch: t212-conflict-tests
started_at: null
finished_at: null
---

# T212 — Conflict tests

## Identity

- Parent story: `S106` Controlled sync
- Owner: platform
- Branch: `t212-conflict-tests`
- Decision references: `docs/architecture-decisions.md` sections 7, 9; `docs/capability-contracts.md` row F053

## Objective

Complete the F053 harness with the E2E, accessibility, performance, and concurrency/conflict suites so every FR/NFR in the ticket has executable evidence before acceptance.

## Specification

- Owned paths: `testing/features/F053/e2e/datamesh.spec.ts`, `testing/features/F053/accessibility/datamesh.a11y.spec.ts`, `testing/features/F053/performance/{preview_bench.rs, sync_bench.rs, conflicts_bench.rs}`, `testing/features/F053/api/concurrency_tests.rs`, `testing/features/F053/requirements/cases.md` (final traceability), `testing/features/F053/README.md`
- Contract/input: seeded tenant A (data-admin, editor, viewer), tenant B without entitlement, `Vendors master` and `Purchase requests` sheets, one mapping with a completed run and two open conflicts, 10,000-changed-row and 100,000-row generators; Playwright sessions per role; two worker instances for the exactly-once run test.
- Output/behavior: E2E covers create mapping → preview → sync → provenance link visible in the target grid → conflict resolved → on-change sync after editing the source; concurrency suite proves two workers process one run exactly once, concurrent edits on both sides during a run become `both_changed` conflicts rather than overwrites, a resolve racing a row edit is rejected, and a bidirectional loop terminates because own writes are ignored; accessibility covers axe on editor, preview, conflicts, keyboard resolve, and marker text; performance covers 100k × 100k preview under 30 s, 10,000-row sync under 2 minutes, conflicts list p95 under 500 ms with 5,000 open conflicts; the requirements table maps FR-F053-01..14 and NFR-F053-01..04 to case IDs with lanes.
- Dependencies: T211 UI, routes, and worker; F004 compose profile with JetStream and a two-worker option.
- Feature flag: `F053_FEATURE` on for the suite; one E2E case runs with the flag off and asserts the navigation entry is absent, routes 404, and the listener does not fire.

## TDD

- Failing test first: `testing/features/F053/e2e/datamesh.spec.ts::create_mapping_preview_sync_resolve`, `::on_change_sync_after_source_edit`, `::provenance_link_visible_in_target_grid`, `::viewer_sees_read_only_tabs`, `::flag_off_hides_module`; `testing/features/F053/api/concurrency_tests.rs::two_workers_process_run_once`, `::edit_during_run_becomes_conflict_not_overwrite`, `::bidirectional_loop_terminates`; `testing/features/F053/accessibility/datamesh.a11y.spec.ts::pages_have_no_serious_axe_violations`; `testing/features/F053/performance/sync_bench.rs::sync_10k_changed_rows_under_2_minutes`
- Targeted command: `cargo xtask test-feature F053`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: Playwright against the real API; k6 script for the conflicts list; generators with deterministic seeds; two-worker compose profile

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] E2E, accessibility, performance, and concurrency lanes pass; evidence stored under `testing/evidence/F053/`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S106
- [ ] `finished_at` recorded
