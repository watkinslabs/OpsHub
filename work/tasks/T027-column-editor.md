---
id: T027
type: task
status: planned
parent_epic: E002
parent_feature: F007
parent_story: S014
depends_on: [T026]
owned_paths: [apps/web/src/features/columns/**, testing/features/F007/frontend/**, testing/features/F007/accessibility/**]
feature_flag: F007_FEATURE
branch: t027-column-editor
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` section 6
- Capability contract: `docs/capability-contracts.md` row F007

# T027 — Column editor

## Identity

- Parent story: `S014` Validation
- Owner: platform
- Branch: `t027-column-editor`
- Decision references: `docs/architecture-decisions.md` section 6; `docs/capability-contracts.md` row F007

## Objective

Build the column header menu, editor drawer, option and rule editors, type-change preview, and per-cell validation icon wired to the real column API inside the F006 sheet page.

## Specification

- Owned paths: `apps/web/src/features/columns/{ColumnHeaderMenu.tsx, ColumnEditorDrawer.tsx, TypePicker.tsx, OptionListEditor.tsx, ValidationRuleEditor.tsx, TypeChangePreview.tsx, ValidationIcon.tsx, AddColumnButton.tsx, api.ts, hooks.ts, index.ts}`
- Contract/input: generated `ColumnsApi` client; props `sheetId`, `columnId`, `role`; query `column={column_id}` opens the drawer; type change performs `updateColumn` with `dry_run: true` and shows `TypeChangePreview.invalid_count` before commit.
- Output/behavior: header menu offers `Edit column`, `Insert left`, `Insert right`, `Hide`, `Delete` (primary column hides `Hide`, `Delete`, and type change); drawer edits label, description, type, required, width, settings, options, and rules with field-level errors from `field_errors`; reorder by drag or `Alt+ArrowLeft/Right` calls `reorderColumn` optimistically and rolls back on `conflict` with the stale banner; `validateColumn` shows a progress chip polling every 2 s; `ValidationIcon` renders `AlertCircle` with the message in `aria-describedby`; states: loading skeleton, empty hint, error banner with correlation ID, denied affordances hidden for viewers, offline badge disabling save; Lucide icons and tokens per ticket section 3; telemetry `column_created`, `column_type_changed`, `column_validated`, `column_reordered`.
- Dependencies: T026 routes; F006 `SheetPage` header slot and `GridView` cell renderer hook for the validation icon.
- Feature flag: `F007_FEATURE` read through the flag hook; the header slot renders nothing when off.

## TDD

- Failing test first: `testing/features/F007/frontend/ColumnEditorDrawer.test.tsx::creates_select_column_with_options`, `::shows_field_error_for_duplicate_label`, `::drawer_type_change_shows_preview_count`, `ColumnHeaderMenu.test.tsx::primary_column_hides_delete_and_hide`, `::keyboard_reorder_calls_api_and_rolls_back_on_conflict`, `ValidationIcon.test.tsx::exposes_message_in_accessible_name`; `testing/features/F007/accessibility/columns.a11y.spec.ts::drawer_and_menu_have_no_serious_axe_violations`
- Targeted command: `cargo xtask test-feature F007`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: MSW handlers from the one-column-per-type fixture; axe-core through Playwright for the accessibility lane

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Component and accessibility lanes pass
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S014
- [ ] `finished_at` recorded
