# Engineering standards

How code is written here. The rules are deliberately narrow: uniformity across every object beats
local cleverness, because fifty-nine features built by different hands have to read as one product.

Every rule names how it is enforced. A rule enforced only by review is a rule that will be broken, so
most are lint or gate rules and the few that cannot be are called out as such.

## 1. Styling and theming

**Tokens are the only source of visual values.** Colour, spacing, radius, type size, line height,
font weight, elevation, duration, easing and z-index come from the CSS custom properties defined in
`apps/web/src/design/tokens.css` and mapped onto the MUI theme in `apps/web/src/design/theme.ts`.

- **No literal where a token exists.** No hex, `rgb()`, `hsl()`, raw `px` for spacing or type, or raw
  `ms` for motion anywhere under `apps/web/src/**`. *Enforced by lint (F062 FR-F062-01).*
- **No component-scoped stylesheets.** No `.css`, `.scss` or CSS-module file outside
  `apps/web/src/design/`. Styling is the theme, `sx` with token references, or a `styled()` wrapper
  in `apps/web/src/ui/`. A feature that needs a new visual treatment extends the theme, not its own
  file. *Enforced by lint.*
- **`className` is for layout only** — grid placement, flex growth, width. Never colour, typography,
  border or shadow. Those are the component's variant. *Review.*
- **Adding a token is a deliberate change**: add it to `tokens.css`, define it in *both* themes, map
  it in `theme.ts`, and it is covered by the parity and contrast tests automatically. A token added
  to one theme fails `token parity`. *Enforced by test (F062 FR-F062-05, FR-F062-06).*
- **Theme, density and brand are CSS-variable swaps**, never React state that re-renders the tree.
  A switch must not re-render `DataGridPanel`. *Enforced by test (FR-F062-08).*
- **The brand hue is one variable.** Accent, selection and focus derive from `--brand` through
  `color-mix`; never author an accent value directly. *Enforced by lint and the contrast gate.*

**Variants are enumerated, not composed ad hoc.** This is the Bootstrap discipline: a button is
`variant="primary|secondary|ghost|danger"` and `size="sm|md|lg"`, a literal union in TypeScript, and
those are all the buttons that exist. A feature that wants a fifth kind of button opens a ticket
against F062; it does not pass `sx` to make one. *Enforced by lint (no `sx` colour/typography keys in
`apps/web/src/features/**`) and by review.*

## 2. Components

- **One import surface.** Features import from `apps/web/src/ui`, never from `@mui/material`,
  `@mui/x-*`, `@tanstack/*` or an icon package directly. The wrapper is the seam that lets the vendor
  change without touching features. *Enforced by lint (FR-F062-09).*
- **No feature-local reimplementation** of anything the shared library exports. A duplicate component
  name under `apps/web/src/features/**` fails lint. *Enforced by lint.*
- **Features compose, they do not restyle.** If a screen needs a variation, the variation belongs to
  the component as a named prop.
- **Every surface ships its states**: loading, empty, error (with `correlation_id`), permission
  denied, stale or conflicted, offline, success. Use the F062 pattern components; do not hand-roll an
  empty state. *Enforced by the per-feature frontend harness lane.*
- **Data surfaces go through the three wrappers** — `DataGridPanel`, `ChartPanel`, `DateField` — so
  theme, density, locale and pagination behave identically everywhere.

## 3. Icons

- **One registry, one library.** Every icon comes from `apps/web/src/ui/icons.ts`, which is the only
  module permitted to import the icon package. *Enforced by lint (FR-F062-14).*
- Four sizes only — 14, 16, 20, 24 — aligned to the type scale. A different size means the wrong
  size is being used somewhere.
- A decorative icon is `aria-hidden`; a meaningful one takes a required `title`. *Enforced by lint
  and axe.*
- **Never emoji as functional UI.** Not in components, not in empty states, not in status.

## 4. TypeScript

- No `any`, no non-null `!` assertion, no `as` cast to silence the compiler in application code.
  Where a boundary genuinely needs it, parse and narrow instead. *Enforced by lint.*
- Variants and states are literal unions or discriminated unions, never bare `string`.
- Every exported component has an exported props interface; components are named exports, so a
  rename is a compile error rather than a silent divergence.
- API types come from the generated client; hand-written duplicates of a server type are forbidden.
  *Enforced by the F044 client-drift check.*

## 5. Rust

- **Data access only through repositories.** No SQL string, `sqlx::query*` call, pool or connection
  outside `crates/persistence`. The domain depends on repository traits. *Enforced by
  `check-persistence` and, once code exists, the F068 source-level gate.*
- **The base contract owns the invariants** — tenant predicate, soft-delete filter, version check,
  audit row, outbox enqueue. A repository never re-implements them, and a `RepositorySpec` cannot
  express a predicate, so forgetting is a compile error. *Enforced by type design plus the runtime
  conformance suite.*
- **Typed domain errors.** Each module defines its error enum and exactly one mapping to the shared
  vocabulary — `invalid`, `denied`, `not_found`, `conflict`, `rate_limited`, `unavailable`. No handler
  invents a status code. *Review, plus the API contract tests.*
- **No `unwrap`, `expect` or `panic!` on a request or job path.** They are permitted in tests and in
  start-up code where a failure must stop the process. *Enforced by lint.*
- **Every mutation carries** an idempotency key and an expected version, and writes its audit row and
  outbox event in the same transaction. *Enforced by the base contract and per-feature tests.*
- **Every request and job runs in a tracing span** carrying `tenant_id`, `actor_id`, `correlation_id`
  and the entity id. A log line without a correlation id is not diagnosable. *Review.*
- Modules mirror the module slug from the contract catalog, so a feature's code location is
  predictable from its row.

## 6. API

The conventions in `docs/capability-contracts.md` are binding, not advisory: cursor pagination,
`Idempotency-Key` and `If-Match` on mutations, the six-code error vocabulary, and
`<aggregate>.<verb>.v1` events through the outbox. A route that departs from them needs a decision
record, not a comment. *Enforced by `check-contracts` and the OpenAPI drift check.*

## 7. Tests

- **The failing test comes first**, in the feature's harness under `testing/features/F###/`, and is
  observed failing before the implementation exists.
- **No test reaches the network.** Providers are mocked in `testing/harness/`; a test that opens a
  socket to a third party is a broken test. *Enforced by the api-lane negative controls.*
- Fixtures are deterministic: fixed clock, fixed seeds, UTC, one tenant per test, one schema per
  worker. A flaky test is reverted, not retried.
- Permission-negative and cross-tenant cases are part of the definition of done, not a later pass.

## 8. Accessibility and performance

- WCAG 2.2 AA is a gate, not an aspiration: axe reports zero serious or critical violations on every
  story in both themes and both densities.
- Every interactive element is keyboard reachable and operable, focus is visible on `:focus-visible`,
  and colour is never the only signal.
- Performance budgets live in each ticket's NFRs and are asserted in its performance lane. A budget
  without a test is not a budget.

## 9. What is enforced where

| Rule | Enforced by |
|---|---|
| No literal colour, spacing, radius or duration | ESLint rule set, `web` CI job |
| No stylesheet outside `design/` | ESLint |
| No direct vendor import; no duplicate component name | ESLint |
| Icons only through the registry | ESLint |
| No `any`, `!`, silencing `as`; no `unwrap` on request paths | ESLint and clippy |
| Token parity and contrast in both themes | F062 accessibility lane |
| No SQL outside `crates/persistence`; no array column; justified `jsonb` | `check-persistence` |
| Catalog and tickets agree in both directions | `check-contracts` |
| Roles defined before use | `check-roles` |
| Every ticket names an existing artboard | `check-design` |
| 500-line file limit | `validate-work`, `line-limit` CI job |
| Accessibility | axe in every feature's accessibility lane |

Rules resting on review alone — `className` for layout only, error mapping, span fields — are the
ones to watch in code review, because nothing else will catch them.
