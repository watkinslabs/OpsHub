---
id: F058
type: feature
status: planned
priority: P1
owner: platform
estimate: 8
target_milestone: M7
parent_epic: E008
depends_on: [F008, F014, F037]
blocks: []
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/mobile/**, crates/persistence/src/mobile/**, services/api/src/mobile/**, apps/web/src/features/mobile/**, services/api/migrations/*_mobile_*.sql, testing/features/F058/**]
feature_flag: F058_FEATURE
flag_default: off
branch: f058-mobile-clients
started_at: null
finished_at: null
---

# F058 — Mobile clients

## 1. Identity and dates

- Branch: `f058-mobile-clients`
- Capability area: work management on mobile (spec 5.1 "Mobile clients support responsive work editing, push/deep links, queued offline mutations, reconnect reconciliation, and secure local-session handling"; 5.3 FORM-03 mobile submission; section 10 "responsive web plus installable PWA, offline queued row edits/forms, push notifications, and reconnect reconciliation; offline document co-editing is excluded")
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 5, 6; `docs/capability-contracts.md` row F058
- Module slug: `mobile`

## 2. Requirement specification

### Problem and user outcome

Field staff update task status, dates, and form intake from phones with unreliable connectivity. The responsive web app works online but loses edits when the connection drops, and notifications open the app on the home page instead of the row.

As a mobile user, I want an installable app that queues my row edits and form submissions while offline, reconciles them safely on reconnect, and opens the exact row from a push notification, so that I can work in the field without losing or overwriting data.

### Functional requirements

- **FR-F058-01:** `GET /manifest.webmanifest` returns a tenant-branded manifest (`name`, `short_name`, icons 192/512 px, `start_url: /m/home`, `display: standalone`, `theme_color` from tenant settings) and the service worker `sw.js` precaches the app shell so the app installs on Android and iOS browsers and opens offline to the last cached shell.
- **FR-F058-02:** `POST /api/v1/mobile/devices` registers a device with `{ platform: android|ios|web, push_subscription?, app_version, device_name }` bound to the current session and returns UUIDv7 `id`; the request and response bodies are unchanged by normalization, and the server writes one `mobile_device_capabilities` row per capability the registration implies (`push` when `push_subscription` is present, `offline_queue` always, `install_prompt` for every supported platform, `secure_keystore` when the client presents a non-extractable key handle), so push eligibility and install prompting are joined and constrained instead of inferred from a nullable column; `DELETE /api/v1/mobile/devices/{id}` revokes it, deletes the linked F037 push subscription, cascades its capability and sheet-subscription rows, and returns `204`; a device belonging to another user returns `not_found`.
- **FR-F058-03:** While offline, the client stores cell edits (F008 `PATCH /api/v1/sheets/{sheet_id}/cells` semantics) and form submissions (F014 semantics) in an IndexedDB queue keyed by `client_op_id`, capped at 500 operations or 7 days; exceeding the cap blocks further edits with the `Queue full` state.
- **FR-F058-04:** `POST /api/v1/mobile/sync` accepts `{ device_id, batch_id, ops: [{ client_op_id, kind: cell_edit|form_submit, target, base_version, payload, recorded_at }] }` (≤ 500 ops), applies each op in recorded order through the F008 and F014 domain services, and returns `{ applied: [{ client_op_id, version }], rejected: [{ client_op_id, code, server_value, server_version }], cursor }`. The request and response keep their JSON array shapes; on the server each op becomes one `mobile_sync_batch_ops` row carrying `op_index` (the position that fixes apply order), `kind`, its typed target columns, `base_version` and `recorded_at`, and each op's payload becomes `mobile_sync_op_values` rows keyed by F007 column or F014 form field, so ops are counted, deduplicated and reported on by query rather than by parsing a batch envelope.
- **FR-F058-05:** A cell edit whose `base_version` is older than the current row version and whose target cell changed since is rejected with code `conflict`; an edit to a row the actor can no longer edit is rejected with `denied`; an edit to a deleted row is rejected with `not_found`; each rejection persists as one `mobile_sync_rejections` row linked to its `mobile_sync_batch_ops` row and ordered by `rejection_index`, with `code` constrained to `conflict|denied|not_found|invalid` and the target read from the op row rather than a JSON blob, and publishes `mobile-sync.rejected.v1`.
- **FR-F058-06:** Replaying a batch with the same `batch_id` or ops with already-applied `client_op_id` values returns the original results without re-applying; the replay response is rebuilt from the stored rows — `mobile_sync_batch_ops` in `op_index` order joined to `mobile_sync_applied_ops` for versions and to `mobile_sync_rejections` in `rejection_index` order — and is byte-identical to the first response, including `cursor`, so replay semantics are unchanged with no stored response document; applied ops publish `mobile-sync.applied.v1` once per batch with `applied_count` and `rejected_count`.
- **FR-F058-07:** `GET /api/v1/mobile/sync?since={cursor}` returns rows changed since the cursor for the sheets the device has opened in the last 30 days — one `mobile_device_sheet_subscriptions(device_id, sheet_id, last_opened_at)` row per opened sheet, joined to the F008 change log instead of scanning a JSON array — paged with `limit` ≤ 500, including `deleted` markers and the new cursor; a cursor older than 7 days returns `invalid` with `field_errors.since = "expired"` and the client performs a full refresh.
- **FR-F058-08:** On reconnect the client first pushes its queue, then pulls with `since`, and for every rejection shows a conflict card with local value, server value, and `Keep mine` (resubmit with current version) or `Take theirs` (discard); unresolved conflicts stay visible and are never auto-resolved.
- **FR-F058-09:** `GET /m/{deep_link}` resolves a signed link of the form `<kind>.<id>.<sig>` for kinds `row`, `sheet`, `form`, `notification` to the corresponding route; an invalid signature returns `404 not_found`; an unauthenticated user is sent through F038 login and returned to the target; a target the user cannot read renders the not-found page.
- **FR-F058-10:** Push notifications delivered by F037 to a registered device holding the `push` capability row carry `deep_link`, and tapping the notification opens `/m/{deep_link}` inside the installed app (service worker `notificationclick`) and marks the notification read through F037.
- **FR-F058-11:** Local session handling: refresh tokens are never stored in `localStorage`; the service worker holds the session in memory and IndexedDB entries are encrypted with a per-install key in the platform keystore (WebCrypto non-extractable key); `session.revoked.v1` for the device or an explicit logout wipes the queue, cache, and key within 5 s of the next network contact.
- **FR-F058-12:** Mobile grid editing supports tap-to-edit for `text`, `number`, `date`, `select`, `person`, `boolean` cells, row detail with all columns, and form submission with attachments queued as F017 uploads; document editing is read-only offline.
- **FR-F058-13:** Every sync batch writes an audit event per applied op with the device ID and `recorded_at`, and mutations carry the device's `Idempotency-Key` derived from `client_op_id`.
- **FR-F058-14:** A tenant with `F058_FEATURE` off serves the responsive web app without manifest install prompt, sync routes return `404 not_found`, and existing devices stop receiving deep links.

### Non-functional requirements

- **NFR-F058-01 Performance:** a 100-op sync batch is applied in under 2 s p95; `GET /mobile/sync` for 500 changed rows responds in under 500 ms p95; the app shell loads from cache in under 1.5 s on a mid-range device.
- **NFR-F058-02 Security/privacy:** device registration is bound to the session and user; sync applies every op under the actor's current permissions at sync time, never the permissions at record time; cached row data is encrypted at rest and purged on revoke; deep-link signatures use the tenant signing key and expire in 30 days.
- **NFR-F058-03 Accessibility:** mobile grid, row detail, conflict cards, and queue status pass axe with zero serious violations; touch targets are at least 44×44 px; offline and queue states are announced by a live region.
- **NFR-F058-04 Reliability/observability:** sync is idempotent per `batch_id` and `client_op_id`, enforced by the `mobile_sync_batches(device_id, batch_id)` and `mobile_sync_applied_ops(device_id, client_op_id)` unique keys rather than by application checks; metrics `mobile_sync_ops_total{result}`, `mobile_sync_batch_duration_ms`, and `mobile_queue_depth` (client telemetry) are emitted; every batch carries a `correlation_id` shared by all applied ops.

### Scope

Included: PWA manifest and service worker, device registry, offline queue for cell edits and form submissions, sync push/pull with conflict rejections, reconnect reconciliation UI, deep links, push tap handling, secure local session and wipe, mobile grid and row detail editing.

Excluded: offline document co-editing (section 10), native app stores, offline attachment preview, background sync of reports and dashboards, offline creation of new sheets or columns.

## 3. UX specification

- Personas: field technician (edits status and dates offline), intake coordinator (submits forms from a phone), manager (opens rows from push).
- Entry points: browser install prompt on `/m/home`; push notification tap; shared `/m/{deep_link}` URL; bottom navigation `Home`, `Sheets`, `Forms`, `Inbox`.
- Primary flow: install the app, open a sheet, lose connectivity, edit three cells and submit a form, see the queue badge `4 pending`, regain connectivity, watch the badge drain, resolve one conflict card by choosing `Keep mine`, receive a push about an assignment, tap it, land on the row.
- Loading: shell from cache with skeleton rows; Empty: `No sheets opened yet`; Error: banner with `correlation_id` and retry; Success: toast `Synced 4 changes`; Stale: row shows `Updated on server` chip until refreshed; Conflict: card with both values and two actions; Offline: persistent top bar `Offline, changes will sync` with queue count; Queue full: edits disabled with explanation; Denied: cell shows lock icon and `You can no longer edit this`.
- Permission-denied: rows the user lost access to are removed on pull with a dismissible notice; deep links to unreadable targets render not-found.
- Responsive: layouts are designed at 360 px first; grid shows the primary column plus one chosen column with horizontal swipe; row detail is a full-screen page; tablets over 768 px show the desktop grid.
- Keyboard and touch: all controls reachable by external keyboard; touch targets ≥ 44 px; `Escape` or back gesture closes row detail; focus moves to the conflict card when one appears; reduced motion disables queue badge animation.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide `WifiOff`, `CloudUpload`, `GitMerge`, `Bell`, `Smartphone`; tokens from `apps/web/src/design/tokens.css` with the compact density scale.

## 4. Technical specification

### Rust backend

- Data access (decision section 2.1): `crates/persistence/src/mobile/` holds `MobileDeviceRepository` (owns `mobile_devices`, `mobile_device_sheet_subscriptions`, `mobile_device_capabilities`), `SyncBatchRepository` (owns `mobile_sync_batches`, `mobile_sync_batch_ops`, `mobile_sync_op_values`), `SyncRejectionRepository` (owns `mobile_sync_rejections`), and `AppliedOpRepository` (owns `mobile_sync_applied_ops`); no other class writes those tables. Named queries: `find_device_for_session`, `find_device_for_user`, `revoke_device`, `list_sheet_subscriptions`, `touch_sheet_subscription`, `prune_subscriptions_older_than`, `record_device_capabilities`, `device_has_capability`, `find_batch_by_device_and_batch_id`, `insert_batch_with_ops`, `list_ops_in_apply_order`, `list_op_values`, `set_op_outcome`, `list_rejections_for_batch`, `list_rejections_for_device`, `claim_client_op_ids`, `list_applied_versions_for_batch`, `advance_device_cursor`, `purge_batches_before`. There is no generic query entry point. The use cases below depend on these repository traits and contain no SQL: `services/api/src/mobile/` handlers, the `session.revoked.v1` wipe consumer, and the F027 purge job call repositories only, and `pull_changes` reads the F008 change log through F008's change-log repository rather than issuing its own SQL. `apply_sync_batch` writes `mobile_sync_batches`, `mobile_sync_batch_ops`, `mobile_sync_op_values`, `mobile_sync_applied_ops`, `mobile_sync_rejections`, and the F008/F014 aggregate tables in one `UnitOfWork` that owns the transaction and the per-op savepoints, so a batch is applied and recorded atomically; `register_device` writes the device with its capability and subscription rows in the same unit of work.
- Canonical contract: aggregate `mobile-session`; module `mobile`; routes `GET /manifest.webmanifest`, `POST /api/v1/mobile/sync`, `GET /api/v1/mobile/sync?since={cursor}`, `POST /api/v1/mobile/devices`, `DELETE /api/v1/mobile/devices/{id}`, `GET /m/{deep_link}`; events `mobile-sync.applied.v1`, `mobile-sync.rejected.v1`, `mobile-device.registered.v1`; tables `mobile_devices`, `mobile_sync_batches`, `mobile_sync_rejections` plus the normalized child tables listed in the PostgreSQL/SQLx section; roles `resource-editor` (applied ops), `self` (devices).
- Domain entities in `crates/domain/src/mobile/`: `MobileDevice { id, tenant_id, user_id, session_id, platform, push_subscription_id, app_version, device_name, subscriptions: Vec<SheetSubscription>, capabilities: BTreeSet<DeviceCapability>, last_sync_cursor, revoked_at, version, audit fields }` where `subscriptions` and `capabilities` are hydrated by `MobileDeviceRepository` from `mobile_device_sheet_subscriptions` and `mobile_device_capabilities` rows, `SyncBatch { id, tenant_id, device_id, batch_id, ops: Vec<SyncOp> in op_index order, applied_count, rejected_count, cursor, correlation_id, created_at }`, `SyncOp { id, op_index, client_op_id, kind: OpKind (CellEdit|FormSubmit), target: OpTarget (Cell { sheet_id, row_id } | Form { form_id }), base_version, values: Vec<OpValue { column_id | form_field_id, value: CellValue }>, recorded_at, outcome, applied_version }`, `SyncRejection { id, sync_batch_id, op_id, rejection_index, client_op_id, code: RejectionCode (Conflict|Denied|NotFound|Invalid), server_value, server_version }`, `DeepLink { kind: DeepLinkKind (Row|Sheet|Form|Notification), id, signature, expires_at }`.
- Use cases: `register_device`, `revoke_device`, `apply_sync_batch` (wraps F008 `grid::apply_cell_edit` and F014 `forms::submit` per op with per-op savepoints), `pull_changes`, `resolve_deep_link`, `sign_deep_link` (used by F037 push payload builder), `wipe_on_revoke` (consumer of `session.revoked.v1`), `render_manifest`.
- API DTOs (`services/api/src/mobile/dto.rs`): `RegisterDeviceRequest`, `DeviceResponse`, `SyncBatchRequest`, `SyncBatchResponse { applied, rejected, cursor }`, `PullResponse { rows, deleted_row_ids, cursor }`, `ManifestResponse`.
- Events: `mobile-device.registered.v1` on register; `mobile-sync.applied.v1` once per batch with `{ batch_id, applied_count, rejected_count }`; `mobile-sync.rejected.v1` per rejection with `{ client_op_id, code, target }`; the underlying `cell.updated.v1` and `form.submitted.v1` events are published by F008 and F014 as usual.
- Authorization: devices are `self` scoped (tenant admins may revoke through F002 user deactivation); each op is authorized at sync time with `authz::require(actor, Permission::CellEdit | FormSubmit, target)`; deep links require an authenticated session plus resource read.
- Validation: ≤ 500 ops per batch, `recorded_at` within the last 7 days, `payload` ≤ 64 KB per op, `device_name` ≤ 80 chars, `since` cursor signed and ≤ 7 days old.
- Error mapping: `MobileError::BatchTooLarge → 400 invalid`, `MobileError::CursorExpired → 400 invalid`, `MobileError::DeviceRevoked → 403 denied`, `MobileError::DeviceNotFound → 404 not_found`, `MobileError::BadSignature → 404 not_found`, `MobileError::FlagOff → 404 not_found`; per-op rejections are data in the 200 response, not HTTP errors.

### PostgreSQL/SQLx

- Migration `*_mobile_*.sql` creates `mobile_devices(id uuid pk, tenant_id uuid not null, user_id uuid not null references users(id) on delete restrict, session_id uuid not null references sessions(id) on delete restrict, platform text not null check (platform in ('android','ios','web')), push_subscription_id uuid references push_subscriptions(id) on delete set null, app_version text not null, device_name text not null, last_sync_cursor text, revoked_at timestamptz, version bigint not null default 1, created_by, created_at, updated_by, updated_at)`, `mobile_sync_batches(id uuid pk, tenant_id, device_id uuid not null references mobile_devices(id) on delete restrict, batch_id uuid not null, applied_count int not null default 0 check (applied_count >= 0), rejected_count int not null default 0 check (rejected_count >= 0), cursor text not null, correlation_id uuid not null, created_at)`, and `mobile_sync_rejections(id uuid pk, tenant_id, sync_batch_id uuid not null references mobile_sync_batches(id) on delete cascade, op_id uuid not null references mobile_sync_batch_ops(id) on delete cascade, device_id uuid not null references mobile_devices(id) on delete restrict, rejection_index int not null check (rejection_index >= 0), client_op_id uuid not null, code text not null check (code in ('conflict','denied','not_found','invalid')), server_value jsonb, server_version bigint, created_at)`.
- Normalized sets (decision section 2, no array or envelope columns): `mobile_device_sheet_subscriptions(device_id uuid references mobile_devices(id) on delete cascade, tenant_id, sheet_id uuid references sheets(id) on delete cascade, last_opened_at timestamptz not null, primary key (device_id, sheet_id))` replaces `mobile_devices.subscriptions jsonb`, which the pull query read by key; `mobile_device_capabilities(device_id uuid references mobile_devices(id) on delete cascade, tenant_id, capability text not null check (capability in ('push','offline_queue','install_prompt','secure_keystore')), granted_at timestamptz not null, primary key (device_id, capability))` holds the device capability and push-topic set as rows so push eligibility is a join; `mobile_sync_batch_ops(id uuid pk, tenant_id, sync_batch_id uuid not null references mobile_sync_batches(id) on delete cascade, op_index int not null check (op_index between 0 and 499), client_op_id uuid not null, kind text not null check (kind in ('cell_edit','form_submit')), target_sheet_id uuid references sheets(id) on delete restrict, target_row_id uuid references rows(id) on delete restrict, target_form_id uuid references forms(id) on delete restrict, base_version bigint, recorded_at timestamptz not null, outcome text not null check (outcome in ('applied','rejected')), applied_version bigint, check ((kind = 'cell_edit' and target_sheet_id is not null and target_row_id is not null and target_form_id is null) or (kind = 'form_submit' and target_form_id is not null and target_sheet_id is null and target_row_id is null)))` replaces the batch `ops` array and the per-op `target jsonb`, with `op_index` carrying the apply order; `mobile_sync_op_values(id uuid pk, tenant_id, op_id uuid not null references mobile_sync_batch_ops(id) on delete cascade, column_id uuid references columns(id) on delete restrict, form_field_id uuid references form_fields(id) on delete restrict, value jsonb not null, check (num_nonnulls(column_id, form_field_id) = 1))` replaces the per-op `payload` document — one row per edited cell or answered form field; `mobile_sync_applied_ops(device_id uuid references mobile_devices(id) on delete cascade, client_op_id uuid not null, tenant_id, op_id uuid not null references mobile_sync_batch_ops(id) on delete restrict, version bigint not null, created_at, primary key (device_id, client_op_id))` is the cross-batch dedupe ledger, and `mobile_sync_rejections` gains `rejection_index` for the response order it previously inherited from a JSON array. `SyncBatchRequest`, `SyncBatchResponse`, `PullResponse`, and `RegisterDeviceRequest` keep their JSON array and object shapes: `SyncBatchRepository::insert_batch_with_ops` fans the `ops` array out to `mobile_sync_batch_ops` and `mobile_sync_op_values` rows, and `list_ops_in_apply_order` plus `list_rejections_for_batch` reassemble `applied` and `rejected` in `op_index` and `rejection_index` order, so request parsing, response bodies, idempotency keys, and replay semantics are byte-for-byte unchanged.
- `jsonb` audit: `mobile_sync_op_values.value` stays `jsonb` — it is the F007 typed cell value or form-field answer, stored and replayed verbatim and never filtered, joined, or aggregated by the mobile module; `mobile_sync_rejections.server_value` stays `jsonb` — it is the server-side half of the conflict diff shown on the conflict card. Converted to tables because the server validates, counts, deduplicates, or reports on them: `mobile_devices.subscriptions` (pull scope, read by key), `mobile_sync_batches.response` (replay envelope, now rebuilt from rows), `mobile_sync_batch_ops.payload` and `.target` (op routing and authorization). No other `jsonb` column remains in this module.
- Invariants: unique `mobile_sync_batches_device_batch_idx on (device_id, batch_id)` keeps batch replay idempotent; primary key `mobile_sync_applied_ops(device_id, client_op_id)` keeps op replay idempotent; unique `mobile_sync_batch_ops(sync_batch_id, op_index)` and `(sync_batch_id, client_op_id)` give one position and one occurrence per op; unique `mobile_sync_rejections(sync_batch_id, rejection_index)` and `(sync_batch_id, client_op_id)` give one rejection per op in a stable response order; unique `mobile_sync_op_values(op_id, column_id)` and `(op_id, form_field_id)` (partial, where the column is not null) allow one value per field per op, and a `cell_edit` op carries exactly one value row, checked by `SyncBatchRepository::insert_batch_with_ops`; check `applied_count + rejected_count <= 500` and both counts equal the matching `mobile_sync_batch_ops` row counts by outcome; one active device per `(user_id, session_id)` partial unique index where `revoked_at is null`; `mobile_device_sheet_subscriptions` and `mobile_device_capabilities` primary keys block duplicate subscriptions and duplicate capability grants.
- Indexes: `mobile_devices(tenant_id, user_id) where revoked_at is null`, `mobile_device_sheet_subscriptions(sheet_id, last_opened_at desc)` for the pull query and the 30-day prune, `mobile_device_capabilities(capability, device_id)` for "which devices take push", `mobile_sync_batches(device_id, created_at desc)`, `mobile_sync_batch_ops(sync_batch_id, op_index)` for ordered replay, `mobile_sync_batch_ops(target_row_id)` for per-row op history, `mobile_sync_op_values(op_id)`, `mobile_sync_applied_ops(created_at)` for the purge job, `mobile_sync_rejections(device_id, created_at desc)` and `mobile_sync_rejections(sync_batch_id, rejection_index)`.
- Audit events: `mobile.device.register`, `mobile.device.revoke`, `mobile.sync.apply` (one per applied op with `client_op_id`, `device_id`, `recorded_at`), `mobile.sync.reject`, `mobile.deeplink.resolve`.
- Retention/deletion: the migration creates parents before children (`mobile_devices`, `mobile_device_capabilities`, `mobile_device_sheet_subscriptions`, `mobile_sync_batches`, `mobile_sync_batch_ops`, `mobile_sync_op_values`, `mobile_sync_applied_ops`, `mobile_sync_rejections`); batches older than 30 days are purged by the F027 job through `SyncBatchRepository::purge_batches_before`, which cascades ops, op values, and rejections and runs before any F008 row purge so the op target foreign keys never block it; sheet subscriptions not touched in 30 days are pruned on each pull; revoked devices are purged after 90 days, cascading their capability, subscription, and applied-op rows; rollback drops the eight tables, children before parents.

### React/TypeScript

- Routes: `/m/home`, `/m/sheets/:sheetId`, `/m/rows/:rowId`, `/m/forms/:formId`, `/m/inbox`, `/m/queue`, `/m/:deepLink` in `apps/web/src/features/mobile/`; components `MobileShell`, `BottomNav`, `OfflineBar`, `QueueBadge`, `MobileGrid`, `MobileCellEditor`, `RowDetailPage`, `MobileFormPage`, `ConflictCard`, `QueuePage`, `DeviceSettings`, `InstallPrompt`.
- Service worker: `apps/web/src/features/mobile/sw.ts` precaches the shell, caches opened sheets with a 30-day LRU, handles `push`, `notificationclick`, and `sync` events, and holds the session token in memory.
- State: `apps/web/src/features/mobile/queue.ts` (IndexedDB via `idb`, encrypted values), `sync.ts` (push then pull, exponential backoff 1 s to 60 s), TanStack Query keys `['mobile-sheet', sheetId]`, `['mobile-queue']`, `['mobile-devices']`; `useOnlineStatus` drives the offline bar.
- API client: generated `MobileApi` with `registerDevice`, `revokeDevice`, `pushSync`, `pullSync`, plus reuse of `GridApi` and `FormsApi` types for op payloads.
- Optimistic updates: queued edits render immediately with a `pending` chip; rejections replace the chip with the conflict card; `Take theirs` writes the server value locally.
- Feature flag: `useFlag('F058_FEATURE')` gates the install prompt, `/m/*` routes, and service worker registration.
- Telemetry: `mobile_installed`, `mobile_edit_queued`, `mobile_sync_completed`, `mobile_conflict_resolved`, `mobile_deep_link_opened`, `mobile_queue_full` with `device_id`, `op_count`, `resolution`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F058-01 through FR-F058-14 in `testing/features/F058/requirements/cases.md`
- [ ] Failure/edge-case tests: 501-op batch, expired cursor, replayed batch, replayed op, edit to deleted row, lost permission between record and sync, queue full, bad deep-link signature
- [ ] Permission-negative and tenant-isolation tests: other user's device not_found, sync as revoked device denied, deep link to unreadable row not-found, cross-tenant device not_found
- [ ] Rust unit tests: `crates/domain/src/mobile/` conflict detection, cursor signing and expiry, deep-link signing, per-op savepoint rollback
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: batch uniqueness, applied-op uniqueness, active device index, duplicate `mobile_device_sheet_subscriptions` and `mobile_device_capabilities` rows rejected, `mobile_sync_batch_ops` op-index uniqueness and the kind/target check, `mobile_sync_op_values` one-value-per-field and exactly-one-target check, `mobile_sync_rejections` code check and rejection-index uniqueness, cascade from batch purge, rollback ordering; fixtures and assertions run through the `crates/persistence/src/mobile/` repositories
- [ ] React component tests: `MobileGrid`, `ConflictCard`, `QueuePage`, `OfflineBar`, service worker handlers
- [ ] Browser E2E tests: install, offline edits, reconnect, conflict resolution, push tap deep link, logout wipe
- [ ] Accessibility tests: axe on mobile grid, row detail, conflict card; touch target size; live region
- [ ] Performance/load tests: 100-op batch p95 under 2 s, pull 500 rows p95 under 500 ms, shell load under 1.5 s

### Fast fanout configuration

- Test harness path: `testing/features/F058/`
- Feature flag: `F058_FEATURE`
- Fixture/seed factory: `testing/fixtures/mobile.rs` builds tenant, two users with sessions, a sheet with 200 rows and six column types, a published form, registered devices for each user, and a foreign tenant
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, fixed signing key for deep links and cursors
- Mock/stub contracts: F037 push delivery recorded in memory; Playwright uses Chromium device emulation (Pixel 7) with network offline toggling; WebCrypto key stub for Vitest
- Parallel isolation: one schema per test worker, tenant ID per test, unique device IDs per test
- Targeted command: `cargo xtask test-feature F058`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F058/`

## 6. Acceptance criteria

```gherkin
Feature: Offline mobile editing with safe reconciliation

Scenario: Queued edits sync on reconnect
  Given an installed app with 3 queued cell edits and 1 queued form submission
  When connectivity returns
  Then POST /api/v1/mobile/sync applies all 4 ops, the queue badge reaches 0
  And mobile-sync.applied.v1 reports applied_count 4 and rejected_count 0

Scenario: Concurrent server edit produces a visible conflict
  Given a queued edit to cell "Status" recorded at row version 5
  When another user changed "Status" to "Done" at version 6 before sync
  Then the op is rejected with code conflict and server_value "Done"
  And the conflict card offers Keep mine and Take theirs and nothing is overwritten

Scenario: Lost permission is enforced at sync time
  Given a queued edit recorded while the user was an editor
  When the user is downgraded to viewer before sync
  Then the op is rejected with code denied and no cell changes

Scenario: Push deep link opens the row
  Given a registered device with a push subscription
  When an assignment notification is tapped
  Then the app opens /m/rows/{row_id} and the notification is marked read
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F008 (cell edit service, versions, history), F014 (form submission service and tokens), F037 (push subscriptions and delivery); decisions sections 2, 3, 4, 5, 6; contracts row F058
- Blocks: none
- Conflicts with: none (disjoint owned paths)
- External dependencies: browser push services reached through F037; no third-party SDK
- Risks and mitigations: iOS background limits can drop the service worker, so the queue is persisted in IndexedDB before any network attempt and sync also runs on app foreground; encrypted cache keys can be lost when storage is evicted, so eviction triggers a full refresh with a user notice; large pulls after long offline periods are bounded by the 7-day cursor expiry and full refresh.
- Rollout: enable `F058_FEATURE` for the pilot tenant, monitor `mobile_sync_ops_total{result="conflict"}` and `mobile_queue_full` for two weeks before wider rollout.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F008, F014, and F037 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F058/`
- [ ] Migration file name and owned paths claimed
- [ ] Device emulation, push recorder, and schema-per-worker isolation available in `testing/harness/`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, service worker, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every applied and rejected op
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F058_FEATURE`, confirm sync routes return not_found, run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Users can install OpsHub as a mobile app, edit rows and submit forms offline, reconcile conflicts on reconnect, and open rows directly from push notifications.
- Support: rejected ops are listed under `/m/queue` with codes; operators can inspect `mobile_sync_rejections` per device.
- Migration adds `mobile_devices`, `mobile_device_capabilities`, `mobile_device_sheet_subscriptions`, `mobile_sync_batches`, `mobile_sync_batch_ops`, `mobile_sync_op_values`, `mobile_sync_applied_ops`, and `mobile_sync_rejections`; rollback drops them. Feature is off by default behind `F058_FEATURE`.
