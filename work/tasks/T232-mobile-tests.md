---
id: T232
type: task
status: planned
parent_epic: E008
parent_feature: F058
parent_story: S116
depends_on: [T231]
owned_paths: [testing/features/F058/e2e/**, testing/features/F058/accessibility/**, testing/features/F058/performance/**, testing/features/F058/api/**]
feature_flag: F058_FEATURE
branch: t232-mobile-tests
started_at: null
finished_at: null
---

# T232 — Mobile tests

## Identity

- Parent story: `S116` Mobile offline/sync
- Owner: platform
- Branch: `t232-mobile-tests`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 9; `docs/capability-contracts.md` row F058

## Objective

Prove the install, offline, reconnect, conflict, push, and wipe flows on emulated devices with accessibility and performance evidence.

## Specification

- Owned paths: `testing/features/F058/e2e/mobile.spec.ts`, `testing/features/F058/e2e/push.spec.ts`, `testing/features/F058/accessibility/mobile.a11y.spec.ts`, `testing/features/F058/performance/sync_bench.rs`, `testing/features/F058/api/concurrency_tests.rs`, `testing/features/F058/api/constraint_tests.rs`
- Contract/input: Playwright Pixel 7 emulation with `context.setOffline`, a second desktop session editing the same row, the in-memory push recorder exposing the delivered payload, and a 100-op batch generator.
- Output/behavior: E2E covers install prompt, offline edits and form submission with queue badge, reconnect drain, conflict card resolution both ways, push tap opening the row, logout wipe, and lost-permission rejection; concurrency test sends the same batch from two connections and asserts one application; axe reports zero serious violations with 44 px targets; performance lane records 100-op batch p95 (< 2 s), 500-row pull p95 (< 500 ms), and cached shell load (< 1.5 s).
- Data access: no test opens a connection or issues SQL of its own; every fixture write and every assertion goes through the `crates/persistence/src/mobile/` repositories (`MobileDeviceRepository`, `SyncBatchRepository`, `AppliedOpRepository`, `SyncRejectionRepository`) and the F008/F014 repositories, and `api/constraint_tests.rs` drives the database constraints on the new child tables directly through those repositories, asserting the rejection each constraint produces (decision section 2.1).
- Dependencies: T231 complete; Playwright device emulation and push recorder from `testing/harness/`.
- Feature flag: `F058_FEATURE`

## TDD

- Failing test first: `testing/features/F058/e2e/mobile.spec.ts::install_edit_offline_reconnect_syncs`, `::conflict_card_keep_mine_and_take_theirs`, `::lost_permission_rejected_at_sync`, `::logout_wipes_queue_and_cache`; `testing/features/F058/e2e/push.spec.ts::push_tap_opens_row_and_marks_read`; `testing/features/F058/api/concurrency_tests.rs::same_batch_from_two_connections_applies_once`; `testing/features/F058/api/constraint_tests.rs::device_capability_row_unique`, `::sheet_subscription_row_unique`, `::batch_op_index_unique_per_batch`, `::batch_op_client_op_id_unique_per_batch`, `::cell_edit_op_requires_sheet_and_row_target`, `::form_submit_op_rejects_sheet_target`, `::op_value_requires_exactly_one_field_reference`, `::op_value_unique_per_field`, `::rejection_code_check_rejects_unknown_code`, `::rejection_index_unique_per_batch`, `::applied_op_unique_per_device`, `::batch_purge_cascades_ops_values_and_rejections`; `testing/features/F058/accessibility/mobile.a11y.spec.ts::mobile_pages_have_no_serious_axe_violations`; `testing/features/F058/performance/sync_bench.rs::sync_batch_100_ops_p95`, `::pull_500_rows_p95`, `::shell_load_from_cache_under_1500ms`
- Targeted command: `cargo xtask test-feature F058`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: seeded tenant with two users; Playwright against the real API; push recorder; batch generator with fixed seed

## Exit criteria

- [ ] E2E, concurrency, constraint, accessibility, and performance lanes pass in targeted and full modes
- [ ] p95 targets from NFR-F058-01 recorded under `testing/evidence/F058/performance/`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S116
- [ ] `finished_at` recorded
