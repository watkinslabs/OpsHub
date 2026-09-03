# F060 — Conditional formatting harness

Feature-gated tests for `F060`. Keep test code in this directory.

- Gate: `F060_FEATURE`
- Targeted: `cargo xtask test-feature F060`
- Full: `cargo xtask test-all`
- Fixtures: `testing/fixtures/formatting.rs` (tenant A and B, a sheet-editor, a sheet-viewer, an actor denied the `Budget` column; sheet `Delivery plan` with `Status` select, `Due date` date, `Owner` person, `Budget` currency, and `Variance` formula columns; 50 rows with 6 known exceptions; views `At risk` and `All work`; rule sets `basic_10` and `stress_100`; generators for 5,000 and 100,000 rows; recorded `formula.recalculated.v1` payloads; token-contrast table parsed from `apps/web/src/design/tokens.css`; fixed clock `2026-09-03T00:00:00Z`, UTC, fixed UUIDv7 and fractional-position seeds).
- Lanes: `requirements/` maps every FR-F060 and NFR-F060 id to a named test; `api/` covers rule CRUD, ordering and precedence, scope, evaluate-on-read, materialization, and permission negatives; `database/` covers the two tables, cascades, and index use; `frontend/` covers the panel, editor, legend, and popover; `e2e/` covers authoring, reordering, view scope, and the explanation popover in the browser; `accessibility/` proves colour is never the only signal; `performance/` holds the evaluation, materialization, and paint budgets.
- Positive controls: a colour-only rule, a token pair mutated below contrast, and a rule set inflated past the 150 ms page budget each turn their gate red and are restored to green.
