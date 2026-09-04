---
id: S116
type: story
status: planned
parent_epic: E008
parent_feature: F058
depends_on: [S115]
owned_paths: [crates/domain/src/mobile/**, crates/persistence/src/mobile/**, services/api/src/mobile/**, apps/web/src/features/mobile/**, testing/features/F058/**]
feature_flag: F058_FEATURE
branch: s116-mobile-offline-sync
started_at: null
finished_at: null
---

# S116 — Mobile offline/sync

## Identity

- Parent feature: `F058` Mobile clients
- Owner: platform
- Branch: `s116-mobile-offline-sync`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 5, 6; `docs/capability-contracts.md` row F058

## Vertical slice

As a field user with unreliable connectivity, I want my edits and form submissions queued offline, applied safely on reconnect with visible conflicts, and push notifications that deep-link to the exact row, so that no work is lost or silently overwritten.

## Requirements

- **SR-S116-01:** `queue.ts` stores cell edits and form submissions in encrypted IndexedDB keyed by `client_op_id`, capped at 500 ops or 7 days, and shows the `Queue full` state beyond the cap (FR-F058-03, FR-F058-11).
- **SR-S116-02:** `POST /api/v1/mobile/sync` persists the batch and its ops through `SyncBatchRepository::insert_batch_with_ops` — one `mobile_sync_batch_ops` row per op with `op_index` fixing `recorded_at` order and `mobile_sync_op_values` rows per edited cell or form field — then applies ops in `op_index` order with per-op savepoints inside one `UnitOfWork`, authorizes each op at sync time, returns the unchanged `applied` and `rejected` arrays with codes `conflict|denied|not_found`, records outcomes on the op rows, writes `mobile_sync_applied_ops` and `mobile_sync_rejections` rows through `AppliedOpRepository` and `SyncRejectionRepository`, and publishes `mobile-sync.applied.v1` once and `mobile-sync.rejected.v1` per rejection (FR-F058-04, FR-F058-05, FR-F058-13).
- **SR-S116-03:** Replaying a `batch_id` or an applied `client_op_id` returns the original response without re-applying; the response is rebuilt by `list_ops_in_apply_order`, `list_applied_versions_for_batch`, and `list_rejections_for_batch` rather than read from a stored envelope, and is byte-identical including `cursor` (FR-F058-06).
- **SR-S116-04:** `GET /api/v1/mobile/sync?since={cursor}` returns changed and deleted rows with `limit` ≤ 500 for the sheets in `mobile_device_sheet_subscriptions`, read by `MobileDeviceRepository::list_sheet_subscriptions` and joined to the F008 change log through F008's change-log repository; an expired cursor returns `invalid` with `field_errors.since = "expired"` (FR-F058-07).
- **SR-S116-05:** `sync.ts` pushes then pulls on reconnect with backoff 1 s to 60 s; `ConflictCard` shows local and server values with `Keep mine` and `Take theirs`; unresolved conflicts stay visible (FR-F058-08).
- **SR-S116-06:** `GET /m/{deep_link}` verifies the signature, redirects unauthenticated users through login, and routes to row, sheet, form, or notification; the service worker `notificationclick` opens the deep link and marks the notification read (FR-F058-09, FR-F058-10).
- **SR-S116-07:** `session.revoked.v1` or logout wipes queue, cache, and key within 5 s of network contact, and the wipe consumer revokes the device and cascades its capability and sheet-subscription rows through `MobileDeviceRepository::revoke_device`; a 100-op batch applies under 2 s p95 and a 500-row pull under 500 ms p95 (FR-F058-11, NFR-F058-01, NFR-F058-02).

## Surfaces

- Infrastructure/container: none new
- Data access: `crates/persistence/src/mobile/{batch_repository.rs, rejection_repository.rs, applied_op_repository.rs, device_repository.rs}` hold every SQL statement for this slice — `SyncBatchRepository` owns `mobile_sync_batches`, `mobile_sync_batch_ops`, `mobile_sync_op_values`; `SyncRejectionRepository` owns `mobile_sync_rejections`; `AppliedOpRepository` owns `mobile_sync_applied_ops`; `MobileDeviceRepository` owns the device, capability, and sheet-subscription tables and advances `last_sync_cursor`. `sync.rs`, `conflict.rs`, `cursor.rs`, `deeplink.rs`, `service_sync.rs`, `wipe_consumer.rs`, and the handlers depend on those traits and contain no `sqlx::query*` call; a batch's writes across all five tables plus the F008/F014 aggregates run in one `UnitOfWork` (decision section 2.1)
- Rust service/API: `crates/domain/src/mobile/{sync.rs, conflict.rs, cursor.rs, deeplink.rs, service_sync.rs, wipe_consumer.rs}`; `services/api/src/mobile/{handlers_sync.rs, handlers_deeplink.rs}`
- Data/migration: none new; uses the eight tables created in S115
- React/UI: `apps/web/src/features/mobile/{queue.ts, sync.ts, crypto.ts, OfflineBar.tsx, QueueBadge.tsx, QueuePage.tsx, ConflictCard.tsx, hooks.ts}` and push handlers in `sw.ts`
- Mocks/fixtures: in-memory push recorder; fixed signing key; Playwright Pixel 7 emulation with offline toggling; WebCrypto stub for Vitest

## TDD harness

- Test path: `testing/features/F058/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F058_FEATURE`
- Targeted command: `cargo xtask test-feature F058`
- Full command: `cargo xtask test-all`
- First failing tests: `sync_applies_ops_in_recorded_order`, `sync_rejects_conflict_with_server_value`, `sync_rejects_denied_at_sync_time`, `sync_replay_batch_returns_original`, `sync_op_rows_carry_apply_order`, `pull_uses_subscription_rows`, `pull_expired_cursor_invalid`, `deep_link_bad_signature_not_found`, `conflict_card_keep_mine_resubmits`

## Exit criteria

- [ ] Requirement tests SR-S116-01 through SR-S116-07 written first and failing
- [ ] Tasks T231 and T232 complete; client wired to real sync routes through generated client
- [ ] Unit, API, React, service worker, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `services/api/src/mobile/handlers_sync.rs` mounted through `services/api/src/mobile/routes.rs` in `services/api/src/router.rs`; `apps/web/src/features/mobile/sync.ts` invoked from `MobileShell.tsx` on reconnect
- [ ] Handoff evidence recorded in the F058 ticket
