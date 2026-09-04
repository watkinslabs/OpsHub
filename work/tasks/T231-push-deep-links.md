---
id: T231
type: task
status: planned
parent_epic: E008
parent_feature: F058
parent_story: S116
depends_on: [S116]
owned_paths: [crates/domain/src/mobile/**, crates/persistence/src/mobile/**, services/api/src/mobile/**, apps/web/src/features/mobile/**, testing/features/F058/api/**, testing/features/F058/frontend/**]
feature_flag: F058_FEATURE
branch: t231-push-deep-links
started_at: null
finished_at: null
---

# T231 — Push/deep links

## Identity

- Parent story: `S116` Mobile offline/sync
- Owner: platform
- Branch: `t231-push-deep-links`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 5; `docs/capability-contracts.md` row F058

## Objective

Implement the offline queue, the sync push and pull routes with conflict rejection and replay safety, the signed deep-link resolver, push tap handling, and revoke wipe.

## Specification

- Owned paths: `crates/domain/src/mobile/{sync.rs, conflict.rs, cursor.rs, deeplink.rs, service_sync.rs, wipe_consumer.rs}`, `crates/persistence/src/mobile/{batch_repository.rs, rejection_repository.rs, applied_op_repository.rs}`, `services/api/src/mobile/{handlers_sync.rs, handlers_deeplink.rs}`, `apps/web/src/features/mobile/{queue.ts, sync.ts, crypto.ts, OfflineBar.tsx, QueueBadge.tsx, QueuePage.tsx, ConflictCard.tsx}` and push handlers in `sw.ts`
- Contract/input: `SyncBatchRequest { device_id, batch_id, ops[≤500] }`, `GET /api/v1/mobile/sync?since&limit`, `GET /m/{deep_link}` with `<kind>.<id>.<sig>`; `sign_deep_link(kind, id, tenant_key, expires_at)` exported for the F037 push payload builder; `session.revoked.v1` consumer.
- Output/behavior: `apply_sync_batch` persists the batch and one `mobile_sync_batch_ops` row per op (`op_index` from the `recorded_at` order) with its `mobile_sync_op_values` rows, then runs each op in a savepoint through F008 `grid::apply_cell_edit` or F014 `forms::submit` with sync-time authorization, records applied ops in `mobile_sync_applied_ops`, sets each op's `outcome` and `applied_version`, persists rejections as ordered `mobile_sync_rejections` rows with `server_value` and `server_version`, and publishes `mobile-sync.applied.v1` and `mobile-sync.rejected.v1`; replay rebuilds the identical response from those rows instead of a stored envelope; `pull_changes` reads the F008 change log for the sheets in `mobile_device_sheet_subscriptions` with a signed cursor expiring after 7 days; deep-link resolver verifies signature and expiry, redirects through login, and renders not-found for unreadable targets; client queue encrypts values with a non-extractable WebCrypto key, caps 500 ops or 7 days, pushes then pulls with backoff, renders conflict cards, and wipes on revoke or logout; service worker handles `push` and `notificationclick`.
- Data access: `sync.rs`, `conflict.rs`, `cursor.rs`, `deeplink.rs`, `service_sync.rs`, `wipe_consumer.rs`, and the handlers hold no SQL. `SyncBatchRepository` owns `mobile_sync_batches`, `mobile_sync_batch_ops`, `mobile_sync_op_values` (`insert_batch_with_ops`, `find_batch_by_device_and_batch_id`, `list_ops_in_apply_order`, `list_op_values`, `set_op_outcome`, `purge_batches_before`); `AppliedOpRepository` owns `mobile_sync_applied_ops` (`claim_client_op_ids`, `list_applied_versions_for_batch`); `SyncRejectionRepository` owns `mobile_sync_rejections` (`list_rejections_for_batch`, `list_rejections_for_device`); the device, capability, and subscription tables stay with T229's `MobileDeviceRepository`, which the pull and wipe paths call for `list_sheet_subscriptions`, `advance_device_cursor`, and `revoke_device`. One batch's writes across all five mobile tables and the F008/F014 aggregates run in a single `UnitOfWork` that owns the transaction and the per-op savepoints (decision section 2.1).
- Dependencies: T230 editors feeding the queue; F008 change log and cell service; F014 submit; F037 push payload and read marking; F038 login redirect.
- Feature flag: `F058_FEATURE`

## TDD

- Failing test first: `testing/features/F058/api/sync_tests.rs::sync_applies_ops_in_recorded_order`, `::sync_rejects_conflict_with_server_value`, `::sync_rejects_denied_at_sync_time`, `::sync_rejects_deleted_row_not_found`, `::sync_replay_batch_returns_original`, `::sync_replay_response_rebuilt_from_rows`, `::sync_op_rows_carry_apply_order`, `::sync_batch_501_ops_invalid`, `::pull_returns_changed_and_deleted_rows`, `::pull_uses_subscription_rows`, `::pull_expired_cursor_invalid`; `testing/features/F058/api/deeplink_tests.rs::deep_link_bad_signature_not_found`, `::deep_link_unreadable_row_not_found`; `testing/features/F058/frontend/ConflictCard.test.tsx::conflict_card_keep_mine_resubmits`, `Queue.test.tsx::queue_full_blocks_edits`, `::revoke_wipes_queue_and_key`
- Targeted command: `cargo xtask test-feature F058`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: two users editing the same row; fixed signing key; in-memory push recorder; WebCrypto stub

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Sync and deep-link routes mounted behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S116
- [ ] `finished_at` recorded
