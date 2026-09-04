---
id: F070
type: feature
status: planned
priority: P1
owner: platform
estimate: 5
target_milestone: M2
parent_epic: E003
depends_on: [F005, F006]
blocks: []
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/trash/**, crates/persistence/src/trash/**, services/api/src/trash/**, services/worker/src/trash/**, apps/web/src/features/trash/**, services/api/migrations/*_trash_*.sql, testing/features/F070/**]
feature_flag: F070_FEATURE
flag_default: off
branch: f070-trash-and-recovery
started_at: null
finished_at: null
---

# F070 — Trash and recovery

## 1. Identity and dates

- Branch: `f070-trash-and-recovery`
- Capability area: work management recovery (spec 4.2 folder trash retention; spec 8 soft-delete recovery; spec 12 the administrator who must recover a deleted row)
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 7; `docs/capability-contracts.md` row F070; `docs/authorization-model.md` sections 1 and 3.3; `docs/threat-model.md` sections 3.4 and 3.6
- Aggregate: `trash-item`
- Module slug: `trash`

## 2. Requirement specification

### Problem and user outcome

Soft deletion is everywhere. Over forty features set `deleted_at` and each offers its own restore — `POST /api/v1/sheets/{id}/restore`, `POST /api/v1/rows/{id}/restore`, `POST /api/v1/documents/{id}/restore`, `POST /api/v1/workspaces/{id}/restore`. Every one of them requires the person to already know what they lost, which object type it was, and where it lived. Someone who deletes the wrong thing and closes the tab has no way back, and the six kinds with no restore route at all — views, files, reports, dashboards and folders — are recoverable only by an engineer with database access. Retention quietly reclaims them thirty days later without anyone seeing the countdown.

As an editor, I want one place that lists everything deleted from the workspaces I can see, with what it was, who deleted it, where it came from and how long is left, so that I can put it back where it belongs or destroy it deliberately instead of hoping a support ticket finds it in time.

### Functional requirements

- **FR-F070-01:** `GET /api/v1/trash` returns a cursor page of `TrashEntryResponse { entry_id, kind, item_id, title, parent_kind, parent_id, parent_path, workspace_id, deleted_at, deleted_by, expires_at, days_remaining, state, blocked_reason, held }` ordered by `deleted_at` descending then `entry_id`, with `limit` 1–200 (default 50) and filters `kind`, `workspace_id`, `deleted_by`, `deleted_after`, `deleted_before` and `q` (case-insensitive prefix over `title`); the envelope carries `as_of` (the projector's last applied event time) and `stale` (true when `as_of` is more than 120 seconds behind now).
- **FR-F070-02:** An entry is listed only when F003 grants `<resource>:read` on the deleted item itself, evaluated against the ACL rows that survive a soft delete, exactly as search prefilters. Being the deleter grants nothing. `GET` filters before paging so page sizes never leak a hidden count, and a caller who could not read the item before it was deleted sees neither the row nor its title, and receives `404 not_found` from restore and purge on its id.
- **FR-F070-03:** `trash_entries` is a projection, never a source of truth. The worker consumer `trash.project` subscribes to the registered kinds' deletion and restoration events — `sheet.deleted.v1`, `sheet.restored.v1`, `row.deleted.v1`, `row.restored.v1`, `view.deleted.v1`, `document.deleted.v1`, `document.restored.v1`, `file.deleted.v1`, `report.deleted.v1`, `dashboard.deleted.v1`, and, because F005 publishes no folder deletion event, `folder.updated.v1` whose `changed_fields` contains `deleted_at` — and upserts one row per `(tenant_id, kind, item_id)`. Application is idempotent and order-independent: an event whose `version` is not greater than the stored `source_version` is discarded, and a restoration event deletes the entry.
- **FR-F070-04:** The job `trash.rebuild` re-derives a tenant's entries from the owning tables by calling every registered kind's `list_deleted` port, writes them under a new `projection_epoch`, and deletes rows from the previous epoch in the same `UnitOfWork`, so a rebuild is atomic and never shows a half-built list. It runs on demand for one tenant, and automatically when the registry key set changes between releases. The index is allowed to be stale — bounded by NFR-F070-01 and surfaced by `stale` — because no decision is taken from it: restore and purge resolve the live row through the owning repository and re-check permission, so a stale entry can only produce `404 not_found` or `409 conflict`, never a wrong grant or a wrong deletion.
- **FR-F070-05:** The eight kinds are `sheet`, `row`, `view`, `folder`, `document`, `file`, `report` and `dashboard`, each mapping to the resource key of the same name in `docs/authorization-model.md` section 1. A kind is registered by its owning feature, not by this one: the owning module declares a `TrashKindSpec` in a `linkme` distributed slice `TRASH_KINDS` inside its own owned paths, giving the kind key, resource key, deletion and restoration event names, and a `TrashTarget` port. `sheet`, `row` and `folder` are live with F005 and F006; `view`, `document`, `file`, `report` and `dashboard` register when F013, F045, F017, F021 and F023 land, and no file under this feature's owned paths changes when they do. `TrashRegistry::load` runs at start-up and refuses to boot on a duplicate kind key or a resource key absent from the authorization model.
- **FR-F070-06:** `POST /api/v1/trash/{kind}/{id}/restore` restores through the kind's `TrashTarget::restore` port inside one `UnitOfWork`, publishes `item.restored.v1` with `{ kind, item_id, parent_kind, parent_id }`, deletes the trash entry, and returns `200` with the restored item's new `version`. Permission is evaluated against the restore target's current ACL — `<resource>:create` on the parent the item returns to, plus `<resource>:update` on the item — and never against the deleter's identity or any permission captured at deletion time, so a person who can see a deleted row in the trash still cannot restore it into a folder they may not write, which returns `403 denied`.
- **FR-F070-07:** Restore refuses to orphan. When the item's `parent_kind`/`parent_id` is itself soft-deleted, the response is `409 conflict` with code `parent_deleted`, `field_errors.parent_id` naming the parent's kind, title and trash `entry_id`, and no write occurs; the entry's `state` is `blocked` with `blocked_reason: parent_deleted` until the parent returns. Restoring a parent restores the children the owning feature's own restore covers — a sheet restore brings back its rows and groups — and those child entries are removed as `superseded` by the resulting restoration events rather than restored twice. When the owning row no longer exists at all the entry is `blocked` with `blocked_reason: target_missing` and restore returns `404 not_found`.
- **FR-F070-08:** `expires_at` is `deleted_at` plus the F027 retention policy `purge_after_days` for the record kind, read through a `RetentionPolicyPort`; a `null` policy means keep forever and renders as no countdown. The nightly job `trash.sweep` sets `state = 'expired'` on entries past `expires_at` and hands them, one batch of 500 per tenant, to the F027 purge path through `PurgeExecutorPort`; it never hard-deletes on its own and never removes an entry whose owning row is still present.
- **FR-F070-09:** A legal hold always beats the retention policy. Before any purge — swept or requested — `LegalHoldPort::is_held(kind, item_id)` is consulted; a held entry is marked `held: true`, keeps its row past `expires_at` with `state = 'held'`, is skipped by the sweep with its held count recorded on the purge request, and refuses `DELETE` with `409 conflict` code `legal_hold` naming the hold. Restore of a held item is allowed, matching FR-F027-05.
- **FR-F070-10:** `DELETE /api/v1/trash/{kind}/{id}` is purge-now and irreversible. It requires `compliance-admin` in addition to read access — the authorization model section 3.3 reserves `purge`, and no resource role grants it — plus `Idempotency-Key` and `If-Match` carrying the entry's `source_version`; it executes through `PurgeExecutorPort` so the same audited code path runs as for an F027 governance purge, removes the owning row and any object-storage blob the kind declares, writes the audit event `trash.purge` with kind, item id, title, actor and the hold check result, publishes `item.purged.v1`, and returns `204`. An `editor` receives `403 denied`.
- **FR-F070-11:** Cross-tenant and permission negatives are part of the contract: an `entry_id`, kind or item id from another tenant returns `404 not_found` on list, restore and purge, never `403 denied`, so existence does not leak; `q` never matches across tenants; and the projector drops an event whose `tenant_id` does not match the entry it would touch.
- **FR-F070-12:** The `/trash` screen lists entries with kind icon, title, original location, deleter, deleted time and days remaining, filters by kind, workspace, person and date, selects rows for bulk restore, and shows a blocked row's reason with a `Restore parent first` action that jumps to the parent's entry. `Purge` is present but disabled with an explanation for anyone without `compliance-admin`, and a held row shows a hold chip in place of the countdown.

### Non-functional requirements

- **NFR-F070-01 Performance:** the first page of 50 entries responds in under 400 ms p95 over 200,000 entries in a tenant; the ACL prefilter is a join against `resource_acls`, never a post-filter, so a page never returns fewer rows than requested while more are available; projection lag from event publish to visible entry is under 5 s p95 and under 120 s p99, which is the bound `stale` reports; a full rebuild of 200,000 entries completes in under 3 minutes.
- **NFR-F070-02 Security/privacy:** trash reveals nothing a caller could not read before deletion — no title, no parent path, no count; `deleted_by` shows a display name only for principals the caller may already see, otherwise `Someone`; purge requires `compliance-admin`, is audited with actor and correlation id, and is refused under hold; every query carries the tenant predicate through the repository base contract; cross-tenant, guest and scoped-token negatives are tested.
- **NFR-F070-03 Accessibility:** the trash screen passes axe with zero serious or critical violations in both themes; `state` is text plus a labelled icon, never colour alone; the purge confirmation dialog traps focus, names the item in its heading, and announces the result; the days-remaining countdown is readable text, not a bar alone.
- **NFR-F070-04 Reliability/observability:** the projector is idempotent per `(tenant_id, kind, item_id, source_version)`, resumes from its durable JetStream cursor after a restart with no duplicate or lost entry, and dead-letters a poison event after 3 attempts without stopping the stream; metrics `trash_projection_lag_seconds`, `trash_entries_total{kind,state}`, `trash_restores_total{kind,outcome}` and `trash_purges_total{kind,outcome}` are emitted; every request and job runs in a span carrying `tenant_id`, `actor_id`, `correlation_id` and `entry_id`.
- **NFR-F070-05 Correctness:** a rebuild is equivalence-checked against the incremental projection — after a randomized sequence of deletes, restores and out-of-order event delivery, `trash.rebuild` produces byte-identical rows to the live projection except `projected_at` and `projection_epoch`, which is the test that the projection really is derived and not a second source of truth.

### Scope

Included: the `trash_entries` projection and its event consumer, the rebuild job, the kind registry and its registration mechanism, the trash index route with ACL prefiltering and filters, restore through the owning repository with parent and permission checks, retention countdown and the expiry sweep, legal-hold refusal, purge-now under `compliance-admin`, the trash screen, and the recovery test suite.

Excluded: the per-entity soft delete and restore routes themselves, which stay with their owning features (F005, F006, F013, F017, F021, F023, F045); retention policies, legal holds, tenant export, purge proposal and confirmation, and access review (F027); cell-level undo and cell history (F008); version history for documents (F045); the audit log reader (F003); archive as a distinct lifecycle state, which this feature does not introduce.

## 3. UX specification

- Entry points: the workspace overflow menu item `Trash`; the route `/trash`, and `/trash?kind=row` from a sheet's `Deleted rows` link.
- Primary flow: an editor deletes the wrong sheet, opens `Trash`, sees `Cutover plan · Sheet · deleted 4 minutes ago by you · 30 days left`, selects it, clicks `Restore`, and the sheet is back in `Northfield Delivery / Migration` with its rows. A second row, `Vendor scorecard`, shows `Blocked · folder Procurement was deleted` with `Restore parent first`; restoring the folder clears the block and the row becomes restorable.
- Loading: table skeleton with the filter bar live; Empty: `Nothing has been deleted in the last 30 days` with a line explaining retention; Error: banner with `correlation_id` and retry; Denied: a member without read access on any workspace sees the empty state, not a denied page, because absence is the correct answer; Stale: a banner `Showing what we knew 3 minutes ago` with `Refresh` when `stale` is true; Offline: restore and purge disabled with an offline badge; Success: toast `Cutover plan restored` with `Open`.
- Restore dialog: names the item, its destination path, and the count of children the owning feature will bring back; a blocked item's dialog is replaced by the reason and the parent link.
- Purge dialog: destructive variant, states that it cannot be undone, requires retyping the item title, and is unreachable without `compliance-admin`; a held item shows the hold name and a disabled action.
- Responsive: filters collapse into a single menu under 900 px; the table drops `parent_path` and `deleted_by` columns under 768 px, keeping title, kind and countdown.
- Keyboard: the table is a grid with roving focus, `r` restores the focused row, `Delete` opens the purge dialog, both dialogs trap focus and return it to the originating row.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for the countdown (F062); Lucide icons `Trash2`, `Undo2`, `AlertTriangle`, `Lock`, `Clock`, `Filter`; tokens from `apps/web/src/design/tokens.css`.
- Design: `design/artboards/Trash.dc.html`, generated by `design/generator/trash.py` and indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

### Rust backend

- Data access (decision section 2.1): `crates/persistence/src/trash/` holds exactly one class, `TrashEntryRepository`, which owns `trash_entries` and is its only writer. Named queries: `upsert_from_event`, `delete_by_source`, `list_visible_page` (the ACL-joined index read), `find_for_action`, `mark_blocked`, `clear_blocked`, `mark_state`, `list_expired_batch`, `count_by_kind_and_state`, `replace_epoch`, `delete_previous_epoch`, `max_applied_version`. No generic query escape hatch exists. Every module below depends on this trait and contains no SQL, no pool and no connection. The feature never writes another feature's table: restore and purge call the owning repository through the kind port, and the base contract applies the tenant predicate, the soft-delete filter, the audit row and the outbox enqueue.
- Domain entities in `crates/domain/src/trash/`: `TrashEntry { id, tenant_id, kind: KindKey, item_id, title, parent: Option<ItemRef>, parent_path, workspace_id, deleted_at, deleted_by, expires_at, state: Restorable|Blocked|Held|Expired, blocked_reason: Option<BlockedReason>, held, source_event_id, source_version, projection_epoch, projected_at }`, `ItemRef { kind: KindKey, id }`, `TrashKindSpec { key, resource, deleted_event, restored_event, target: &'static dyn TrashTarget }`, `TrashRegistry { by_key: BTreeMap<KindKey, &'static TrashKindSpec> }`.
- Registry and ports in `crates/domain/src/trash/registry.rs`: `trait TrashTarget { fn describe(&self, uow, id) -> Result<Option<DeletedItem>>; fn parent_of(&self, uow, id) -> Result<Option<ItemRef>>; fn restore(&self, uow, id) -> Result<Version>; fn purge(&self, uow, id) -> Result<PurgedBlobs>; fn list_deleted(&self, uow, tenant, cursor) -> Result<Page<DeletedItem>> }`. Owning features implement it in their own module and publish it through the `linkme` distributed slice `TRASH_KINDS`; `TrashRegistry::load` collects the slice at start-up, where a failure must stop the process, and validates uniqueness and resource keys. Adding a kind touches only the owning feature.
- Use cases: `list_trash`, `restore_item`, `purge_item`, `project_event`, `rebuild_tenant`, `sweep_expired`, `resolve_blocked_state`.
- API endpoints (`services/api/src/trash/`): `GET /api/v1/trash`, `POST /api/v1/trash/{kind}/{id}/restore`, `DELETE /api/v1/trash/{kind}/{id}`. DTOs: `TrashQuery { kind?, workspace_id?, deleted_by?, deleted_after?, deleted_before?, q?, cursor?, limit? }`, `TrashEntryResponse`, `TrashPage { items, next_cursor, as_of, stale }`, `RestoreResponse { kind, item_id, version, restored_children }`. Purge returns no body.
- Worker jobs (`services/worker/src/trash/`): `project.rs` consuming `jobs.trash.project` fed by the outbox subjects of the registered kinds; `rebuild.rs` consuming `jobs.trash.rebuild` with per-tenant quota 1 and a 30-minute timeout; `sweep.rs` nightly at 03:00 tenant local, batching 500 entries, 3 retries then dead letter.
- Events: `item.restored.v1` and `item.purged.v1`, published through the outbox with the conventional envelope plus `{ kind, item_id, parent_kind, parent_id }`. Deletion itself publishes nothing here — the owning feature's `<aggregate>.deleted.v1` is the only deletion event, which is what makes this a projection.
- Authorization: `editor` on the resource for list and restore, resolved through F003 against the item's surviving ACL and, for restore, additionally `<resource>:create` on the restore parent; `compliance-admin` for `DELETE`; cross-tenant maps to `not_found`. No new role is introduced.
- Validation: `kind` must be a registered key; `limit` 1–200; `q` 1–120 characters; `deleted_after` before `deleted_before`; `If-Match` on purge must equal the entry's `source_version`.
- Error mapping: `TrashError::UnknownKind → 400 invalid`, `::EntryNotFound → 404 not_found`, `::TargetMissing → 404 not_found`, `::ParentDeleted → 409 conflict`, `::VersionMismatch → 409 conflict`, `::LegalHold → 409 conflict`, `::PurgeNotPermitted → 403 denied`, `AuthzError::Denied → 403 denied`, `::RegistryUnavailable → 503 unavailable`.

### PostgreSQL/SQLx

- Migration `*_trash_*.sql` creates `trash_entries(id uuid primary key, tenant_id uuid not null, kind text not null, item_id uuid not null, title text not null, parent_kind text null, parent_id uuid null, parent_path text not null default '', workspace_id uuid null references workspaces(id) on delete restrict, deleted_at timestamptz not null, deleted_by uuid not null references users(id) on delete restrict, expires_at timestamptz null, state text not null default 'restorable' check (state in ('restorable','blocked','held','expired')), blocked_reason text null check (blocked_reason in ('parent_deleted','target_missing')), held boolean not null default false, source_event_id uuid not null, source_version bigint not null, projection_epoch bigint not null default 1, projected_at timestamptz not null, unique (tenant_id, kind, item_id))`.
- Why the row carries no `version` and no updated-actor columns: it is a projection with no user-editable field, so there is nothing to lock optimistically. Concurrency is settled by `source_version` — `upsert_from_event` applies `on conflict (tenant_id, kind, item_id) do update ... where excluded.source_version > trash_entries.source_version`, which makes replay and out-of-order delivery harmless without a lock. The consistency claim is the rebuild equivalence test in NFR-F070-05, not a constraint.
- Why `kind` is `text` with no check constraint, against the default in decision section 2: this enum is extended by later features and its members carry behaviour — a restore port, a purge port, an event name — which cannot live in a lookup row. The closed set is `TRASH_KINDS`, validated by `TrashRegistry::load` at start-up and by `TrashEntryRepository::upsert_from_event` on every write, so an unregistered kind can never reach the table; pinning it with a check constraint would instead make every new kind a migration. `blocked_reason` and `state` carry no behaviour and keep their check constraints.
- `parent_path` is a derived, rebuildable cache in the sense decision section 2 permits: it serves the index's `Where it was` column without joining eight owning tables per page, it is never filtered or sorted on, and `trash.rebuild` is the job that rebuilds it. No `jsonb` column exists in this module; the event payload the projector reads is the outbox row's, owned by F004, and nothing of it is stored here beyond `source_event_id` and `source_version`. There is no array column: an entry has exactly one kind and one parent.
- Invariants: `unique (tenant_id, kind, item_id)` makes the projection idempotent; `check ((parent_kind is null) = (parent_id is null))`; `check (state <> 'blocked' or blocked_reason is not null)`; `check (state <> 'held' or held)`; an entry exists only while the owning row has a non-null `deleted_at`, asserted by the rebuild equivalence test rather than by a cross-table constraint, since a foreign key cannot span eight polymorphic parents — the residual risk the threat model already accepts for polymorphic references, with the same mitigation: the kind is checked and the target is resolved inside the writing transaction.
- Indexes: `trash_entries(tenant_id, deleted_at desc, id)` for the default page, `trash_entries(tenant_id, kind, deleted_at desc)` and `trash_entries(tenant_id, deleted_by, deleted_at desc)` for the filters, `trash_entries(tenant_id, workspace_id, deleted_at desc)` for the workspace scope, `trash_entries(tenant_id, expires_at) where state <> 'held'` for the sweep, `trash_entries(tenant_id, parent_kind, parent_id) where state = 'blocked'` so restoring a parent can find its blocked children, and `trash_entries(tenant_id, projection_epoch)` so `delete_previous_epoch` is a single indexed statement.
- Audit events: `trash.list` is not audited (it is a read of what the caller may already read); `trash.restore` and `trash.purge` are, each with kind, item id, title, parent reference, hold check result and correlation id; the purge additionally writes the F027 `purge.executed` event through the shared executor so one purge is never recorded twice under two different names.
- Retention/deletion: entries carry no independent retention — they live exactly as long as the owning row's soft-deleted state does, and the F027 sweep removing that row removes the entry with it. Migration rollback drops `trash_entries` and its indexes; no other feature's data is touched, which is the property that makes this feature safe to remove.

### React/TypeScript

- Route `/trash` in `apps/web/src/features/trash/`; components `TrashPage`, `TrashFilters`, `TrashTable`, `TrashRow`, `RestoreDialog`, `PurgeDialog`, `BlockedReason`, `StaleBanner`, `EmptyTrash`, composed from the F062 primitives with `DataGridPanel` for the table.
- State: TanStack Query keys `['trash', filters, cursor]` with a 30-second refetch while the tab is focused, `['trash-entry', entryId]`; a restore or purge invalidates `['trash']` and the owning feature's list key so the item reappears where it belongs without a reload.
- API client: generated `TrashApi` with `listTrash`, `restoreItem`, `purgeItem`; no hand-written server types.
- Telemetry: `trash_opened`, `trash_filtered`, `trash_restore_attempted`, `trash_restore_blocked`, `trash_purge_confirmed`, each with `kind` and the outcome code.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F070-01 through FR-F070-12 and NFR-F070-01 through NFR-F070-05 in `testing/features/F070/requirements/cases.md`
- [ ] Failure/edge-case tests: replayed and out-of-order deletion events, a restoration event arriving before its deletion, restore of a child under a deleted parent, restore when the owning row was hard-purged, purge with a stale `If-Match`, purge under a hold, sweep meeting a hold, rebuild interrupted mid-epoch
- [ ] Permission-negative and tenant-isolation tests: an item the caller could not read is absent from the list and returns `not_found` by id; a caller who may read a row but not write its destination folder is denied restore; an `editor` is denied purge; a foreign-tenant kind and id return `not_found` on all three routes; a scoped token cannot exceed its stored scope
- [ ] Rust unit tests: `crates/domain/src/trash/` registry loading and duplicate-key refusal, version comparison in the projector, blocked-state resolution, expiry arithmetic against a null and a set policy
- [ ] API contract/integration tests: the three routes with every success and error code, cursor stability across a concurrent delete, and `stale` flipping at the 120-second bound
- [ ] Database migration/constraint tests: unique key rejects a duplicate entry, the state and blocked-reason checks hold, the sweep index is used, rollback drops the table
- [ ] React component tests: `TrashTable`, `BlockedReason`, `RestoreDialog`, `PurgeDialog`, `StaleBanner`, `EmptyTrash` states
- [ ] Browser E2E tests: delete a sheet and restore it; delete a folder and its child sheet, see the block, restore the parent, then the child; attempt a purge as an editor and see it disabled
- [ ] Accessibility tests: axe on `/trash` and both dialogs, roving grid focus, state not by colour alone
- [ ] Performance/load tests: 200,000-entry tenant page latency, projection lag under a 5,000-event burst, rebuild duration

### Fast fanout configuration

- Test harness path: `testing/features/F070/`
- Feature flag: `F070_FEATURE`
- Fixture/seed factory: `testing/fixtures/trash.rs` builds tenants A and B, an editor, a member with no access to workspace `Procurement`, a compliance administrator, three registered live kinds plus a test-double kind, a deleted sheet with 40 rows, a deleted folder holding a deleted sheet, a held document, and a 200,000-entry generator
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC, a scripted event stream with declared out-of-order permutations
- Mock/stub contracts: an in-memory `TrashTarget` double recording restore and purge calls, a `LegalHoldPort` stub with a programmable held set, a `RetentionPolicyPort` stub returning 30 days and null, and a `PurgeExecutorPort` spy asserting the shared audited path was used
- Parallel isolation: one schema per test worker, one tenant per test, one JetStream subject prefix per worker
- Targeted command: `cargo xtask test-feature F070`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F070/`

## 6. Acceptance criteria

```gherkin
Feature: Trash and recovery

Scenario: A deleted sheet is found and restored
  Given an editor deleted the sheet "Cutover plan" from folder "Migration"
  When they open the trash and restore it
  Then the sheet and its rows are back in "Migration", item.restored.v1 is published, and the entry is gone

Scenario: Restoring a child under a deleted parent is refused
  Given the folder "Procurement" and the sheet "Vendor scorecard" inside it are both deleted
  When an editor restores the sheet
  Then the response is 409 conflict with code parent_deleted naming the folder, and nothing is written

Scenario: Trash does not reveal what the caller could not read
  Given a member with no access to workspace "Procurement"
  When they list the trash and then request the deleted sheet by id
  Then no entry from "Procurement" appears and the id returns 404 not_found

Scenario: A legal hold beats the retention policy
  Given a deleted document under an active legal hold and past its retention expiry
  When the sweep runs and a compliance administrator then purges it directly
  Then the sweep skips it and records it as held, and the purge returns 409 conflict with code legal_hold

Scenario: The projection is derived, not a second truth
  Given a randomized stream of deletions, restorations and out-of-order redeliveries
  When trash.rebuild runs for the tenant
  Then the rebuilt rows equal the incrementally projected rows apart from projected_at and projection_epoch
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F005 (workspaces and folders, and the folder update event carrying `deleted_at`); F006 (sheets and rows, the first two registered kinds); F003 for permission evaluation and audit; F004 for the outbox and job transport; F027 for retention policies, legal holds and the shared purge executor; F062 for the UI primitives; decisions sections 2, 2.1, 3, 4, 7; contracts row F070
- Blocks: nothing; later kinds register themselves
- Conflicts with: none (disjoint owned paths; the only table written is `trash_entries`)
- External dependencies: none
- Risks and mitigations: the projection drifting from the owning tables, mitigated by the rebuild equivalence test and the rule that no decision reads the projection; an ACL post-filter silently leaking titles, mitigated by making the prefilter a join and testing the page-size invariant; a purge path that bypasses F027's audit, mitigated by routing every purge through `PurgeExecutorPort` and asserting it with a spy; a later feature registering a kind whose restore is not idempotent, mitigated by a registry conformance suite each owning feature runs in its own harness
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F005 and F006 accepted and archived, with their deletion and restoration events published through the outbox
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F070/`
- [ ] Migration file name and owned paths claimed
- [ ] `TrashTarget` implementations for `sheet`, `row` and `folder` agreed with the F005 and F006 owners

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Rebuild equivalence proven and recorded as evidence
- [ ] Audit events verified for every restore and purge, and the purge spy proves the F027 path was used
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets`, `check-contracts`, `check-persistence`, `check-roles` and `check-design` pass
- [ ] Rollback verified: disable `F070_FEATURE`, run the down migration, confirm no owning feature changes behaviour
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Everything deleted across sheets, rows, views, folders, documents, files, reports and dashboards now appears in one Trash screen with where it came from, who deleted it and how long is left; an editor can restore it in place, and a compliance administrator can destroy it immediately. Restore is checked against the destination's permissions, refuses to orphan a child under a deleted parent, and a legal hold refuses any purge.
- Migration adds `trash_entries`; rollback drops it. The index is a rebuildable projection of the owning features' soft deletes and holds no data of its own. Feature is off by default behind `F070_FEATURE`.
