---
id: T155
type: task
status: planned
parent_epic: E008
parent_feature: F039
parent_story: S078
depends_on: [S078]
owned_paths: [apps/web/src/features/ai-assist/**, testing/features/F039/frontend/**, testing/features/F039/e2e/**, testing/features/F039/accessibility/**]
feature_flag: F039_FEATURE
branch: t155-proposal-diff-ui
started_at: null
finished_at: null
---

# T155 — Proposal and diff UI

## Identity

- Parent story: `S078` natural-language reports
- Owner: platform
- Branch: `t155-proposal-diff-ui`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 8; `docs/capability-contracts.md` row F039

## Objective

Build the review surface that makes model output safe to accept: the two prompt panels, the proposal card, the formula and plan diffs, the preview table, the apply confirmation, and the tenant AI settings page, with every state the backend can return and no way to write without an explicit confirmed diff.

## Specification

- Owned files: `apps/web/src/features/ai-assist/{AiFormulaPanel.tsx, AiQueryPanel.tsx, ProposalCard.tsx, FormulaDiff.tsx, PlanDiff.tsx, PreviewTable.tsx, ExcludedSourcesNotice.tsx, ApplyConfirmDialog.tsx, AiSettingsPage.tsx, api.ts, hooks.ts, routes.ts}`.
- Contract/input: generated `AiAssistApi` with `generateFormula`, `compileQuery`, `getQuery`, `executeQuery`, `applyProposal`, `rejectProposal`, `updateAiSettings`; TanStack Query keys `['ai-proposal', proposalId]`, `['ai-query', queryId]`, `['ai-query-rows', queryId, cursor]`, `['ai-settings', tenantId]`; generation is a mutation carrying an `AbortController` bound to the cancel control.
- Output/behavior: `AiFormulaPanel` mounts in the F035 formula editor for `formula` columns; `AiQueryPanel` mounts on `/reports`; `AiSettingsPage` is routed at `/admin/ai-settings`. `ProposalCard` renders the formula or plan, `plan_explanation`, referenced-field chips, a confidence bucket (`low` < 0.5, `medium` < 0.8, `high`), and `limitations`. `FormulaDiff` renders word-level `ins`/`del` marks with the text labels `Added`, `Removed`, `Changed`; `PlanDiff` groups changes under `sources`, `joins`, `filters`, `group_by`, `aggregates`, `calculated_fields`. `ExcludedSourcesNotice` lists each `excluded_sources` entry with its reason in words. `PreviewTable` renders the 5-row formula preview with per-row F035 `error_code` badges, or the executed query rows with `meta.restricted_sources` and `meta.hidden_columns` notices. `ApplyConfirmDialog` names the target column or report, traps focus, and is the only path to `applyProposal`, which sends `Idempotency-Key` and `If-Match`. States rendered: loading skeleton, empty prompt with three examples, generating with cancel, error banner with `correlation_id` and retry, `403 denied` page, `ai_disabled`, `not_entitled`, `rate_limited` with `resets_at`, stale baseline with `Regenerate`, `409 conflict` on apply, and expired proposal. Telemetry events `ai_prompt_submitted`, `ai_proposal_shown`, `ai_proposal_applied`, `ai_proposal_rejected`, `ai_proposal_regenerated`, `ai_query_previewed`, `ai_limit_hit` carry `kind`, `request_id`, and confidence bucket and never carry prompt text. Applying invalidates the F035 column key and the F021 reports list key. Layout is a right-hand drawer above 1024 px, a full-height sheet below, one diff column below 768 px, usable at 320 px; `prefers-reduced-motion` removes the generating shimmer.
- Data access: this task adds no persistence file and touches no database — every surface reads and writes through the generated `AiAssistApi`, and the arrays it renders (`referenced_fields`, `limitations`, `sources`, `excluded_sources`, `allowed_kinds`, `meta.restricted_sources`, `meta.hidden_columns`) keep the same JSON shape now that the API reassembles them from child-table rows, so no component changes; MSW fixtures reproduce that same shape and Playwright seeds go through the `crates/persistence/src/ai-assist/` repositories rather than SQL (decision section 2.1).
- Dependencies: T153 routes for formulas, proposals, and settings; T154 query compile and execute; F035 formula editor mount point; F021 reports list mount point; F048 entitlement state for the not-entitled surface; the shared design tokens and Lucide icon set.
- Feature flag: `F039_FEATURE` evaluated through the F048 flag client hides both entry points when disabled.
- Rollback: disable `F039_FEATURE`; the panels unmount and the F035 and F021 surfaces are unchanged.

## TDD

- Failing test first: `testing/features/F039/frontend/ProposalCard.test.tsx::renders_formula_explanation_fields_and_confidence_bucket`, `::renders_limitations_when_present`; `testing/features/F039/frontend/FormulaDiff.test.tsx::marks_additions_and_removals_with_text_not_color`, `::renders_stale_banner_with_regenerate`; `testing/features/F039/frontend/PlanDiff.test.tsx::plan_diff_groups_changes_by_definition_section`; `testing/features/F039/frontend/PreviewTable.test.tsx::shows_f035_error_code_badge_per_row`, `::shows_restricted_sources_and_hidden_columns_notice`; `testing/features/F039/frontend/ApplyConfirmDialog.test.tsx::apply_is_only_reachable_through_confirmation`, `::conflict_response_shows_current_version_and_keeps_proposal`; `testing/features/F039/frontend/AiPanels.test.tsx::rate_limited_shows_resets_at`, `::ai_disabled_and_not_entitled_render_distinct_states`, `::expired_proposal_shows_regenerate`, `::cancel_aborts_generation_and_restores_focus`; `testing/features/F039/frontend/AiSettingsPage.test.tsx::non_admin_sees_denied_page`; `testing/features/F039/e2e/ai_assist.spec.ts::generate_and_apply_formula`, `::compile_preview_and_save_report`; `testing/features/F039/accessibility/ai_assist.a11y.spec.ts::panels_and_diff_have_no_serious_violations`, `::generation_state_announced_in_live_region`
- Targeted command: `cargo xtask test-feature F039`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: MSW handlers for the seven routes covering success, `denied`, `rate_limited`, `conflict`, and `unavailable`; seeded proposal, plan, and settings payloads from `testing/fixtures/ai_assist.rs`; Playwright runs against the seeded tenant with `AI_PROVIDER=recorded`

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Both panels mounted from the F035 editor and the F021 reports list behind the flag; `/admin/ai-settings` routed
- [ ] axe reports zero serious or critical violations on both panels, the diff view, and the settings page
- [ ] No prompt text appears in telemetry payloads, verified by a test asserting the emitted event shape
- [ ] Owned-path check, file limit, and lint gates pass
- [ ] Handoff evidence recorded in S078
- [ ] `finished_at` recorded
