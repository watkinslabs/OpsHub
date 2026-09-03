---
id: T036
type: task
status: planned
parent_epic: E002
parent_feature: F009
parent_story: S018
depends_on: [T035]
owned_paths: [apps/web/src/features/links/**, testing/features/F009/frontend/**, testing/features/F009/e2e/**, testing/features/F009/accessibility/**]
feature_flag: F009_FEATURE
branch: t036-relationship-ui
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 4, 6, 9
- Capability contract: `docs/capability-contracts.md` row F009

# T036 — Relationship UI

## Identity

- Parent story: `S018` Linked records
- Owner: platform
- Branch: `t036-relationship-ui`
- Decision references: `docs/architecture-decisions.md` sections 4, 6, 9; `docs/capability-contracts.md` row F009

## Objective

Build the hierarchy controls, child outline, linked-cell renderer, link picker, and roll-up rule editor with treegrid semantics and keyboard indent, wired to the real hierarchy, link, and rollup routes.

## Specification

- Owned paths: `apps/web/src/features/links/{HierarchyControls.tsx, IndentGuide.tsx, ChildRowsOutline.tsx, LinkPicker.tsx, LinkedCellRenderer.tsx, BrokenLinkBadge.tsx, RollupRuleEditor.tsx, RollupCellRenderer.tsx, api.ts, hooks.ts, index.ts}`
- Contract/input: generated `LinksApi` client (`indentRow`, `outdentRow`, `listChildren`, `listLinks`, `createLink`, `updateLink`, `deleteLink`, `setRollupRule`); mount points: `HierarchyControls` in the F008 `VirtualGrid` row toolbar, `LinkedCellRenderer` and `RollupCellRenderer` registered in the F008 cell renderer registry for `link` and rolled-up columns, `RollupRuleEditor` in the F007 `ColumnHeaderMenu`.
- Output/behavior: rows render `role="row"` inside a `treegrid` with `aria-level`, `aria-expanded`, `aria-setsize`, and indent guides; `Tab`/`Shift+Tab` on a focused row (outside cell edit) call indent/outdent optimistically and roll back on `invalid` or `conflict` with the reason in a toast; `ArrowRight`/`ArrowLeft` expand and collapse and fetch `['row-children', rowId]`; `LinkedCellRenderer` shows a chip `<primary value> · <sheet name>`, a `Restricted` chip for redacted targets, and an amber `BrokenLinkBadge` with tooltip for `status = broken`; `LinkPicker` searches readable target sheets and rows with debounce 300 ms and creates the link on select; `RollupCellRenderer` shows shimmer for `pending` and a lock tooltip "Computed from children"; `RollupRuleEditor` offers only functions valid for the column type and validates weight and priority inputs; states: loading, empty, error banner with correlation ID, denied affordances hidden for viewers, conflict banner; Lucide icons and design tokens per ticket section 3; telemetry `row_indented`, `row_outdented`, `subtree_expanded`, `link_created`, `link_removed`, `link_broken_viewed`, `rollup_configured`.
- Dependencies: T035 routes and events; F008 grid renderer registry and row toolbar; F007 column header menu.
- Feature flag: `F009_FEATURE` read through the flag hook; controls and renderers are not registered when off.

## TDD

- Failing test first: `testing/features/F009/frontend/HierarchyControls.test.tsx::tab_indents_and_shift_tab_outdents`, `::rolls_back_on_depth_exceeded`, `::hides_controls_for_viewer`; `LinkedCellRenderer.test.tsx::linked_cell_shows_broken_state`, `::redacted_target_shows_restricted_chip`; `LinkPicker.test.tsx::lists_only_readable_sheets`; `RollupRuleEditor.test.tsx::offers_only_compatible_functions`; `testing/features/F009/e2e/hierarchy.spec.ts::indent_row_and_see_rollup_sum`, `::link_to_vendor_and_break_on_delete`; `testing/features/F009/accessibility/links.a11y.spec.ts::treegrid_has_no_serious_axe_violations`, `::level_change_is_announced`
- Targeted command: `cargo xtask test-feature F009`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: MSW handlers from the `Plan` and `Vendors` fixtures; Playwright uses the real API against a seeded tenant

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Component, E2E, and accessibility lanes pass
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S018
- [ ] `finished_at` recorded
