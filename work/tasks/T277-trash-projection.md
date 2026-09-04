---
id: T277
type: task
status: planned
parent_epic: E003
parent_feature: F070
parent_story: S139
depends_on: [S139]
owned_paths: [services/api/migrations/*_trash_*.sql, crates/persistence/src/trash/**, crates/domain/src/trash/**, services/worker/src/trash/**, testing/features/F070/database/**, testing/features/F070/api/**]
feature_flag: F070_FEATURE
branch: t277-trash-projection
started_at: null
finished_at: null
---

# T277 — Trash projection

## Identity

- Parent story: `S139` Trash index
- Owner: platform
- Branch: `t277-trash-projection`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 7; `docs/capability-contracts.md` row F070

## Objective

Create the `trash` schema, the `TrashEntryRepository`, the kind registry that later features register into, and the event consumer and rebuild job that keep `trash_entries` a derived projection of the owning features' soft deletes.

## Specification

- Owned paths: `services/api/migrations/<ts>_trash_create_tables.sql` and `.down.sql`, `crates/persistence/src/trash/{mod.rs, entry_repository.rs, queries.rs}`, `crates/domain/src/trash/{mod.rs, entry.rs, registry.rs, projector.rs, errors.rs}`, `services/worker/src/trash/{mod.rs, project.rs, rebuild.rs}`
- Contract/input: JetStream subjects for the registered kinds' deletion and restoration events — `sheet.deleted.v1`, `sheet.restored.v1`, `row.deleted.v1`, `row.restored.v1`, `view.deleted.v1`, `document.deleted.v1`, `document.restored.v1`, `file.deleted.v1`, `report.deleted.v1`, `dashboard.deleted.v1` — plus `folder.updated.v1` filtered on `changed_fields` containing `deleted_at`; the rebuild job takes `{ tenant_id }`.
- Output/behavior: DDL for `trash_entries` exactly as ticket section 4 declares it, including the `(tenant_id, kind, item_id)` unique key, the `state` and `blocked_reason` checks, the parent-pair check, and the six indexes; `entry_repository.rs` exposes `upsert_from_event`, `delete_by_source`, `list_visible_page`, `find_for_action`, `mark_blocked`, `clear_blocked`, `mark_state`, `list_expired_batch`, `count_by_kind_and_state`, `replace_epoch`, `delete_previous_epoch` and `max_applied_version`, with `upsert_from_event` writing `on conflict (tenant_id, kind, item_id) do update ... where excluded.source_version > trash_entries.source_version` so replay and out-of-order delivery are harmless; `registry.rs` defines `TrashKindSpec`, the `TrashTarget` trait and `TrashRegistry::load`, which collects the `linkme` distributed slice `TRASH_KINDS`, refuses a duplicate kind key or a resource key absent from the authorization model, and aborts start-up on failure; `projector.rs` maps an event to an upsert or a delete, drops a tenant mismatch, and resolves `expires_at` through `RetentionPolicyPort` and `held` through `LegalHoldPort`; `rebuild.rs` writes a whole tenant under a new `projection_epoch` from each kind's `list_deleted` port and deletes the previous epoch in the same `UnitOfWork`.
- Data access: `projector.rs`, `registry.rs`, `project.rs` and `rebuild.rs` hold no SQL; every read and write goes through `TrashEntryRepository` and, for other features' tables, through `TrashTarget`, so no two classes write the same table (decision section 2.1).
- Dependencies: F004 outbox and job transport; F005 and F006 `TrashTarget` implementations for `folder`, `sheet` and `row`; F027 `RetentionPolicyPort` and `LegalHoldPort`; F003 audit.
- Feature flag: `F070_FEATURE` gates the consumer and the rebuild job; the migration runs regardless.

## TDD

- Failing test first: `testing/features/F070/database/migration_tests.rs::trash_entries_exists_with_constraints`, `::duplicate_kind_and_item_rejected`, `::state_requires_blocked_reason`, `::sweep_index_used_for_expiry_scan`, `::rollback_drops_trash_entries`; `testing/features/F070/api/projection_tests.rs::projector_upserts_entry_from_sheet_deleted`, `::projector_discards_older_source_version`, `::projector_deletes_entry_on_restored_event`, `::projector_records_folder_update_carrying_deleted_at`, `::projector_drops_foreign_tenant_event`, `::rebuild_matches_incremental_projection`, `::rebuild_epoch_swap_is_atomic`; `testing/features/F070/api/registry_tests.rs::registry_refuses_duplicate_kind_key`, `::registry_refuses_unknown_resource_key`, `::registry_accepts_a_kind_declared_outside_this_module`
- Targeted command: `cargo xtask test-feature F070`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/trash.rs`; an in-memory `TrashTarget` double, a scripted out-of-order event stream with declared permutations, `RetentionPolicyPort` and `LegalHoldPort` stubs, fixed clock `2026-09-03T00:00:00Z`

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; consumer and rebuild job registered behind the flag
- [ ] `cargo xtask check-persistence` passes: no SQL outside `crates/persistence/src/trash/`, no array column, no unjustified `jsonb`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S139
- [ ] `finished_at` recorded
