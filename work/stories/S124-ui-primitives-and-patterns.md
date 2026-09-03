---
id: S124
type: story
status: planned
parent_epic: E001
parent_feature: F062
depends_on: [S123]
owned_paths: [apps/web/src/ui/primitives/**, apps/web/src/ui/patterns/**, apps/web/src/ui/shell/**, apps/web/src/ui/icons.ts, apps/web/src/ui/index.ts, testing/features/F062/frontend/**, testing/features/F062/e2e/**, testing/features/F062/requirements/**]
feature_flag: F062_FEATURE
branch: s124-ui-primitives-and-patterns
started_at: null
finished_at: null
---

# S124 — UI primitives and patterns

## Identity

- Parent feature: `F062` Design system and UI primitives
- Owner: platform
- Branch: `s124-ui-primitives-and-patterns`
- Decision references: `docs/architecture-decisions.md` sections 5, 6; `docs/capability-contracts.md` row F062

## Vertical slice

As a product engineer building any OpsHub screen, I want one library of primitives, one set of composed state patterns, and one application shell, all keyboard-correct and theme-aware, so that I compose a feature from `apps/web/src/ui` instead of designing a button, a dialog, an empty state, and a table for the fifty-ninth time.

## Requirements

- **SR-S124-01:** `apps/web/src/ui/primitives/` exports the closed list of primitives in the ticket, each a `forwardRef` component with literal-union variants and sizes, spreading `...rest` onto its root and taking `className` for layout only (covers FR-F062-07).
- **SR-S124-02:** Overlay primitives share the `internal/focus.ts` and `internal/layers.ts` modules: focus enters on open, is trapped, returns to the invoker on close, `Escape` closes only the topmost layer, scroll locks without layout shift, and the trigger carries `aria-expanded` and `aria-controls` (FR-F062-08).
- **SR-S124-03:** `apps/web/src/ui/patterns/` exports `PageHeader`, `EmptyState`, `ErrorState`, `DeniedState`, `NotFoundState`, `OfflineBanner`, `StaleBanner`, `LoadingSkeleton`, `ConfirmDialog`, `FormLayout`, `FilterBar`, and `DataTable`, each taking copy as props so no feature wording is hard-coded, and `ErrorState` always renders `correlation_id` with a retry action (FR-F062-09, NFR-F062-04).
- **SR-S124-04:** `AppShell` provides the top bar, resizable and persisted navigation rail, optional inspector, content region, and toast region, and collapses per the five breakpoints; F005 composes it rather than defining its own frame (FR-F062-10).
- **SR-S124-05:** Every interactive primitive is keyboard-operable, shows the focus ring on `:focus-visible` only, and composite widgets implement roving tabindex with arrows, `Home`, `End`, and type-ahead against the WAI-ARIA pattern named in their source doc comment (FR-F062-11, NFR-F062-03).
- **SR-S124-06:** `icons.ts` is the only module importing `lucide-react`, exposes the four sizes aligned to the type scale, marks decorative icons `aria-hidden`, and requires `title` on meaningful ones (FR-F062-13).
- **SR-S124-07:** `FormattedDate`, `FormattedNumber`, and `RelativeTime` read locale and timezone from F049 context with an `en-US`/`UTC` fallback, never call `toLocaleString` without an explicit locale, and no component concatenates translated fragments (FR-F062-14).
- **SR-S124-08:** Every primitive and pattern has stories covering its states in both themes and both densities, and the visual lane pins a deterministic screenshot per story that fails on a pixel diff above 0.1% (FR-F062-15, NFR-F062-04).
- **SR-S124-09:** No primitive renders raw HTML from props, link primitives force `rel="noopener noreferrer"` with `target="_blank"`, the primitive bundle stays under 90 KB gzipped, and a `fetch` spy proves no module under `apps/web/src/ui/**` performs a network call (NFR-F062-01, NFR-F062-02).

## Surfaces

- Infrastructure/container: none; stories build through the existing web pipeline from F001
- Rust service/API: none — F062 owns no Rust path
- Data/migration: none — the harness asserts no migration is added under this feature's owned paths
- React/UI: `apps/web/src/ui/{index.ts, icons.ts, primitives/*.tsx, patterns/*.tsx, shell/{AppShell.tsx, TopBar.tsx, NavRail.tsx, InspectorPanel.tsx, ToastRegion.tsx}}` plus a `*.stories.tsx` beside each component
- Mocks/fixtures: `testing/fixtures/design_system.ts` story matrix and the 10,000-row table dataset; a `fetch` spy; screenshots at device pixel ratio 1 with animations disabled

## TDD harness

- Test path: `testing/features/F062/{frontend,e2e,requirements}/`
- Feature flag: `F062_FEATURE`
- Targeted command: `cargo xtask test-feature F062`
- Full command: `cargo xtask test-all`
- First failing tests: `every_exported_primitive_renders_all_variants`, `nested_menu_escape_leaves_dialog_open`, `error_state_renders_correlation_id_and_retry`, `app_shell_rail_width_persists_across_reload`, `roving_tabindex_moves_with_arrows_and_typeahead`, `icons_import_only_through_registry`, `formatted_date_uses_explicit_locale`, `ui_modules_perform_no_network_call`, `primitive_bundle_under_90kb`

## Exit criteria

- [ ] Requirement tests SR-S124-01 through SR-S124-09 written first and observed failing
- [ ] Tasks T247 and T248 complete
- [ ] Component, E2E, accessibility, visual, and performance lanes pass in both themes and both densities
- [ ] Production call path named: `apps/web/src/ui/index.ts` is the single import surface; `AppShell` mounted by `apps/web/src/main.tsx`; the lint rules from ticket section 4 active in the `web` CI job
- [ ] Handoff evidence recorded in the F062 ticket
