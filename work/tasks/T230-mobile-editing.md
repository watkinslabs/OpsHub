---
id: T230
type: task
status: planned
parent_epic: E008
parent_feature: F058
parent_story: S115
depends_on: [T229]
owned_paths: [apps/web/src/features/mobile/**, testing/features/F058/frontend/**, testing/features/F058/accessibility/**, testing/features/F058/requirements/**]
feature_flag: F058_FEATURE
branch: t230-mobile-editing
started_at: null
finished_at: null
---

# T230 — Mobile editing

## Identity

- Parent story: `S115` Mobile work
- Owner: platform
- Branch: `t230-mobile-editing`
- Decision references: `docs/architecture-decisions.md` section 6; `docs/capability-contracts.md` row F058

## Objective

Build the touch-first mobile grid, cell editors, row detail page, and mobile form page that edit through the existing grid and form APIs while online.

## Specification

- Owned paths: `apps/web/src/features/mobile/{MobileGrid.tsx, MobileCellEditor.tsx, RowDetailPage.tsx, MobileFormPage.tsx, editors/TextEditor.tsx, editors/NumberEditor.tsx, editors/DateEditor.tsx, editors/SelectEditor.tsx, editors/PersonEditor.tsx, editors/BooleanEditor.tsx, hooks.ts}`
- Contract/input: F008 `PATCH /api/v1/sheets/{sheet_id}/cells` through the generated `GridApi`; F014 `POST /public/forms/{token}/submissions` and internal form routes through `FormsApi`; F017 upload routes for attachments; route params `sheetId`, `rowId`, `formId`.
- Output/behavior: grid renders the primary column plus one chosen column with horizontal swipe, 44 px targets, tap-to-edit opening the editor for the six supported types, saves with `If-Match` and shows the stale chip on `conflict`; row detail lists every column with editors and the F016 comment count; form page renders fields with conditional logic and queues attachments as uploads; states: loading skeleton, empty, error banner with correlation ID, denied lock icon, stale chip, offline bar (edits still allowed and handed to T231's queue when present), success toast; telemetry `mobile_edit_saved`, `mobile_form_submitted`.
- Dependencies: T229 shell and routes; F008 and F014 clients; F013 view settings for the chosen column.
- Feature flag: `F058_FEATURE`

## TDD

- Failing test first: `testing/features/F058/frontend/MobileGrid.test.tsx::mobile_grid_edits_cell_online`, `::swipe_changes_visible_column`, `::stale_chip_on_conflict`, `::denied_cell_shows_lock`; `testing/features/F058/frontend/RowDetailPage.test.tsx::renders_all_columns_with_editors`; `testing/features/F058/frontend/MobileFormPage.test.tsx::submits_with_conditional_fields`; `testing/features/F058/accessibility/mobile.a11y.spec.ts::grid_and_detail_touch_targets_44px`
- Targeted command: `cargo xtask test-feature F058`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: MSW handlers from the 200-row sheet and published form fixture; Vitest viewport 360 px

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Component and accessibility lanes pass at 360 px and 768 px
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S115
- [ ] `finished_at` recorded
