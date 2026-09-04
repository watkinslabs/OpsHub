---
id: T278
type: task
status: planned
parent_epic: E003
parent_feature: F070
parent_story: S139
depends_on: [S139, T277]
owned_paths: [crates/domain/src/trash/**, services/api/src/trash/**, testing/features/F070/api/**]
feature_flag: F070_FEATURE
branch: t278-restore-service
started_at: null
finished_at: null
---

# T278 — Restore service

## Identity

- Parent story: `S139` Trash index
- Owner: platform
- Branch: `t278-restore-service`
- Decision references: `docs/architecture-decisions.md` sections 2.1, 3, 4; `docs/capability-contracts.md` row F070; `docs/authorization-model.md` sections 1 and 3.3

## Objective

Implement the trash index read with its ACL prefilter and the restore path with its destination permission check, parent-deleted refusal and `item.restored.v1` publication.

## Specification

- Owned paths: `crates/domain/src/trash/{service.rs, visibility.rs, restore.rs}`, `services/api/src/trash/{mod.rs, routes.rs, handlers_index.rs, handlers_restore.rs, dto.rs}`
- Contract/input: `TrashQuery { kind?, workspace_id?, deleted_by?, deleted_after?, deleted_before?, q?, cursor?, limit? }` with `limit` 1–200 default 50 and `q` 1–120 characters; restore takes the path kind and item id plus `Idempotency-Key`.
- Output/behavior: `GET /api/v1/trash` returns `TrashPage { items, next_cursor, as_of, stale }` of `TrashEntryResponse` ordered by `deleted_at desc, entry_id`, with `stale` true when `as_of` is more than 120 seconds behind the request clock; `visibility.rs` builds the predicate that `TrashEntryRepository::list_visible_page` joins against `resource_acls`, so filtering happens before paging and a full page is returned while more visible rows exist; `POST /api/v1/trash/{kind}/{id}/restore` resolves the live row through `TrashTarget::describe`, evaluates `<resource>:create` on the parent returned by `TrashTarget::parent_of` and `<resource>:update` on the item against their current ACLs through F003, calls `TrashTarget::restore` and deletes the entry in one `UnitOfWork`, publishes `item.restored.v1` with `{ kind, item_id, parent_kind, parent_id }`, writes the `trash.restore` audit event, and returns `RestoreResponse { kind, item_id, version, restored_children }`; a soft-deleted parent returns `409 conflict` code `parent_deleted` with `field_errors.parent_id` naming the parent kind, title and entry id and marks the entry `blocked`; a missing owning row returns `404 not_found` and `blocked_reason: target_missing`; error mapping is the single table in ticket section 4 and no handler invents a status code.
- Data access: `service.rs`, `visibility.rs`, `restore.rs` and the three handler modules hold no SQL; reads and writes go through `TrashEntryRepository` and `TrashTarget`, and the restore commits in one `UnitOfWork` (decision section 2.1).
- Dependencies: T277 for the repository, registry and projection; F003 for permission evaluation and audit; F005 and F006 for the three live kind ports.
- Feature flag: `F070_FEATURE` gates both routes.

## TDD

- Failing test first: `testing/features/F070/api/index_tests.rs::index_orders_by_deleted_at_then_entry_id`, `::index_filters_by_kind_workspace_person_and_date`, `::index_page_is_acl_joined_not_post_filtered`, `::index_reports_stale_past_the_120_second_bound`, `::index_rejects_limit_above_200`; `testing/features/F070/api/restore_tests.rs::restore_puts_sheet_back_and_publishes_restored`, `::restore_checks_destination_parent_acl`, `::restore_under_deleted_parent_conflicts_with_parent_named`, `::restore_of_missing_target_returns_not_found`, `::restore_of_held_item_succeeds`, `::restore_is_idempotent_under_replayed_key`; `testing/features/F070/api/negative_tests.rs::invisible_entry_returns_not_found`, `::foreign_tenant_entry_returns_not_found`, `::reader_without_destination_write_is_denied`, `::deleter_identity_grants_nothing`
- Targeted command: `cargo xtask test-feature F070`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/trash.rs`; tenants A and B, an editor, a member with no access to workspace `Procurement`, a deleted folder holding a deleted sheet, and the in-memory `TrashTarget` double recording restore calls

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Routes mounted in `services/api/src/router.rs` behind the flag; OpenAPI regenerated without drift
- [ ] Permission-negative and cross-tenant cases pass
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S139
- [ ] `finished_at` recorded
