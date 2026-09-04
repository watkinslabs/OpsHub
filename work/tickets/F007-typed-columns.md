---
id: F007
type: feature
status: planned
priority: P0
owner: platform
estimate: 8
target_milestone: M1
parent_epic: E002
depends_on: [F006]
blocks: [F008, F009, F035, F011, F014, F018]
conflicts_with: []
parallel_safe: true
owned_paths: [crates/persistence/src/columns/**, crates/domain/src/columns/**, services/api/src/columns/**, apps/web/src/features/columns/**, services/api/migrations/*_columns_*.sql, testing/features/F007/**]
feature_flag: F007_FEATURE
flag_default: off
branch: f007-typed-columns
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 6, 9
- Capability contract: `docs/capability-contracts.md` row F007

# F007 — Typed columns

## 1. Identity and dates

- Branch: `f007-typed-columns`
- Capability area: core work record engine (spec 5.1 WORK-01, WORK-02; section 4 Column entity and record rules; section 6 scale targets)
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 6; `docs/capability-contracts.md` row F007
- Aggregate: `column`
- Module slug: `columns`

## 2. Requirement specification

### Problem and user outcome

F006 gives every sheet a single primary text column. Teams cannot yet model statuses, owners, due dates, priorities, budgets, or tags, and nothing checks that a cell holds a value of the right shape. Every later feature (grid editing, hierarchy, formulas, dates, forms, workflows) needs a typed schema with stable column IDs and a validation state per cell.

As a sheet editor, I want to add typed columns with options and validation rules to a sheet, rename and reorder them without breaking anything that references them, and see which cells violate the rules, so that my team's data stays consistent and downstream features can trust it.

### Functional requirements

- **FR-F007-01:** An actor with `sheet-editor` on the sheet can create a column with `type` in exactly `text, number, currency, date, datetime, boolean, person, link, file, select, formula, duration`, a `label` of 1–120 chars, and optional `description`, `required`, `width` (40–1,000 px), type settings (one `column_settings` row), and validation rules (one `column_validation_rules` row per rule); the response returns a UUIDv7 `id`, a fractional `position` after the last column, and `version` 1.
- **FR-F007-02:** A sheet holds at most 500 non-deleted columns; the 501st create returns `invalid` with `field_errors.sheet_id = "column_limit"` and writes nothing.
- **FR-F007-03:** Column labels are unique per sheet (case-insensitive) among non-deleted columns; a duplicate returns `conflict` with `field_errors.label = "taken"`.
- **FR-F007-04:** Renaming a column changes only `label`; the column `id` is immutable, and cells, formulas, links, views, and reports keyed by `id` continue to resolve after the rename.
- **FR-F007-05:** `PATCH /api/v1/columns/{id}` accepts `label`, `description`, `required`, `width`, `hidden`, the `column_settings` fields, the validation rule set (replaced atomically as `column_validation_rules` rows), and `type`; a `type` change is accepted only when the conversion matrix in section 4 allows it, otherwise the response is `invalid` with `field_errors.type = "unsupported_conversion"`.
- **FR-F007-06:** A `type` change or a change to the column's validation rules re-normalizes every cell in the column inside the same transaction for sheets up to 10,000 rows and as an async job above that; the response includes `preview.invalid_count` (cells that will hold state `invalid`) and `preview.mode = "sync" | "async"`.
- **FR-F007-07:** `select` columns own an ordered list of `column_options` with `label`, `color` (one of 12 token names), and `archived`; archiving an option keeps existing cells valid but rejects new writes of that option; `column_settings.multi = true` allows a cell to hold more than one option ID.
- **FR-F007-08:** `number`, `currency`, and `duration` columns store `raw` as the user-entered string, `normalized` as a decimal (scale from `column_settings.precision`, 0–8) or ISO 8601 duration, and `display` formatted with `column_settings.currency_code` (ISO 4217) or `column_settings.display_format`; a non-numeric input yields validation state `invalid` with code `type_mismatch`.
- **FR-F007-09:** `date` and `datetime` columns normalize to ISO 8601 (`YYYY-MM-DD` or RFC 3339 in UTC) and accept `column_settings.display_format` for display; `person` columns store a user ID that must belong to the tenant, otherwise state `invalid` with code `unknown_person`.
- **FR-F007-10:** Validation rules are `required`, `min`/`max` (number, currency, duration, date, datetime), `regex` (text, RE2 syntax, ≤ 512 chars), `allowed_options` (select), `date_range`, and `unique` (text, number); each rule is one `column_validation_rules` row whose `rule` column carries the name and whose typed bound columns carry the parameters, and each failure records state `invalid` with the rule name as `code` and a message in `cell_validation_states`.
- **FR-F007-11:** `POST /api/v1/columns/{id}/validate` enqueues a job that evaluates every cell of the column, acknowledges in under 2 s with `{ job_id, status: "queued" }`, writes one `cell_validation_states` row per cell, and returns `{ status, valid_count, invalid_count, checked_at }` on the same route via `GET`-style polling of the job record included in the column response.
- **FR-F007-12:** `POST /api/v1/columns/{id}/reorder` with `{ after_column_id? }` assigns a new fractional `position`, rebalances the sheet when any key exceeds 64 chars, and emits `column.reordered.v1`; the primary column always keeps the first position.
- **FR-F007-13:** The primary column cannot be deleted, hidden, or changed to a non-`text` type; such requests return `invalid` with `field_errors.is_primary`.
- **FR-F007-14:** `DELETE /api/v1/columns/{id}` is a soft delete that hides the column and its cells from reads and marks dependent formulas (F035) and links (F009) with state `missing reference`; restore is performed by the sheet restore path of F006 and keeps the column `id`.
- **FR-F007-15:** `formula` and `link` columns are created here as shells with no expression and no target row of their own; the expression lives in the F035 `formula_definitions` row and the target in the F009 link tables, set only through F035 and F009 routes, and cells of these types are read-only through cell writes.
- **FR-F007-16:** Every mutation requires `Idempotency-Key` and `If-Match`, writes an `audit_events` row with a field diff, and publishes the matching `column.*.v1` event; cross-tenant access to any column returns `not_found`.
- **FR-F007-17:** The web app lets an editor add, edit, reorder, hide, and delete columns from the grid header and a column editor drawer, shows the type-change preview count before confirming, and renders per-cell validation state as an icon with the message in a tooltip and in the accessible name.

### Non-functional requirements

- **NFR-F007-01 Performance:** listing 500 columns of a sheet responds in under 500 ms p95; column create and patch without re-normalization respond in under 800 ms p95; the validate job over 100,000 rows completes in under 60 s and its acknowledgement returns in under 2 s (spec section 6).
- **NFR-F007-02 Security/privacy:** every query carries a `tenant_id` predicate; `person` values are validated against tenant users only; regex rules are compiled with RE2 semantics and a 10 ms match budget per cell to prevent catastrophic backtracking; role and cross-tenant negatives are part of the harness.
- **NFR-F007-03 Accessibility:** the column editor drawer, option list editor, and validation rule editor pass axe with zero serious violations, trap focus, and are fully keyboard operable; validation icons expose their message through `aria-describedby`.
- **NFR-F007-04 Reliability/observability:** every request span carries `tenant_id`, `sheet_id`, `column_id`, and `correlation_id`; validate jobs record `job_runs` entries with duration and counts; outbox publish failure rolls back the mutation.

### Scope

Included: column CRUD, the twelve column types with normalization and display formatting, select options, validation rule engine and per-cell validation state, type conversion matrix with preview, reorder, hide, soft delete, audit and outbox events, column editor UI, validation icons in the grid header and cells.

Excluded: inline cell editing, undo, and bulk edits (F008), link targets and rollups (F009), formula expressions and recalculation (F035), working calendars and timezone rendering rules (F011), form field mapping (F014), conditional formatting (F060).

## 3. UX specification

- Entry points: grid header `+` button at the end of the column strip; column header menu (`Edit column`, `Insert left`, `Insert right`, `Hide`, `Delete`); route `/w/{workspace_id}/sheets/{sheet_id}?column={column_id}` opens the drawer for deep links.
- Primary flow: editor clicks `+`, picks type `select` from a type list with icons, types label `Status`, adds options `Todo`, `Doing`, `Done` with colors, toggles `required`, saves; the column appears at the end of the grid with version 1; editor drags the header before `Owner`, the API confirms the reorder; editor changes type `text` to `number` on `Estimate`, the preview shows `3 cells will become invalid`, editor confirms, cells show validation icons.
- Loading: header skeleton while `['columns', sheetId]` loads; Empty: sheet with only the primary column shows `Add your first column` hint; Error: inline banner with `correlation_id` and retry; Success: toast `Column added`; Stale/conflict: drawer shows `This column changed` with reload; Offline: drawer save disabled with an offline badge.
- Permission-denied: viewers and commenters see headers without the menu and cannot open the drawer; `denied` responses render an inline explanation; no access to the sheet renders the not-found page.
- Responsive: the drawer becomes a full-screen sheet under 768 px; header menus open as bottom sheets under 640 px.
- Keyboard: header receives focus in the tab order, `Enter` opens the menu, `Alt+ArrowLeft/Right` reorders, `Delete` prompts removal; drawer traps focus, `Escape` closes without saving; option list supports `Alt+ArrowUp/Down` reorder; motion respects `prefers-reduced-motion`.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide icons `Type`, `Hash`, `DollarSign`, `Calendar`, `Clock`, `ToggleLeft`, `User`, `Link`, `Paperclip`, `List`, `Sigma`, `Timer`, `AlertCircle`, `EyeOff`, `GripVertical`; tokens from `apps/web/src/design/tokens.css`.

## 4. Technical specification

Canonical contract: `docs/capability-contracts.md` row F007.

### Rust backend

- Domain entities in `crates/domain/src/columns/`: `Column { id, tenant_id, sheet_id, column_type: ColumnType, label, description, required, is_primary, position: FracIndex, width, hidden, settings: ColumnSettings, validation: Vec<ValidationRule>, version, created/updated actor+time, deleted_at }` where `ColumnSettings` is the column's one `column_settings` row and `Vec<ValidationRule>` its `column_validation_rules` rows, both loaded and replaced with the column, `ColumnOption { id, tenant_id, column_id, label, color: ColorToken, position, archived }`, `CellValidationState { tenant_id, row_id, column_id, state: ValidationState (Valid | Invalid | Pending), code: Option<ValidationCode>, message: Option<String>, checked_at }`.
- `ColumnType` enum in `crates/domain/src/columns/types.rs` with the twelve variants; each variant implements `normalize(raw: &Value, settings: &ColumnSettings, ctx: &TenantContext) -> Result<Normalized, ValidationCode>` and `display(normalized, settings) -> String`; `ValidationCode` is `required | min | max | regex | allowed_options | date_range | unique | type_mismatch | unknown_person | unsupported_conversion`.
- Conversion matrix in `crates/domain/src/columns/conversion.rs`: `text → any` (re-normalize), `number ↔ currency`, `number → text`, `date → datetime`, `datetime → date` (truncate), `select → text` (option label), `text → select` (create options from distinct values up to 200), `boolean → text`; every other pair is unsupported; `formula`, `link`, and `file` never convert.
- Data access (decision 2.1): `ColumnRepository` (`columns`, `column_settings`, `column_validation_rules`), `ColumnOptionRepository` (`column_options`), and `CellValidationStateRepository` (`cell_validation_states`) in `crates/persistence/src/columns/`; each table is written by exactly one of them, and cell re-normalization writes `cells` through the F006 `CellRepository` instead of a second SQL path. The use cases below, the validation engine, and the async re-normalization job depend on those repository traits and the shared `UnitOfWork` and contain no SQL.
- Use cases: `create_column`, `update_column`, `change_column_type`, `delete_column`, `list_columns`, `reorder_column`, `upsert_options`, `validate_column`, `renormalize_cells`; validation engine `crates/domain/src/columns/validation.rs` exposes `evaluate(rules, normalized, ctx) -> ValidationOutcome` and is reused by F008 cell writes and F014 form submissions.
- API endpoints (`services/api/src/columns/`): `GET /api/v1/sheets/{sheet_id}/columns`, `POST /api/v1/sheets/{sheet_id}/columns`, `PATCH /api/v1/columns/{id}`, `DELETE /api/v1/columns/{id}`, `POST /api/v1/columns/{id}/reorder`, `POST /api/v1/columns/{id}/validate`. DTOs `CreateColumnRequest`, `UpdateColumnRequest`, `ReorderColumnRequest`, `ColumnResponse { id, sheet_id, type, label, description, required, is_primary, position, width, hidden, settings, validation, options, version, last_validation: { job_id, status, valid_count, invalid_count, checked_at }, audit fields }`, `TypeChangePreview { invalid_count, mode }`, `ValidateJobResponse { job_id, status }`.
- Events: `column.created.v1`, `column.updated.v1`, `column.deleted.v1`, `column.reordered.v1` with `changed_fields`; validate completion updates `column.updated.v1` with `changed_fields = ["last_validation"]`.
- Authorization: `sheet-editor` on the sheet for every mutation; `sheet-viewer` for list; explicit deny wins; unknown or foreign-tenant sheet maps to `not_found`.
- Validation and limits: label 1–120 chars, description ≤ 2,000 chars, width 40–1,000, precision 0–8, ≤ 200 options per column, ≤ 16 validation rules per column with at most one row per rule name, regex ≤ 512 chars compiled by `regex` crate (RE2), 500 columns per sheet checked with a row lock on `sheets`. Async re-normalization above 10,000 rows runs as a JetStream job consumed by the F004 worker runtime calling `renormalize_cells` in batches of 1,000.
- Error mapping: `ColumnError::LabelTaken → 409 conflict`, `ColumnError::Limit → 400 invalid (column_limit)`, `ColumnError::UnsupportedConversion → 400 invalid`, `ColumnError::PrimaryImmutable → 400 invalid`, `ColumnError::StaleVersion → 409 conflict`, `ColumnError::NotFound → 404 not_found`, `AuthzError::Denied → 403 denied`.

### PostgreSQL/SQLx

- Migration `*_columns_*.sql` creates `columns(id uuid pk, tenant_id uuid not null, sheet_id uuid not null references sheets(id) on delete restrict, type text not null check (type in (...twelve...)), label text not null, description text, required bool not null default false, is_primary bool not null default false, position text not null collate "C", width int not null default 160, hidden bool not null default false, version bigint not null default 1, created_by, created_at, updated_by, updated_at, deleted_at)`, `column_settings(column_id uuid primary key references columns(id) on delete cascade, tenant_id uuid not null, precision smallint check (precision between 0 and 8), currency_code char(3), display_format text, multi bool not null default false, time_zone text, updated_by uuid, updated_at timestamptz not null)`, `column_validation_rules(tenant_id uuid not null, column_id uuid not null references columns(id) on delete cascade, rule text not null check (rule in ('required','min','max','regex','allowed_options','date_range','unique')), min_number numeric, max_number numeric, min_datetime timestamptz, max_datetime timestamptz, pattern text, message text, created_by uuid, created_at timestamptz not null, primary key (column_id, rule))`, `column_options(id uuid pk, tenant_id, column_id references columns(id) on delete restrict, label text not null, color text not null, position text not null collate "C", archived bool not null default false, version, audit fields)`, `cell_validation_states(tenant_id, row_id uuid references rows(id), column_id uuid references columns(id), state text not null check (state in ('valid','invalid','pending')), code text, message text, checked_at timestamptz not null, primary key (row_id, column_id))`.
- Neither column settings nor validation rules are `jsonb`: the product reads `precision`, `currency_code`, `display_format`, and `multi` by name on every normalization and constrains their ranges, and it evaluates, edits, counts, and audits rules individually, so both are tables (decision 2). One `column_settings` row per column is created with the column by a trigger, so the former empty settings object and the new row mean the same thing; `column_validation_rules` primary key `(column_id, rule)` makes a duplicate rule impossible where the old array could hold two, and a check constraint per rule name requires exactly the bound columns that rule uses (`min`/`max` a number or datetime bound, `regex` a `pattern`, `date_range` both datetime bounds).
- Invariants: partial unique index `columns_sheet_label_idx on (tenant_id, sheet_id, lower(label)) where deleted_at is null`; partial unique index `columns_sheet_primary_idx on (sheet_id) where is_primary and deleted_at is null`; check `width between 40 and 1000`; `column_options_column_label_idx on (column_id, lower(label)) where not archived`; the 500-column limit is enforced in the service under `select ... for update` on the sheet row.
- Indexes: `columns(sheet_id, position) where deleted_at is null`, `columns(tenant_id, id)`, `column_validation_rules(tenant_id, rule)` so the engine can find every column carrying a given rule, `column_options(column_id, position)`, `cell_validation_states(column_id, state)` for invalid counts, `cell_validation_states(tenant_id, row_id)`.
- The F006 `cells` table gains `normalized jsonb` through an additive nullable column in this migration, with the F006 down migration untouched. `normalized` stays `jsonb` for the same reason as `raw`: it is one user-defined typed cell value whose shape follows the tenant's column type, never a structure the product queries by key (decision 2). This migration also moves the interim `cells.validation_state`, `validation_code`, and `validation_message` columns from F006 into `cell_validation_states`, copying every non-default row first and dropping the three columns afterwards, declared and justified as a destructive statement per the F044 migration gate; the down migration recreates the columns and copies the rows back, so the cell-level validation behaviour F006 shipped is unchanged and there is only one source of truth for it.
- Audit events: `column.create`, `column.update`, `column.type_change`, `column.delete`, `column.reorder`, `column.options_upsert`, `column.validate` with field-level diffs and counts.
- Retention/deletion: soft delete sets `deleted_at`; purge follows F027; rollback drops `column_options`, `cell_validation_states`, `column_validation_rules`, `column_settings`, `columns`, and the `cells.normalized` column, and restores the three `cells.validation_*` columns.

### React/TypeScript

- Routes: none new; components mount inside the F006 `SheetPage` header slot from `apps/web/src/features/columns/`: `ColumnHeaderMenu`, `ColumnEditorDrawer`, `TypePicker`, `OptionListEditor`, `ValidationRuleEditor`, `TypeChangePreview`, `ValidationIcon`, `AddColumnButton`.
- State: TanStack Query keys `['columns', sheetId]`, `['column-validation', columnId]`; mutations `createColumn`, `updateColumn`, `deleteColumn`, `reorderColumn`, `validateColumn` invalidate `['columns', sheetId]` and update cached `version`; validation polling every 2 s while status is `queued` or `running`.
- API client: generated `ColumnsApi` from OpenAPI; type change first calls `updateColumn` with `dry_run: true` to obtain `TypeChangePreview`, then commits.
- Optimistic updates: reorder applies locally and rolls back on `conflict` with the stale banner; hide toggles locally.
- Telemetry: `column_created`, `column_type_changed`, `column_validated`, `column_reordered` with `sheet_id`, `column_id`, `type`, and `invalid_count`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F007-01 through FR-F007-17 in `testing/features/F007/requirements/cases.md`
- [ ] Failure/edge-case tests: 501st column, duplicate label, unsupported conversion, regex over 512 chars, archived option write, primary delete, stale version, idempotent replay
- [ ] Permission-negative and tenant-isolation tests: viewer create returns `denied`, foreign tenant returns `not_found`, person value from another tenant is `invalid`
- [ ] Rust unit tests: `crates/domain/src/columns/` normalization per type, conversion matrix, validation rules, position rebalancing
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: label index, primary index, type check, validation state primary key, rollback
- [ ] React component tests: `ColumnEditorDrawer`, `OptionListEditor`, `TypeChangePreview`, `ValidationIcon` states
- [ ] Browser E2E tests: add select column, reorder, change type with preview, validate column, viewer read-only
- [ ] Accessibility tests: axe on drawer and header menu, keyboard reorder, validation icon names
- [ ] Performance/load tests: 500-column list p95, create p95, validate 100,000 rows under 60 s

### Fast fanout configuration

- Test harness path: `testing/features/F007/`
- Feature flag: `F007_FEATURE`
- Fixture/seed factory: `testing/fixtures/columns.rs` builds tenant, sheet with 12 columns (one per type), 20 select options, 500 rows with mixed valid and invalid values, editor, viewer, foreign tenant
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC, currency `USD`
- Mock/stub contracts: outbox recorded in memory; job queue replaced by an inline executor for sync tests and the real JetStream consumer for the performance lane; authz uses the real F003 engine
- Parallel isolation: one schema per test worker, tenant ID per test
- Targeted command: `cargo xtask test-feature F007`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F007/`

## 6. Acceptance criteria

```gherkin
Feature: Typed columns and validation

Scenario: Add a select column with options
  Given an editor on sheet "Launch plan"
  When they create column "Status" of type select with options Todo, Doing, Done and required true
  Then the column has version 1 and three options in order
  And column.created.v1 is in the outbox

Scenario: Type change previews invalid cells
  Given text column "Estimate" with values "5", "12", "n/a"
  When the editor changes the type to number
  Then the preview reports invalid_count 1
  And after confirmation the cell "n/a" has validation state invalid with code type_mismatch

Scenario: Viewer cannot add columns
  Given a viewer on sheet "Launch plan"
  When they POST a column
  Then the response is 403 denied and no column is written

Scenario: Rename keeps references
  Given formula column "Total" referencing column "Estimate" by id
  When the editor renames "Estimate" to "Effort"
  Then the formula still resolves and column.updated.v1 lists changed_fields ["label"]
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F006 (sheets, rows, cells, primary column); decisions sections 2–4, 6; contracts row F007
- Blocks: F008, F009, F035, F011, F014, F018
- Conflicts with: none (disjoint owned paths)
- External dependencies: `regex` crate for RE2 semantics; `rust_decimal` for number and currency normalization
- Risks and mitigations: synchronous re-normalization on large sheets can exceed the write budget, so sheets above 10,000 rows use the async job and cells show `pending` until it completes; `text → select` on high-cardinality data can create hundreds of options, so the conversion caps at 200 distinct values and reports `invalid` for the rest; regex rules could be slow, so RE2 semantics and a per-cell budget are enforced.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F006 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F007/`
- [ ] Migration file name and owned paths claimed
- [ ] Fixture factory and schema-per-worker isolation available in `testing/harness/`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F007_FEATURE`, run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Users can add twelve typed column types with options and validation rules, reorder and hide columns, and see invalid cells flagged.
- Migration adds `columns`, `column_settings`, `column_validation_rules`, `column_options`, `cell_validation_states`, and `cells.normalized`, and folds the interim `cells.validation_*` columns into `cell_validation_states`; rollback removes them. Feature is off by default behind `F007_FEATURE`.
