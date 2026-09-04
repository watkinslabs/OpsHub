---
id: T229
type: task
status: planned
parent_epic: E008
parent_feature: F058
parent_story: S115
depends_on: [S115]
owned_paths: [services/api/migrations/*_mobile_*.sql, crates/domain/src/mobile/**, crates/persistence/src/mobile/**, services/api/src/mobile/**, apps/web/src/features/mobile/**, testing/features/F058/database/**, testing/features/F058/api/**, testing/features/F058/frontend/**]
feature_flag: F058_FEATURE
branch: t229-mobile-shell
started_at: null
finished_at: null
---

# T229 — Mobile shell

## Identity

- Parent story: `S115` Mobile work
- Owner: platform
- Branch: `t229-mobile-shell`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 6; `docs/capability-contracts.md` row F058

## Objective

Create the mobile schema, the manifest and device routes, and the installable PWA shell with service worker precache and bottom navigation.

## Specification

- Owned paths: `services/api/migrations/<ts>_mobile_create_tables.sql`, `services/api/migrations/<ts>_mobile_create_tables.down.sql`, `crates/domain/src/mobile/{mod.rs, device.rs, manifest.rs, errors.rs, schema.rs, service_devices.rs}`, `crates/persistence/src/mobile/{mod.rs, device_repository.rs, batch_repository.rs}`, `services/api/src/mobile/{mod.rs, routes.rs, handlers_devices.rs, handlers_manifest.rs, dto.rs}`, `apps/web/src/features/mobile/{MobileShell.tsx, BottomNav.tsx, InstallPrompt.tsx, DeviceSettings.tsx, sw.ts, api.ts, routes.ts}`
- Contract/input: `RegisterDeviceRequest { platform, push_subscription?, app_version, device_name }`; `GET /manifest.webmanifest` with tenant from session or host; service worker registered from `MobileShell` when `F058_FEATURE` is on.
- Output/behavior: DDL creates the eight tables from ticket section 4 — `mobile_devices`, `mobile_device_capabilities`, `mobile_device_sheet_subscriptions`, `mobile_sync_batches`, `mobile_sync_batch_ops`, `mobile_sync_op_values`, `mobile_sync_applied_ops`, `mobile_sync_rejections` — with every foreign key declared (`cascade` from device and batch to their child rows, `restrict` to `users`, `sessions`, `sheets`, `rows`, `forms`, `columns`, `form_fields`), the `platform`, `kind`, `outcome`, `code`, and `capability` check constraints, the composite keys `(device_id, sheet_id)`, `(device_id, capability)`, `(device_id, client_op_id)`, and the unique batch, op-index, rejection-index, and active-device indexes; `POST /api/v1/mobile/devices` returns `DeviceResponse { id, platform, device_name, app_version, version, created_at }` unchanged and publishes `mobile-device.registered.v1`; `DELETE` revokes, removes the F037 subscription, and cascades capability and subscription rows; manifest returns tenant name, icons, `start_url: /m/home`, `display: standalone`; `sw.ts` precaches the shell with a versioned cache name and serves it offline; `BottomNav` exposes Home, Sheets, Forms, Inbox; flag off returns `404` for device routes and skips service worker registration.
- Data access: `device.rs`, `manifest.rs`, `service_devices.rs`, and the handlers hold no SQL. `MobileDeviceRepository` (`crates/persistence/src/mobile/device_repository.rs`) owns `mobile_devices`, `mobile_device_capabilities`, and `mobile_device_sheet_subscriptions` and exposes `find_device_for_session`, `find_device_for_user`, `record_device_capabilities`, `device_has_capability`, `touch_sheet_subscription`, `list_sheet_subscriptions`, `prune_subscriptions_older_than`, `revoke_device`, and `advance_device_cursor`; `SyncBatchRepository` (`batch_repository.rs`) is created here owning `mobile_sync_batches`, `mobile_sync_batch_ops`, and `mobile_sync_op_values` for T231. Registration writes the device row and its capability rows in one `UnitOfWork` (decision section 2.1).
- Dependencies: F038 session context; F037 `push_subscriptions` link; F002 tenant settings for branding.
- Feature flag: `F058_FEATURE`; migration runs regardless.
- Large-table note: `mobile_sync_batch_ops` and `mobile_sync_op_values` grow per op and `mobile_sync_applied_ops` per applied op; the 30-day purge is owned by F027 and runs through `SyncBatchRepository::purge_batches_before`, which cascades ops, values, and rejections from the batch; the supporting indexes are `mobile_sync_batch_ops(sync_batch_id, op_index)`, `mobile_sync_op_values(op_id)`, and `mobile_sync_applied_ops(created_at)` beside the `(device_id, client_op_id)` primary key.

## TDD

- Failing test first: `testing/features/F058/database/migration_tests.rs::mobile_tables_exist_with_constraints`, `::duplicate_batch_id_rejected`, `::second_active_device_per_session_rejected`, `::device_capability_row_unique`, `::device_capability_value_checked`, `::sheet_subscription_row_unique`, `::device_delete_cascades_capabilities_and_subscriptions`, `::rollback_drops_tables_children_first`; `testing/features/F058/api/device_tests.rs::manifest_is_tenant_branded`, `::device_register_bound_to_session`, `::device_revoke_other_user_not_found`, `::device_routes_flag_off_not_found`; `testing/features/F058/frontend/MobileShell.test.tsx::registers_service_worker_when_flag_on`, `::flag_off_hides_install_and_routes`
- Targeted command: `cargo xtask test-feature F058`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: schema-per-worker database; `testing/fixtures/mobile.rs` users and sessions; service worker test harness with a fake cache

## Exit criteria

- [ ] Tests written before the migration and shell and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; routes mounted behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S115
- [ ] `finished_at` recorded
