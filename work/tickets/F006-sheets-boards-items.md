---
id: F006
type: feature
status: planned
priority: P0
owner: platform
estimate: 8
target_milestone: M1
parent_epic: E002
depends_on: [F005]
blocks: [F007, F016, F017]
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/sheets/**, services/api/src/sheets/**, apps/web/src/features/sheets/**, services/api/migrations/*_sheets_*.sql, testing/features/F006/**]
feature_flag: F006_FEATURE
flag_default: off
branch: f006-sheets-boards-items
started_at: null
finished_at: null
---

# F006 — Sheets/boards/items

## 1. Identity and dates

- Branch: `f006-sheets-boards-items`
- Capability area: core work record engine (spec 5.1 WORK-01, WORK-02, 5.2 DATA-01, section 4 record rules)
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4; `docs/capability-contracts.md` row F006
- Aggregate: `sheet`
- Module slug: `sheets`

## 2. Requirement specification

### Problem and user outcome

A team has no canonical place to model work. They need to create a sheet inside a workspace, add rows that represent work items, group rows, and see the same rows in a grid and a board. Every later feature (columns, formulas, views, forms, reports) reads from these records.

As a workspace editor, I want to create sheets and rows with stable IDs and version history, so that my team's work has one source of truth that other features and integrations can reference safely.

### Functional requirements

- **FR-F006-01:** An actor with the `sheet-editor` role on a workspace can create a sheet with `name`, `workspace_id`, optional `folder_id`, and optional `description`; the response returns a UUIDv7 `id`, `version` 1, and the default `Primary` text column reference.
- **FR-F006-02:** Sheet names are unique per folder within a tenant (case-insensitive); a duplicate returns error code `conflict` with `field_errors.name`.
- **FR-F006-03:** An actor can list sheets in a workspace with cursor pagination, filter by `folder_id`, `name` prefix, and `deleted=true|false`, and sort by `name` or `updated_at`.
- **FR-F006-04:** An actor can update sheet `name`, `description`, `folder_id`, and `settings` (`row_numbering`, `default_view`, `board_lane_column_id`) with `If-Match` version; a stale version returns `conflict` with the current version in the body.
- **FR-F006-05:** Deleting a sheet is a soft delete that hides the sheet and its rows from lists and reads; `POST /restore` within the tenant retention window restores the sheet, its rows, and its groups with their original `id` values.
- **FR-F006-06:** An actor can create a row in a sheet with an ordered `cells` map keyed by column ID, optional `group_id`, and optional `after_row_id`; the row receives a stable UUIDv7 `id`, a fractional `position` key, and `version` 1.
- **FR-F006-07:** Row reads and lists return `id`, `sheet_id`, `group_id`, `position`, `version`, `cells` (raw value, display value, validation state), audit fields, and `deleted_at`; lists page by cursor in `position` order with `limit` up to 500.
- **FR-F006-08:** `POST /api/v1/rows/{id}/move` changes `group_id` and/or `position` relative to `after_row_id`; the move emits `row.moved.v1` and never changes the row `id`.
- **FR-F006-09:** Every sheet has an ordered set of groups (board lanes and grid sections); a default group named `Ungrouped` exists and cannot be deleted; deleting a non-default group moves its rows to the default group.
- **FR-F006-10:** Every mutation requires `Idempotency-Key`; replaying the same key with the same body returns the original response and performs no second write; the same key with a different body returns `conflict`.
- **FR-F006-11:** Every mutation writes an `audit_events` row with actor, action, before/after diff, and correlation ID, and publishes the matching `sheet.*.v1` or `row.*.v1` event through the outbox.
- **FR-F006-12:** Cross-tenant access to any sheet or row by ID returns `not_found`, never `denied`, so IDs do not leak existence.
- **FR-F006-13:** The web app renders a sheet in grid mode (rows by position, groups as sections) and board mode (groups as lanes), and dragging a card between lanes calls the move endpoint and reflects the new version.
- **FR-F006-14:** A viewer without edit rights sees the grid and board read-only with the denied state on edit affordances; a user with no access to the workspace sees the not-found state.

### Non-functional requirements

- **NFR-F006-01 Performance:** listing 500 rows of a 100,000-row sheet responds in under 500 ms p95 with a warm cache; single-row create responds in under 800 ms p95 (spec section 6).
- **NFR-F006-02 Security/privacy:** tenant isolation enforced in the service layer and by a `tenant_id` predicate on every query; cross-tenant and unauthorized-role tests are part of the harness.
- **NFR-F006-03 Accessibility:** grid and board pass axe checks with no serious violations; all row and lane actions are reachable by keyboard; screen readers announce lane moves.
- **NFR-F006-04 Reliability/observability:** every request has a tracing span with `tenant_id`, `sheet_id`, and `correlation_id`; outbox publish failure does not lose the write and surfaces in `outbox_events` metrics.

### Scope

Included: sheet CRUD, soft delete and restore, row CRUD, row move, groups, idempotency, optimistic concurrency, audit, outbox events, grid and board rendering with the primary column, sheet settings.

Excluded: typed columns beyond the primary text column (F007), inline cell editing and bulk edits (F008), hierarchy and links (F009), formulas (F035), search and import (F010), saved views (F013), comments (F016), attachments (F017), live patches (F046).

## 3. UX specification

- Entry points: workspace tree item `New sheet`; route `/w/{workspace_id}/sheets/{sheet_id}` with `?mode=grid|board`; folder context menu `Restore` for deleted sheets.
- Primary flow: open workspace, click `New sheet`, enter name and optional folder, submit, land on the empty grid with the primary column and one empty group; click `Add row`, type the primary value, press Enter, row appears with version 1; switch to `Board`, drag the card to another lane, card stays in the new lane after the API confirms.
- Loading: skeleton rows and lanes; Empty: illustration with `Add row` call to action; Error: inline banner with `correlation_id` and retry; Success: toast on create/restore; Stale/conflict: banner `This sheet changed` with `Reload` and the diff of changed fields; Offline: edits disabled with an offline badge.
- Permission-denied: edit affordances hidden for viewers and `denied` responses show an inline explanation; no-access renders the not-found page.
- Responsive: grid scrolls horizontally with the primary column frozen under 768 px; board lanes stack vertically under 640 px.
- Keyboard: arrow keys move focus between rows and lanes, `Enter` opens a row, `Space` picks up a card, arrows move it, `Enter` drops it, `Escape` cancels; focus ring uses the shared token; motion respects `prefers-reduced-motion`.
- Font/icon/design tokens: Inter variable, Lucide icons `Table`, `Kanban`, `Plus`, `RotateCcw`, `Trash2`; spacing and color from `apps/web/src/design/tokens.css`.

## 4. Technical specification

### Rust backend

- Domain entities: `Sheet { id, tenant_id, workspace_id, folder_id, name, description, settings: SheetSettings, version, created/updated actor+time, deleted_at }`, `SheetGroup { id, sheet_id, name, position, is_default }`, `Row { id, tenant_id, sheet_id, group_id, position: FracIndex, version, deleted_at }`, `Cell { row_id, column_id, raw: Value, display: String, validation: CellValidation }`.
- Use cases in `crates/domain/src/sheets/`: `create_sheet`, `update_sheet`, `delete_sheet`, `restore_sheet`, `list_sheets`, `create_row`, `update_row`, `delete_row`, `restore_row`, `move_row`, `list_rows`, `upsert_group`, `delete_group`.
- API endpoints (`services/api/src/sheets/`): `GET /api/v1/sheets`, `POST /api/v1/sheets`, `GET /api/v1/sheets/{id}`, `PATCH /api/v1/sheets/{id}`, `DELETE /api/v1/sheets/{id}`, `POST /api/v1/sheets/{id}/restore`, `GET /api/v1/sheets/{id}/rows`, `POST /api/v1/sheets/{id}/rows`, `GET /api/v1/rows/{id}`, `PATCH /api/v1/rows/{id}`, `DELETE /api/v1/rows/{id}`, `POST /api/v1/rows/{id}/restore`, `POST /api/v1/rows/{id}/move`. Request bodies are typed `CreateSheetRequest`, `UpdateSheetRequest`, `CreateRowRequest`, `UpdateRowRequest`, `MoveRowRequest`; responses `SheetResponse`, `RowResponse`, `Page<RowResponse>`.
- Events: `sheet.created.v1`, `sheet.updated.v1`, `sheet.deleted.v1`, `sheet.restored.v1`, `row.created.v1`, `row.updated.v1`, `row.deleted.v1`, `row.restored.v1`, `row.moved.v1`; payload per contract conventions with `changed_fields`.
- Authorization: `sheet-editor` on the workspace for mutations; `sheet-viewer` for reads; ACL inherits from workspace and folder; explicit deny wins; missing workspace access maps to `not_found`.
- Validation: name 1–200 chars, description ≤ 4,000 chars, cells map keys must be column IDs of the sheet, `limit` 1–500. Idempotency stored in `idempotency_keys(tenant_id, key, request_hash, response)` for 24 hours. Concurrency: `If-Match` version compared inside the update transaction.
- Error mapping: `SheetError::NameTaken → 409 conflict`, `SheetError::StaleVersion → 409 conflict`, `SheetError::NotFound → 404 not_found`, `AuthzError::Denied → 403 denied`, validation → `400 invalid` with `field_errors`.

### PostgreSQL/SQLx

- Migration `*_sheets_*.sql` creates `sheets(id uuid pk, tenant_id uuid not null, workspace_id uuid not null, folder_id uuid null, name text not null, description text, settings jsonb not null default '{}', version bigint not null default 1, created_by, created_at, updated_by, updated_at, deleted_at)`, `sheet_groups(id, tenant_id, sheet_id, name, position numeric, is_default bool, version, audit fields)`, `rows(id, tenant_id, sheet_id, group_id, position text not null, version, audit fields, deleted_at)`, `cells(tenant_id, row_id, column_id, raw jsonb, display text, validation jsonb, updated_at, primary key (row_id, column_id))`.
- Invariants: unique index `sheets_tenant_folder_name_idx on (tenant_id, workspace_id, coalesce(folder_id, '00000000-...'), lower(name)) where deleted_at is null`; exactly one `is_default` group per sheet enforced by partial unique index; `rows.sheet_id` and `cells.row_id` foreign keys with `on delete restrict`; `position` uses fractional indexing strings ordered by collation `C`.
- Indexes: `rows(sheet_id, position) where deleted_at is null`, `rows(tenant_id, id)`, `cells(row_id)`, `sheets(tenant_id, workspace_id, updated_at desc)`.
- Audit events: `sheet.create`, `sheet.update`, `sheet.delete`, `sheet.restore`, `row.create`, `row.update`, `row.delete`, `row.restore`, `row.move`, `group.upsert`, `group.delete` with field-level diffs.
- Retention/deletion: soft delete sets `deleted_at`; purge job from F027 removes rows older than tenant retention; migration rollback drops the four tables (no data exists before this feature).

### React/TypeScript

- Routes: `/w/:workspaceId/sheets/new`, `/w/:workspaceId/sheets/:sheetId` in `apps/web/src/features/sheets/`; components `SheetPage`, `SheetHeader`, `GridView`, `GroupSection`, `RowLine`, `BoardView`, `BoardLane`, `RowCard`, `NewSheetDialog`, `RestoreSheetDialog`.
- State: TanStack Query keys `['sheet', id]`, `['sheet-rows', id, cursor]`; mutations invalidate by key and update cached `version`.
- API client: generated `SheetsApi` from OpenAPI with `createSheet`, `updateSheet`, `deleteSheet`, `restoreSheet`, `listRows`, `createRow`, `updateRow`, `moveRow`.
- Optimistic updates: row move applies locally, rolls back on `conflict` and shows the stale banner.
- Telemetry: `sheet_created`, `sheet_opened`, `row_created`, `row_moved`, `sheet_mode_changed` with `sheet_id` and `mode`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F006-01 through FR-F006-14 in `testing/features/F006/requirements/cases.md`
- [ ] Failure/edge-case tests: duplicate name, stale version, idempotent replay with mismatched body, move to deleted group, restore after retention window
- [ ] Permission-negative and tenant-isolation tests: cross-tenant read returns `not_found`, viewer mutation returns `denied`, guest link cannot mutate
- [ ] Rust unit tests: `crates/domain/src/sheets/` position ordering, settings validation, error mapping
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: unique name index, default group invariant, foreign keys, rollback
- [ ] React component tests: `GridView`, `BoardView`, `NewSheetDialog` states
- [ ] Browser E2E tests: create sheet, add row, switch to board, drag lane, restore deleted sheet
- [ ] Accessibility tests: axe on grid and board, keyboard card move
- [ ] Performance/load tests: 100,000-row sheet list p95 under 500 ms, row create p95 under 800 ms

### Fast fanout configuration

- Test harness path: `testing/features/F006/`
- Feature flag: `F006_FEATURE`
- Fixture/seed factory: `testing/fixtures/sheets.rs` builds tenant, workspace, editor, viewer, foreign tenant, and a seeded sheet with 3 groups and 50 rows
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC
- Mock/stub contracts: outbox publisher recorded in memory; authz uses the real F003 engine with fixture bindings
- Parallel isolation: one schema per test worker, tenant ID per test
- Targeted command: `cargo xtask test-feature F006`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F006/`

## 6. Acceptance criteria

```gherkin
Feature: Sheets, rows, and groups

Scenario: Create a sheet and first row
  Given an editor in workspace "Ops"
  When they create sheet "Launch plan" and add a row with primary value "Kickoff"
  Then the sheet has version 1, a default group, and one row at the first position
  And events sheet.created.v1 and row.created.v1 are in the outbox

Scenario: Stale update is rejected
  Given sheet "Launch plan" at version 3
  When an editor patches it with If-Match 2
  Then the response is 409 conflict with current version 3 and no change is written

Scenario: Cross-tenant read does not leak
  Given a sheet in tenant A
  When an editor from tenant B requests it by id
  Then the response is 404 not_found

Scenario: Board move
  Given a row in group "Backlog"
  When a keyboard user moves its card to lane "Doing"
  Then the row has group "Doing", a new version, and row.moved.v1 is published
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F005 (workspace, folder tree, membership); decisions sections 2–4; contracts row F006
- Blocks: F007, F016, F017
- Conflicts with: none (disjoint owned paths)
- External dependencies: none
- Risks and mitigations: fractional position keys can grow unbounded under repeated inserts at the same spot, so the move service rebalances a group when any key exceeds 64 chars; large-sheet list performance depends on the `(sheet_id, position)` partial index, verified by the load test.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F005 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F006/`
- [ ] Migration file name and owned paths claimed
- [ ] Fixture factory and schema-per-worker isolation available in `testing/harness/`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F006_FEATURE`, run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Users can create sheets, groups, and rows in a workspace and switch between grid and board modes.
- Migration adds `sheets`, `sheet_groups`, `rows`, and `cells`; rollback drops them. Feature is off by default behind `F006_FEATURE`.
