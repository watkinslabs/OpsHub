# Accessibility conformance

The claim, what backs it, and where we know we fall short. Written to be publishable — an enterprise
buyer's procurement pack asks for exactly this, and a vague answer reads as "we have not looked".

**Target: WCAG 2.2 Level AA.** This document is the engineering statement. A formal VPAT / ACR on the
ITI template is produced from it before the first enterprise deployment; the substance below is what
that document would say, and it is written now so the claim is testable rather than retrofitted.

## What backs the claim

Nothing here rests on inspection. Every conformance statement maps to a test that runs in CI:

| Claim | Test |
|---|---|
| Contrast meets 4.5:1 for body text and 3:1 for large text, icons, meaningful borders and the focus ring | Computed over the token file in both themes for the default brand and every preset (F062 FR-F062-06) |
| A tenant cannot brand itself into an inaccessible product | `validateBrand` refuses a hue that breaks the floor and names the failing pair (FR-F062-04) |
| No serious or critical violations on any surface | axe over every component story in both themes and both densities, plus every feature's accessibility lane |
| Every interactive element is keyboard operable | Keyboard-only walkthrough per feature; composite widgets implement their WAI-ARIA pattern with roving tabindex, arrows, `Home`, `End` and type-ahead |
| Focus is visible and never trapped | Focus ring on `:focus-visible`; overlays return focus to the invoker; `Escape` closes one layer at a time |
| Colour is never the only signal | Status carries text with its icon; chart series carry a legend, direct label or value (FR-F062-13) |
| Motion respects preference | Under `prefers-reduced-motion` no transition exceeds 1 ms and no state relies on movement |
| Virtualized data is announced correctly | `role="grid"` with `aria-rowindex` and `aria-colindex` against full counts, not the rendered window |
| Every surface ships denied, empty, error and loading states | Per-feature frontend lane; `ErrorState` always carries `correlation_id` |

## Where we fall short

Stated plainly, because a conformance claim with no exceptions is not credible.

- **Complex data surfaces are hard to use with a screen reader even when conformant.** A 500-column
  virtualized grid, a Gantt with dependency arrows, and a pivot with nested dimensions all pass their
  automated checks and remain difficult. We treat "passes axe" as the floor, not the goal, and these
  three are the surfaces to test with real assistive-technology users first.
- **Charts convey shape.** Each carries a legend, labels and a text summary, and the underlying rows
  are reachable, but a trend line is not equivalent to reading it.
- **Automated coverage is partial by nature.** axe catches roughly a third of WCAG criteria. Keyboard
  walkthroughs and manual review cover more; neither replaces testing with users who rely on
  assistive technology, which has not yet happened and is scheduled before the first enterprise
  deployment.
- **Third-party surfaces we render** — the identity provider's sign-in page, the payment provider's
  portal — are outside our control. We link to their own conformance statements rather than claiming
  theirs.
- **The design canvas and internal tooling are not in scope.** Only the product is.

## How a regression is caught

A change that breaks contrast, removes a keyboard path, or introduces an axe violation fails CI
before review. That is the point of putting the checks in the pipeline rather than in a checklist: a
conformance claim only survives if breaking it is inconvenient at the moment of writing the code.

Accessibility findings are triaged on the same severity scale as any other defect, and one that makes
a surface unusable with a keyboard or screen reader is a Sev 2 — a customer fully blocked with no
workaround.

## Feedback

Accessibility problems can be reported to **accessibility@[DOMAIN]**, acknowledged within 2 business
days. Reports name the surface, the assistive technology and version, and what could not be done.
