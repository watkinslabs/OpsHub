---
id: S014
type: story
status: planned
parent_epic: E002
parent_feature: F007
depends_on: [S013]
owned_paths: [crates/domain/src/columns/**, services/api/src/columns/**, apps/web/src/features/columns/**, testing/features/F007/**]
feature_flag: F007_FEATURE
branch: s014-validation
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 6, 7
- Capability contract: `docs/capability-contracts.md` row F007

# S014 — Validation

## Identity

- Parent feature: `F007` Typed columns
- Owner: platform
- Branch: `s014-validation`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 6, 7; `docs/capability-contracts.md` row F007

## Vertical slice

As a sheet editor, I want each cell normalized and checked against the column's type and validation rules, to run a full-column validation job, and to manage columns, options, and rules from the grid header, so that invalid data is visible and fixable in the real UI.

## Requirements

- **SR-S014-01:** Every `ColumnType` normalizes raw input to `normalized` and `display` per the ticket rules: decimals with `settings.precision`, ISO 4217 currency display, ISO 8601 dates and durations, tenant-checked `person`, and option IDs for `select`; non-conforming input yields state `invalid` with code `type_mismatch` or `unknown_person` (covers FR-F007-08, FR-F007-09).
- **SR-S014-02:** `evaluate(rules, normalized, ctx)` implements `required`, `min`, `max`, `regex`, `allowed_options`, `date_range`, and `unique`, recording the failing rule name as `code` and a message in `cell_validation_states` (FR-F007-10).
- **SR-S014-03:** Archived options keep existing cells `valid` but reject new writes with code `allowed_options`; `settings.multi` accepts an array of option IDs (FR-F007-07).
- **SR-S014-04:** `POST /api/v1/columns/{id}/validate` acknowledges in under 2 s with `{ job_id, status: "queued" }`, the job writes one state row per cell in batches of 1,000, and `ColumnResponse.last_validation` exposes counts and `checked_at` (FR-F007-11, NFR-F007-01).
- **SR-S014-05:** `formula` and `link` cells are read-only for cell writes and return `invalid` with `field_errors.cells` when written outside F035 or F009 (FR-F007-15).
- **SR-S014-06:** `ColumnHeaderMenu`, `ColumnEditorDrawer`, `OptionListEditor`, `ValidationRuleEditor`, and `TypeChangePreview` let an editor perform every lifecycle action, show loading, empty, error, denied, stale, and offline states, and `ValidationIcon` exposes the message in the accessible name (FR-F007-17, NFR-F007-03).
- **SR-S014-07:** The 500-column list, column create, and 100,000-row validate job meet NFR-F007-01 in the performance lane.

## Surfaces

- Infrastructure/container: JetStream job subject `columns.validate` consumed by the F004 worker runtime
- Rust service/API: `crates/domain/src/columns/{normalize.rs, validation.rs, validate_job.rs}`; `services/api/src/columns/{handlers_validate.rs, job_dispatch.rs}`; rules are loaded from `column_validation_rules` and type settings from `column_settings` through `ColumnRepository`, outcomes are written through `CellValidationStateRepository`, and normalized values through the F006 `CellRepository` — the engine, the handler, and the job hold no SQL (decision 2.1)
- Data/migration: none new; uses `column_validation_rules`, `column_settings`, `cell_validation_states`, and `cells.normalized` from S013, `cell_validation_states` being the only store of per-cell validation state
- React/UI: `apps/web/src/features/columns/{ColumnHeaderMenu.tsx, ColumnEditorDrawer.tsx, TypePicker.tsx, OptionListEditor.tsx, ValidationRuleEditor.tsx, TypeChangePreview.tsx, ValidationIcon.tsx, AddColumnButton.tsx, api.ts, hooks.ts}`
- Mocks/fixtures: 500-row mixed validity sheet; 100,000-row generator for the performance lane; inline job executor; MSW handlers for component tests

## TDD harness

- Test path: `testing/features/F007/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F007_FEATURE`
- Targeted command: `cargo xtask test-feature F007`
- Full command: `cargo xtask test-all`
- First failing tests: `number_normalizes_with_precision`, `person_outside_tenant_invalid`, `regex_rule_records_code_and_message`, `validate_job_acknowledges_under_two_seconds`, `drawer_type_change_shows_preview_count`, `validate_100k_rows_under_60s`

## Exit criteria

- [ ] Requirement tests SR-S014-01 through SR-S014-07 written first and failing
- [ ] Tasks T027 and T028 complete; UI wired to real API through generated client
- [ ] Unit, API, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `apps/web/src/features/columns/ColumnHeaderMenu.tsx` mounted in the F006 `SheetPage` header slot at `/w/:workspaceId/sheets/:sheetId`
- [ ] Handoff evidence recorded in the F007 ticket
