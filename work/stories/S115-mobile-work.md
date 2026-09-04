---
id: S115
type: story
status: planned
parent_epic: E008
parent_feature: F058
depends_on: [F008, F014, F037]
owned_paths: [crates/domain/src/mobile/**, crates/persistence/src/mobile/**, services/api/src/mobile/**, apps/web/src/features/mobile/**, services/api/migrations/*_mobile_*.sql, testing/features/F058/**]
feature_flag: F058_FEATURE
branch: s115-mobile-work
started_at: null
finished_at: null
---

# S115 — Mobile work

## Identity

- Parent feature: `F058` Mobile clients
- Owner: platform
- Branch: `s115-mobile-work`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 6; `docs/capability-contracts.md` row F058

## Vertical slice

As a field user, I want an installable mobile shell with device registration, a touch-first grid and row detail, and form submission, so that online mobile work is complete before offline queueing and sync are added.

## Requirements

- **SR-S115-01:** `GET /manifest.webmanifest` returns the tenant-branded manifest and `sw.js` precaches the shell so the app installs and opens to `/m/home` (covers FR-F058-01).
- **SR-S115-02:** `POST /api/v1/mobile/devices` binds a device to the current session and user through `MobileDeviceRepository`, writing the device row plus its `mobile_device_capabilities` rows (`push` when a push subscription is supplied, `offline_queue`, `install_prompt`, `secure_keystore` when a key handle is presented) in one `UnitOfWork`, returns the unchanged `DeviceResponse` with version 1, and publishes `mobile-device.registered.v1`; `DELETE /api/v1/mobile/devices/{id}` revokes it and its F037 push subscription and cascades its capability and subscription rows; another user's device returns `404 not_found` (FR-F058-02).
- **SR-S115-03:** The migration creates `mobile_devices`, `mobile_device_capabilities`, `mobile_device_sheet_subscriptions`, `mobile_sync_batches`, `mobile_sync_batch_ops`, `mobile_sync_op_values`, `mobile_sync_applied_ops`, and `mobile_sync_rejections` with the foreign keys, `check` constraints, composite keys, and indexes from ticket section 4, parents before children, and reverts children first (NFR-F058-04).
- **SR-S115-04:** `MobileGrid` shows the primary column plus one swipeable column with 44 px touch targets; `MobileCellEditor` edits `text`, `number`, `date`, `select`, `person`, `boolean` through F008 `PATCH cells` when online, and opening a sheet records a `mobile_device_sheet_subscriptions` row through `MobileDeviceRepository::touch_sheet_subscription` so the later pull scope is a joined set, not a JSON list (FR-F058-12, FR-F058-07).
- **SR-S115-05:** `RowDetailPage` shows all columns and `MobileFormPage` submits a published form with attachments through F014 and F017 when online (FR-F058-12).
- **SR-S115-06:** With `F058_FEATURE` off, the manifest omits the install prompt, `/m/*` routes are not registered, and sync and device routes return `404 not_found` (FR-F058-14).
- **SR-S115-07:** Shell, grid, and row detail pass axe with zero serious violations and load from cache in under 1.5 s (NFR-F058-01, NFR-F058-03).

## Surfaces

- Infrastructure/container: none beyond F004 baseline
- Data access: `crates/persistence/src/mobile/{mod.rs, device_repository.rs, batch_repository.rs}` hold every SQL statement for this slice — `MobileDeviceRepository` owns `mobile_devices`, `mobile_device_capabilities`, and `mobile_device_sheet_subscriptions`; `SyncBatchRepository` owns `mobile_sync_batches`, `mobile_sync_batch_ops`, and `mobile_sync_op_values` and is created here for S116 to use. `crates/domain/src/mobile/` and the `services/api/src/mobile` handlers depend on the repository traits and contain no `sqlx::query*` call (decision section 2.1)
- Rust service/API: `crates/domain/src/mobile/{mod.rs, device.rs, manifest.rs, errors.rs, service_devices.rs}`; `services/api/src/mobile/{mod.rs, routes.rs, handlers_devices.rs, handlers_manifest.rs, dto.rs}`
- Data/migration: `services/api/migrations/<ts>_mobile_create_tables.sql` and `.down.sql`
- React/UI: `apps/web/src/features/mobile/{MobileShell.tsx, BottomNav.tsx, InstallPrompt.tsx, MobileGrid.tsx, MobileCellEditor.tsx, RowDetailPage.tsx, MobileFormPage.tsx, DeviceSettings.tsx, sw.ts, api.ts, routes.ts}`
- Mocks/fixtures: `testing/fixtures/mobile.rs` tenant, two users with sessions, 200-row sheet with six column types, published form, foreign tenant; MSW handlers for grid and forms

## TDD harness

- Test path: `testing/features/F058/{api,database,frontend,accessibility}/`
- Feature flag: `F058_FEATURE`
- Targeted command: `cargo xtask test-feature F058`
- Full command: `cargo xtask test-all`
- First failing tests: `manifest_is_tenant_branded`, `device_register_bound_to_session`, `device_revoke_other_user_not_found`, `mobile_tables_exist_with_constraints`, `device_capability_row_unique`, `sheet_subscription_row_unique`, `mobile_grid_edits_cell_online`, `flag_off_hides_install_and_routes`

## Exit criteria

- [ ] Requirement tests SR-S115-01 through SR-S115-07 written first and failing
- [ ] Tasks T229 and T230 complete and wired through `services/api` router and the web router
- [ ] Unit, API, database, React, accessibility, permission tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/mobile/routes.rs` mounted in `services/api/src/router.rs`; `apps/web/src/features/mobile/MobileShell.tsx` mounted at `/m/*`
- [ ] Handoff evidence recorded in the F058 ticket
