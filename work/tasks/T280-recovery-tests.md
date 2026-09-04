---
id: T280
type: task
status: planned
parent_epic: E003
parent_feature: F070
parent_story: S140
depends_on: [S140, T279]
owned_paths: [services/worker/src/trash/**, crates/domain/src/trash/**, testing/features/F070/**]
feature_flag: F070_FEATURE
branch: t280-recovery-tests
started_at: null
finished_at: null
---

# T280 — Recovery tests

## Identity

- Parent story: `S140` Restore and purge
- Owner: platform
- Branch: `t280-recovery-tests`
- Decision references: `docs/architecture-decisions.md` sections 2, 7, 9; `docs/capability-contracts.md` row F070; `docs/threat-model.md` sections 3.4, 3.6 and 5

## Objective

Ship the retention expiry sweep — the last recovery path with no user-visible surface — together with the end-to-end, accessibility and performance evidence that proves recovery, hold precedence and the projection's derivedness across the whole feature.

## Specification

- Owned paths: `services/worker/src/trash/sweep.rs`, `crates/domain/src/trash/sweep.rs`, `testing/features/F070/{requirements,api,database,frontend,e2e,accessibility,performance}/`
- Contract/input: the sweep consumes `jobs.trash.sweep` nightly at 03:00 tenant local with per-tenant quota 1, 3 retries then dead letter; each run takes `{ tenant_id, batch_size }` defaulting to 500.
- Output/behavior: `sweep.rs` reads `TrashEntryRepository::list_expired_batch`, marks entries past `expires_at` as `expired`, consults `LegalHoldPort::is_held` per entry and skips held ones with `state = 'held'` and a recorded held count, hands the remainder to `PurgeExecutorPort` in batches of 500, and hard-deletes nothing itself; an entry whose owning row is no longer soft-deleted is dropped rather than purged. The evidence suite covers the seven lanes: the requirements lane traces every FR-F070 and NFR-F070 id, the e2e lane drives delete-and-restore, the deleted-parent block and its resolution, and a denied purge as an editor, the accessibility lane runs axe on the screen and both dialogs in both themes, and the performance lane asserts the 400 ms p95 first page over 200,000 entries, the 5 s p95 and 120 s p99 projection lag under a 5,000-event burst, and the 3-minute rebuild.
- Data access: `sweep.rs` holds no SQL; it reads and writes through `TrashEntryRepository` and reaches owning tables only through `PurgeExecutorPort` and `TrashTarget::purge` (decision section 2.1).
- Dependencies: T277 for the repository and registry, T278 for the index and restore paths, T279 for the screen and purge route, F027 for holds and the purge executor, F067 fixtures for the 200,000-entry generator.
- Feature flag: `F070_FEATURE` gates the sweep job and selects the suite; the full run enables every flag.

## TDD

- Failing test first: `testing/features/F070/api/sweep_tests.rs::sweep_marks_expired_and_hands_batch_to_executor`, `::sweep_skips_held_entry_and_counts_it`, `::sweep_never_hard_deletes_directly`, `::sweep_drops_entry_whose_row_was_restored`, `::sweep_resumes_after_worker_restart_without_double_purge`; `testing/features/F070/e2e/trash.spec.ts::delete_sheet_and_restore_it`, `::restore_parent_then_child`, `::editor_cannot_purge`; `testing/features/F070/accessibility/trash.a11y.spec.ts::trash_page_has_no_serious_axe_violations`, `::state_is_not_colour_only`; `testing/features/F070/performance/trash_bench.rs::first_page_p95_under_400ms_over_200k_entries`, `::projection_lag_within_bounds_under_burst`, `::rebuild_200k_entries_under_3_minutes`
- Targeted command: `cargo xtask test-feature F070`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/trash.rs`; a 200,000-entry generator, a held-document fixture, a `PurgeExecutorPort` spy, a fixed clock advanced past `expires_at`, and one JetStream subject prefix per worker

## Exit criteria

- [ ] Tests written before implementation and observed failing, with a positive control per new gate: known defect, RED, restore, GREEN
- [ ] Sweep registered in `services/worker/src/registry.rs` behind the flag
- [ ] All seven lanes present and passing in targeted and full modes; evidence under `testing/evidence/F070/`
- [ ] Rebuild equivalence result recorded as evidence
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S140
- [ ] `finished_at` recorded
