---
id: S013
type: story
status: planned
parent_epic: E002
parent_feature: F007
depends_on: [F006]
owned_paths: [crates/domain/src/columns/**, services/api/src/columns/**, services/api/migrations/*_columns_*.sql, testing/features/F007/**]
feature_flag: F007_FEATURE
branch: s013-column-lifecycle
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4
- Capability contract: `docs/capability-contracts.md` row F007

# S013 — Column lifecycle

## Identity

- Parent feature: `F007` Typed columns
- Owner: platform
- Branch: `s013-column-lifecycle`
- Decision references: `docs/architecture-decisions.md` sections 2–4; `docs/capability-contracts.md` row F007

## Vertical slice

As a sheet editor, I want to create, list, rename, reorder, hide, retype, and soft-delete typed columns with select options through the API, so that a sheet has a stable typed schema before any cell editing or validation UI exists.

## Requirements

- **SR-S013-01:** `POST /api/v1/sheets/{sheet_id}/columns` with `{ type, label, description?, required?, width?, settings?, validation?, options? }` writes `columns` and `column_options` in one transaction and returns `ColumnResponse` with version 1 and a position after the last column (covers FR-F007-01, FR-F007-07).
- **SR-S013-02:** The 501st non-deleted column returns `400 invalid` with `field_errors.sheet_id = "column_limit"` under a sheet row lock (FR-F007-02).
- **SR-S013-03:** A duplicate case-insensitive label in the same sheet returns `409 conflict` with `field_errors.label = "taken"` (FR-F007-03).
- **SR-S013-04:** `PATCH /api/v1/columns/{id}` renames without changing `id`, and cells keyed by the column id still resolve; `If-Match` mismatch returns `409 conflict` with `current_version` (FR-F007-04, FR-F007-16).
- **SR-S013-05:** A `type` change allowed by the conversion matrix re-normalizes cells and returns `preview.invalid_count`; an unsupported pair returns `400 invalid` with `field_errors.type = "unsupported_conversion"` (FR-F007-05, FR-F007-06).
- **SR-S013-06:** `POST /api/v1/columns/{id}/reorder` assigns a fractional position, rebalances keys over 64 chars, keeps the primary column first, and emits `column.reordered.v1` (FR-F007-12, FR-F007-13).
- **SR-S013-07:** `DELETE` soft-deletes a non-primary column and hides its cells; deleting, hiding, or retyping the primary column returns `400 invalid` with `field_errors.is_primary` (FR-F007-13, FR-F007-14).
- **SR-S013-08:** Every mutation checks `Idempotency-Key`, writes an audit event, enqueues the matching `column.*.v1` outbox event, and a foreign-tenant actor receives `404 not_found` on every route (FR-F007-16).

## Surfaces

- Infrastructure/container: none beyond F004 baseline
- Rust service/API: `crates/domain/src/columns/{mod.rs, column.rs, types.rs, settings.rs, conversion.rs, position.rs, errors.rs, service.rs}`; `services/api/src/columns/{mod.rs, routes.rs, handlers_column.rs, handlers_reorder.rs, dto.rs}`
- Data/migration: `services/api/migrations/<ts>_columns_create_tables.sql` creating `columns`, `column_options`, `cell_validation_states`, and `cells.normalized` with indexes from ticket section 4
- React/UI: none in this story (S014 and T027 cover UI)
- Mocks/fixtures: `testing/fixtures/columns.rs` sheet with one column per type, editor, viewer, foreign tenant; in-memory outbox recorder

## TDD harness

- Test path: `testing/features/F007/api/` and `testing/features/F007/database/`
- Feature flag: `F007_FEATURE`
- Targeted command: `cargo xtask test-feature F007`
- Full command: `cargo xtask test-all`
- First failing tests: `column_create_returns_version_one`, `column_limit_501_rejected`, `column_duplicate_label_conflicts`, `column_rename_keeps_id_and_cells`, `column_type_change_previews_invalid`, `column_reorder_keeps_primary_first`, `column_cross_tenant_not_found`

## Exit criteria

- [ ] Requirement tests SR-S013-01 through SR-S013-08 written first and failing
- [ ] Tasks T025 and T026 complete and wired through `services/api` router
- [ ] Unit, API, database, permission tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/columns/routes.rs` mounted in `services/api/src/router.rs`
- [ ] Handoff evidence recorded in the F007 ticket
