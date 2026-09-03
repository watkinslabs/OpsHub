---
id: S011
type: story
status: planned
parent_epic: E002
parent_feature: F006
depends_on: [F005]
owned_paths: [crates/domain/src/sheets/**, services/api/src/sheets/**, services/api/migrations/*_sheets_*.sql, testing/features/F006/**]
feature_flag: F006_FEATURE
branch: s011-create-sheet
started_at: null
finished_at: null
---

# S011 — Create sheet

## Identity

- Parent feature: `F006` Sheets/boards/items
- Owner: platform
- Branch: `s011-create-sheet`
- Decision references: `docs/architecture-decisions.md` sections 2–4; `docs/capability-contracts.md` row F006

## Vertical slice

As a workspace editor, I want to create, read, update, soft-delete, and restore a sheet with its default group, so that my team has a canonical container for rows before any column or row features exist.

## Requirements

- **SR-S011-01:** `POST /api/v1/sheets` with `{ name, workspace_id, folder_id?, description? }` creates `sheets` and `sheet_groups` rows in one transaction and returns `SheetResponse` with version 1 (covers FR-F006-01, FR-F006-09).
- **SR-S011-02:** Duplicate case-insensitive name in the same folder returns `409 conflict` with `field_errors.name = "taken"` (FR-F006-02).
- **SR-S011-03:** `GET /api/v1/sheets` pages by opaque cursor, filters by `folder_id`, `name` prefix, `deleted`, and sorts by `name` or `updated_at` (FR-F006-03).
- **SR-S011-04:** `PATCH /api/v1/sheets/{id}` requires `If-Match`; stale version returns `409 conflict` with `current_version` (FR-F006-04).
- **SR-S011-05:** `DELETE` sets `deleted_at`; `POST /restore` clears it on the sheet, groups, and rows and keeps IDs (FR-F006-05).
- **SR-S011-06:** Every mutation checks `Idempotency-Key`, writes an audit event, and enqueues the matching `sheet.*.v1` outbox event (FR-F006-10, FR-F006-11).
- **SR-S011-07:** A foreign-tenant actor receives `404 not_found` for every sheet route (FR-F006-12).

## Surfaces

- Infrastructure/container: none beyond F004 baseline
- Rust service/API: `crates/domain/src/sheets/{sheet.rs, group.rs, errors.rs, service.rs}`; `services/api/src/sheets/{routes.rs, handlers_sheet.rs, dto.rs}`
- Data/migration: `services/api/migrations/<ts>_sheets_create_tables.sql` creating `sheets`, `sheet_groups`, `rows`, `cells` with indexes from ticket section 4
- React/UI: none in this story (S012 and T024 cover UI)
- Mocks/fixtures: `testing/fixtures/sheets.rs` tenant/workspace/editor/viewer/foreign-tenant builders; in-memory outbox recorder

## TDD harness

- Test path: `testing/features/F006/api/` and `testing/features/F006/database/`
- Feature flag: `F006_FEATURE`
- Targeted command: `cargo xtask test-feature F006`
- Full command: `cargo xtask test-all`
- First failing tests: `sheet_create_returns_version_one`, `sheet_duplicate_name_conflicts`, `sheet_stale_version_conflicts`, `sheet_cross_tenant_not_found`, `sheet_restore_keeps_ids`

## Exit criteria

- [ ] Requirement tests SR-S011-01 through SR-S011-07 written first and failing
- [ ] Tasks T021 and T022 complete and wired through `services/api` router
- [ ] Unit, API, database, permission tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/sheets/routes.rs` mounted in `services/api/src/router.rs`
- [ ] Handoff evidence recorded in the F006 ticket
