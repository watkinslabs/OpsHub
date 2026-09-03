# F062 requirements cases

Feature: design system and UI primitives. Flag `F062_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F062-REQ-001` | FR-F062-01 | accessibility | `tokens.css` declares the six scales with the specified values; a spacing step off the 4px base or a component using a raw hex, px, or ms fails lint |
| `F062-REQ-002` | FR-F062-02 | accessibility, frontend | Inter variable loads from the repository with the documented fallback stacks; the seven steps and three weights match; a size outside the scale fails |
| `F062-REQ-003` | FR-F062-03 | accessibility | every color token is semantic; the five intent families each expose `-bg`, `-fg`, `-border`, `-emphasis`; a literal palette reference in a component fails lint |
| `F062-REQ-004` | FR-F062-04 | e2e | light and dark define identical token names; `system` follows `prefers-color-scheme`; the stored choice applies before first paint with no flash on reload |
| `F062-REQ-005` | FR-F062-05 | accessibility | computed contrast over every pair in both themes: body ≥ 4.5:1, large text, icons, meaningful borders and `--focus-ring` ≥ 3:1 against both neighbours |
| `F062-REQ-006` | FR-F062-06 | e2e, frontend | `compact` changes control heights to 24/28/34 and row height to 28; every primitive derives size from the density tokens; the choice persists |
| `F062-REQ-007` | FR-F062-07 | frontend | every primitive on the closed list renders all variants and sizes, forwards its ref, and spreads `...rest`; a feature module redefining one fails lint |
| `F062-REQ-008` | FR-F062-08 | frontend | focus enters on open, is trapped, and returns to the invoker; `Escape` in a menu inside a dialog closes only the menu; scroll locks with no layout shift |
| `F062-REQ-009` | FR-F062-09 | frontend | every pattern takes copy as props; `ErrorState` renders `correlation_id` and retry; the five `LoadingSkeleton` shapes render |
| `F062-REQ-010` | FR-F062-10 | e2e | the shell renders top bar, rail, inspector, content, and toast region; rail width persists; the rail becomes a drawer below `lg` and the inspector a sheet below `sm` |
| `F062-REQ-011` | FR-F062-11 | accessibility, frontend | every interactive primitive is keyboard-operable, rings only on `:focus-visible`, and composite widgets support arrows, `Home`, `End`, and type-ahead |
| `F062-REQ-012` | FR-F062-12 | accessibility | motion tokens carry three durations and three easings; under `prefers-reduced-motion` no transition exceeds 1 ms and no state relies on movement alone |
| `F062-REQ-013` | FR-F062-13 | frontend | `icons.ts` is the only importer of `lucide-react`; decorative icons are `aria-hidden`; meaningful icons require `title`; the four sizes align to the type scale |
| `F062-REQ-014` | FR-F062-14 | frontend | `FormattedDate`, `FormattedNumber`, and `RelativeTime` pass an explicit locale, fall back to `en-US`/`UTC`, and no component concatenates translated fragments |
| `F062-REQ-015` | FR-F062-15 | performance | every primitive and pattern has stories for its states in both themes and both densities; the visual runner captures one deterministic screenshot per story |
| `F062-NFR-001` | NFR-F062-01 | performance | primitive bundle < 90 KB gzipped; `tokens.css` < 12 KB; theme switch repaints a 1,000-row table under 16 ms; 10,000-row scroll holds 60 fps |
| `F062-NFR-002` | NFR-F062-02 | api, frontend | no primitive uses `dangerouslySetInnerHTML`; `target="_blank"` forces `rel="noopener noreferrer"`; the theme bootstrap interpolates no stored value |
| `F062-NFR-003` | NFR-F062-03 | accessibility | axe reports zero serious or critical violations over every story in all four theme-density combinations; the keyboard walkthrough reaches every control |
| `F062-NFR-004` | NFR-F062-04 | api, database, performance | no module under `apps/web/src/ui/**` performs a network call; the feature adds no migration; a story screenshot diff above 0.1% fails the run |

Evidence: command, fixture seed, result, screenshot baseline, and artifact path recorded under `testing/evidence/F062/`.
