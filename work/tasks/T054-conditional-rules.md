---
id: T054
type: task
status: planned
parent_epic: E003
parent_feature: F014
parent_story: S027
depends_on: [T053]
owned_paths: [crates/domain/src/forms/**, services/api/src/forms/**, apps/web/src/features/forms/**, testing/features/F014/api/**, testing/features/F014/frontend/**, testing/features/F014/accessibility/**]
feature_flag: F014_FEATURE
branch: t054-conditional-rules
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 3, 4, 6
- Capability contract: `docs/capability-contracts.md` row F014

# T054 — Conditional rules

## Identity

- Parent story: `S027` Form builder
- Owner: platform
- Branch: `t054-conditional-rules`
- Decision references: `docs/architecture-decisions.md` sections 3, 4, 6; `docs/capability-contracts.md` row F014

## Objective

Implement field validation rules and the shared `show_if` condition evaluator on server and browser, and build the form builder page with palette, field editor, condition editor, live preview, publish and share dialogs.

## Specification

- Owned paths: `crates/domain/src/forms/{conditions.rs, validation.rs}`, `services/api/src/forms/handlers_form.rs` (field validation wiring), `apps/web/src/features/forms/{FormBuilderPage.tsx, FieldPalette.tsx, FieldEditor.tsx, ConditionEditor.tsx, FormPreview.tsx, PublishDialog.tsx, ShareDialog.tsx, conditions.ts, api.ts, hooks.ts, routes.ts}`
- Contract/input: `ConditionAst = Cmp { field: key, op: eq|ne|gt|lt|contains|is_empty, value } | And(Vec) | Or(Vec)` with depth ≤ 4 and at most 32 leaves; `FieldValidation { regex?, min?, max?, options_subset? }` checked against the column type from F007 (`regex` only on text, `min`/`max` on number, currency, date, `options_subset` on select); generated `FormsApi` client; route params `workspaceId`, `formId`.
- Output/behavior: `evaluate(ast, values) -> bool` is deterministic and identical in Rust and TypeScript against `testing/fixtures/forms/conditions.json` (64 cases); hidden fields are not required and their values are dropped before validation; the builder renders loading skeleton, empty palette hint, error banner with correlation ID, denied state for submitters, stale banner on `conflict`, and success toasts; `FormPreview` re-evaluates conditions on every keystroke; `PublishDialog` shows the token once and the `ShareDialog` offers internal, link, and embed tabs with the `<iframe>` snippet; telemetry `form_created`, `form_published`, `form_shared`.
- Dependencies: T053 routes and tables; F007 column types and options; F005 workspace shell for the `Forms` tab.
- Feature flag: `F014_FEATURE` read through the flag hook; routes are not registered when off.

## TDD

- Failing test first: `testing/features/F014/api/condition_tests.rs::condition_hidden_field_not_required`, `::condition_depth_over_four_invalid`, `::validation_regex_only_on_text_columns`; `testing/features/F014/frontend/ConditionEditor.test.tsx::evaluator_matches_shared_fixtures`, `::preview_hides_field_when_condition_false`; `testing/features/F014/frontend/FormBuilderPage.test.tsx::shows_denied_state_for_submitter`, `::publish_dialog_shows_token_once`; `testing/features/F014/accessibility/forms.a11y.spec.ts::builder_has_no_serious_axe_violations`
- Targeted command: `cargo xtask test-feature F014`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: shared `conditions.json`; MSW handlers from the 12-column sheet fixture; axe-core via Playwright

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Rust and TypeScript evaluators pass the same fixture set in CI
- [ ] Component and accessibility lanes pass; builder mounted at `/w/:workspaceId/forms/:formId`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S027
- [ ] `finished_at` recorded
