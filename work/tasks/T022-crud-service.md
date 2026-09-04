---
id: T022
type: task
status: planned
parent_epic: E002
parent_feature: F006
parent_story: S011
depends_on: [T021]
owned_paths: [crates/domain/src/sheets/**, services/api/src/sheets/**, testing/features/F006/api/**, testing/features/F006/requirements/**]
feature_flag: F006_FEATURE
branch: t022-crud-service
started_at: null
finished_at: null
---

# T022 — CRUD service

## Identity

- Parent story: `S011` Create sheet
- Owner: platform
- Branch: `t022-crud-service`
- Decision references: `docs/architecture-decisions.md` sections 2–4; `docs/capability-contracts.md` row F006

## Objective

Implement `SheetRepository` and `SheetGroupRepository`, the sheet domain service, and the six sheet HTTP routes with authorization, idempotency, optimistic concurrency, audit, and outbox publication.

## Specification

- Owned paths: `crates/persistence/src/sheets/{mod.rs, sheet_repository.rs, sheet_group_repository.rs}` holding every SQL statement for `sheets`, `sheet_settings`, and `sheet_groups`, `crates/domain/src/sheets/{mod.rs, sheet.rs, group.rs, errors.rs, service.rs}`, `services/api/src/sheets/{mod.rs, routes.rs, handlers_sheet.rs, dto.rs}`
- Contract/input: `CreateSheetRequest { name, workspace_id, folder_id?, description? }`, `UpdateSheetRequest { name?, description?, folder_id?, settings? { row_numbering?, default_view?, board_lane_column_id? } }`, list query `{ cursor?, limit?, folder_id?, name_prefix?, deleted?, sort? }`; headers `Idempotency-Key`, `If-Match`.
- Output/behavior: routes `GET/POST /api/v1/sheets`, `GET/PATCH/DELETE /api/v1/sheets/{id}`, `POST /api/v1/sheets/{id}/restore` return `SheetResponse { id, workspace_id, folder_id, name, description, settings { row_numbering, default_view, board_lane_column_id }, default_group_id, version, created_at, updated_at, deleted_at }` projected from the `sheet_settings` row; `SheetRepository` (`sheets`, `sheet_settings`) and `SheetGroupRepository` (`sheet_groups`) implement the shared `Repository` contract and own every statement, so `service.rs`, the handlers, and the api lane call repository traits and contain no SQL (decision 2.1); create relies on the settings trigger and update writes `sheets` and `sheet_settings` in one `UnitOfWork` transaction; errors map per ticket section 4; events `sheet.created.v1`, `sheet.updated.v1`, `sheet.deleted.v1`, `sheet.restored.v1` written to `outbox_events` in the same transaction; audit rows written via the F003 audit writer.
- Dependencies: T021 schema and triggers; F003 `authz::require(actor, Permission::SheetEdit, workspace)`; F004 outbox writer; F005 folder lookup.
- Feature flag: `F006_FEATURE` gates router mounting.

## TDD

- Failing test first: `testing/features/F006/api/sheet_tests.rs::sheet_create_returns_version_one`, `::sheet_duplicate_name_conflicts`, `::sheet_stale_version_conflicts`, `::sheet_patch_updates_settings_row`, `::sheet_idempotent_replay_returns_original`, `::sheet_cross_tenant_not_found`, `::sheet_restore_keeps_ids`, `::sheet_viewer_mutation_denied`
- Targeted command: `cargo xtask test-feature F006`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/sheets.rs` tenants A and B, editor, viewer; in-memory outbox recorder

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Router mounted in `services/api/src/router.rs` behind the flag; OpenAPI regenerated without drift
- [ ] `cargo xtask check-persistence` passes: no SQL outside `crates/persistence`, one class per table
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S011
- [ ] `finished_at` recorded
