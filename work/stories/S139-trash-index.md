---
id: S139
type: story
status: planned
parent_epic: E003
parent_feature: F070
depends_on: [F005, F006]
owned_paths: [crates/domain/src/trash/**, crates/persistence/src/trash/**, services/api/src/trash/**, services/worker/src/trash/**, services/api/migrations/*_trash_*.sql, testing/features/F070/**]
feature_flag: F070_FEATURE
branch: s139-trash-index
started_at: null
finished_at: null
---

# S139 — Trash index

## Identity

- Parent feature: `F070` Trash and recovery
- Owner: platform
- Branch: `s139-trash-index`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 7; `docs/capability-contracts.md` row F070; `docs/authorization-model.md` sections 1 and 3.3

## Vertical slice

As an editor, I want one API that lists everything I could read and someone deleted, and one that puts a chosen item back where it came from, so that recovery no longer depends on knowing which object type I lost and which per-entity restore route owns it.

This slice delivers the projection and the two read/restore paths end to end: the `trash_entries` table and its repository, the kind registry that later features register into, the event consumer and rebuild job that keep the projection derived, `GET /api/v1/trash` with its ACL prefilter, and `POST /api/v1/trash/{kind}/{id}/restore` with the destination permission check and the parent-deleted refusal.

## Requirements

- **SR-S139-01:** `trash_entries` is created by `services/api/migrations/<ts>_trash_create_tables.sql` with the columns, checks, unique key and six indexes from ticket section 4, and is reached only through `TrashEntryRepository` in `crates/persistence/src/trash/`, which is its only writer (covers FR-F070-03, NFR-F070-04).
- **SR-S139-02:** `TrashRegistry::load` collects the `linkme` slice `TRASH_KINDS` at start-up, refuses to boot on a duplicate kind key or a resource key absent from `docs/authorization-model.md`, and exposes `sheet`, `row` and `folder` from the F005 and F006 modules plus any kind a later feature registers without changing this feature's files (covers FR-F070-05).
- **SR-S139-03:** The `trash.project` consumer upserts one entry per `(tenant_id, kind, item_id)` from the registered deletion events and from `folder.updated.v1` whose `changed_fields` contains `deleted_at`, discards an event whose `version` is not greater than `source_version`, deletes the entry on a restoration event, and drops an event whose tenant does not match (covers FR-F070-03, FR-F070-11, NFR-F070-04).
- **SR-S139-04:** `trash.rebuild` re-derives a tenant's entries through each kind's `list_deleted` port under a new `projection_epoch` and deletes the previous epoch in the same `UnitOfWork`, and its output equals the incrementally projected rows apart from `projected_at` and `projection_epoch` (covers FR-F070-04, NFR-F070-05).
- **SR-S139-05:** `GET /api/v1/trash` pages by cursor over `deleted_at desc, entry_id`, applies the `kind`, `workspace_id`, `deleted_by`, `deleted_after`, `deleted_before` and `q` filters, and returns `as_of` and `stale` computed from the projector's last applied event time against the 120-second bound (covers FR-F070-01, NFR-F070-01).
- **SR-S139-06:** Visibility is an ACL join, not a post-filter: an entry appears only when F003 grants `<resource>:read` on the deleted item's surviving ACL, a full page is returned while more visible rows exist, and an invisible item's id returns `not_found` rather than `denied` (covers FR-F070-02, FR-F070-11, NFR-F070-02).
- **SR-S139-07:** `POST /api/v1/trash/{kind}/{id}/restore` resolves the live row through the owning repository, checks `<resource>:create` on the restore parent and `<resource>:update` on the item against their current ACLs, restores through `TrashTarget::restore` in one `UnitOfWork`, publishes `item.restored.v1`, deletes the entry, and returns the new `version` (covers FR-F070-06).
- **SR-S139-08:** Restore refuses to orphan: a deleted parent yields `409 conflict` with code `parent_deleted` naming the parent's kind, title and entry id with no write, the entry is marked `blocked` with `blocked_reason: parent_deleted`, and a missing owning row yields `404 not_found` with `blocked_reason: target_missing` (covers FR-F070-07).
- **SR-S139-09:** A member without access to the item's workspace sees no entry and gets `not_found`; a caller who may read the item but not write its destination gets `403 denied` on restore; foreign-tenant ids return `not_found` on both routes (covers FR-F070-02, FR-F070-11, NFR-F070-02).

## Surfaces

- Data access: `crates/persistence/src/trash/{mod.rs, entry_repository.rs, queries.rs}` holds every SQL statement for this slice; `crates/domain/src/trash`, the `services/api/src/trash` handlers and the `services/worker/src/trash` jobs depend on the repository trait and contain no `sqlx::query*` call, pool or connection; restore and rebuild run their multi-table work in one `UnitOfWork` and reach other features' tables only through `TrashTarget` (decision section 2.1)
- Rust service/API: `crates/domain/src/trash/{mod.rs, entry.rs, registry.rs, service.rs, projector.rs, errors.rs}`; `services/api/src/trash/{mod.rs, routes.rs, handlers_index.rs, handlers_restore.rs, dto.rs}`; `services/worker/src/trash/{mod.rs, project.rs, rebuild.rs}`
- Data/migration: `services/api/migrations/<ts>_trash_create_tables.sql` and its `.down.sql`, creating `trash_entries` with the unique key `(tenant_id, kind, item_id)` and the six indexes from ticket section 4
- Ports consumed: `TrashTarget` implementations for `sheet`, `row` and `folder` declared in the F005 and F006 modules; `RetentionPolicyPort` and `LegalHoldPort` from F027 for `expires_at` and `held`
- Mocks/fixtures: `testing/fixtures/trash.rs`; an in-memory `TrashTarget` double, a scripted out-of-order event stream, and a fixed clock

## TDD harness

- Test path: `testing/features/F070/{api,database,requirements}/`
- Feature flag: `F070_FEATURE`
- Targeted command: `cargo xtask test-feature F070`
- Full command: `cargo xtask test-all`
- First failing tests: `registry_refuses_duplicate_kind_key`, `projector_discards_older_source_version`, `projector_records_folder_update_carrying_deleted_at`, `rebuild_matches_incremental_projection`, `index_page_is_acl_joined_not_post_filtered`, `restore_checks_destination_parent_acl`, `restore_under_deleted_parent_conflicts`, `invisible_entry_returns_not_found`

## Exit criteria

- [ ] Requirement tests SR-S139-01 through SR-S139-09 written first and observed failing
- [ ] Tasks T277 and T278 complete and wired through the `services/api` router and the `services/worker` registry
- [ ] Unit, API, database and permission tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/trash/routes.rs` mounted in `services/api/src/router.rs` at `/api/v1/trash`; `services/worker/src/trash/project.rs` and `rebuild.rs` registered in `services/worker/src/registry.rs`
- [ ] Handoff evidence recorded in the F070 ticket
