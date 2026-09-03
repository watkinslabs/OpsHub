---
id: T246
type: task
status: planned
parent_epic: E001
parent_feature: F062
parent_story: S123
depends_on: [T245]
owned_paths: [apps/web/src/ui/internal/**, apps/web/src/ui/primitives/**, apps/web/src/ui/icons.ts, testing/features/F062/frontend/**]
feature_flag: F062_FEATURE
branch: t246-primitive-components
started_at: null
finished_at: null
---

# T246 — Primitive components

## Identity

- Parent story: `S123` Design tokens and theming
- Owner: platform
- Branch: `t246-primitive-components`
- Decision references: `docs/architecture-decisions.md` sections 5, 6; `docs/capability-contracts.md` row F062

## Objective

Build the focus and layering modules and the closed primitive list on top of the tokens, with the keyboard and ARIA behavior each pattern requires.

## Specification

- Owned paths: `apps/web/src/ui/internal/{focus.ts, layers.ts, useControllableState.ts, useMediaQuery.ts, usePersistedState.ts}`, `apps/web/src/ui/primitives/*.tsx` and their `*.stories.tsx`, `apps/web/src/ui/icons.ts`.
- Contract/input: the primitive list in FR-F062-07 — `Button`, `IconButton`, `Input`, `Textarea`, `Select`, `Combobox`, `Checkbox`, `Radio`, `Switch`, `Slider`, `DatePicker`, `Label`, `FieldError`, `Field`, `Dialog`, `Drawer`, `Popover`, `Tooltip`, `Menu`, `Tabs`, `Accordion`, `Toast`, `Banner`, `Badge`, `Avatar`, `Spinner`, `Skeleton`, `Table`, `Pagination`, `Breadcrumb`, `SegmentedControl`, `ContextMenu`, `Separator`, `VisuallyHidden` — each with literal-union `variant` and `size` props and a `forwardRef` root.
- Output/behavior: `focus.ts` moves focus in on open, traps it, and returns it to the invoker on close; `layers.ts` keeps the ordered overlay stack so `Escape` and outside-click dismiss only the top entry and scroll locks without layout shift; overlay triggers carry `aria-expanded` and `aria-controls`; composite widgets implement roving tabindex with arrows, `Home`, `End`, and type-ahead against the WAI-ARIA pattern named in each file's doc comment; every primitive derives size from the density tokens and shows the ring on `:focus-visible` only; `Toast` queues at most 5 with a 6 s dismissal that pauses on hover and focus; `icons.ts` is the only importer of `lucide-react` and exposes sizes 14, 16, 20, 24; no primitive uses `dangerouslySetInnerHTML` and link primitives force `rel="noopener noreferrer"` with `target="_blank"`.
- Dependencies: T245 tokens; an accessible headless base for overlay and composite widgets; F001 web test runner.
- Feature flag: `F062_FEATURE` gates the `apps/web/src/ui` barrel export; nothing else imports these files while it is off.

## TDD

- Failing test first: `testing/features/F062/frontend/primitive_tests.tsx::every_exported_primitive_renders_all_variants`, `::sizes_derive_from_density_tokens`, `::focus_ring_only_on_focus_visible`, `::disabled_and_loading_states_block_interaction`; `testing/features/F062/frontend/overlay_tests.tsx::focus_returns_to_invoker_on_close`, `::nested_menu_escape_leaves_dialog_open`, `::scroll_lock_causes_no_layout_shift`, `::trigger_marks_aria_expanded_and_controls`; `testing/features/F062/frontend/keyboard_tests.tsx::roving_tabindex_moves_with_arrows_and_typeahead`, `::tabs_home_end_reach_bounds`; `testing/features/F062/frontend/safety_tests.tsx::no_primitive_renders_raw_html`, `::external_links_force_noopener`, `::icons_import_only_through_registry`
- Targeted command: `cargo xtask test-feature F062`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/design_system.ts` story matrix over states × 2 themes × 2 densities; a `fetch` spy asserting zero calls

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Every primitive has stories for its states in both themes and both densities
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S123
- [ ] `finished_at` recorded
