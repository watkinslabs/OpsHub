---
id: S078
type: story
status: planned
parent_epic: E008
parent_feature: F039
depends_on: [F039]
owned_paths: [crates/domain/src/ai-assist/query/**, services/api/src/ai-assist/**, apps/web/src/features/ai-assist/**, testing/features/F039/frontend/**, testing/features/F039/e2e/**, testing/features/F039/accessibility/**, testing/features/F039/performance/**, testing/features/F039/evaluation/**]
feature_flag: F039_FEATURE
branch: s078-natural-language-reports
started_at: null
finished_at: null
---

# S078 — Natural-language reports

## Identity

- Parent feature: `F039` AI formulas/queries
- Owner: platform
- Branch: `s078-natural-language-reports`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 7; `docs/capability-contracts.md` row F039
- Child tasks: `T155` proposal/diff UI, `T156` evaluation harness

## Vertical slice

As a report viewer, I want to ask "open risks per owner across the launch sheets" and see the compiled report plan — sources, joins, filters, grouping, aggregates — with the sheets I cannot read listed as excluded, preview the rows under my own permissions, and then save it as a report only if the diff looks right, so that I get a cross-source report without learning the report builder and without ever seeing data I am not entitled to.

This slice adds query compilation and execution on top of the S077 spine, the review surfaces that make a proposal reviewable, and the offline evaluation harness that proves the whole capability is permission-safe and deterministic without a live model call.

## Requirements

- **SR-S078-01:** `POST /api/v1/ai/queries` compiles `{ question, workspace_id?, sheet_ids? }` into an F021 `ReportDefinition` and returns `plan`, `plan_explanation`, `sources`, `excluded_sources` with reason `denied`, `not_found`, or `over_limit`, `estimated_rows`, `plan_hash`, and `requires_preview`; the route compiles only and reads no row data (covers FR-F039-03).
- **SR-S078-02:** The compiled plan is run through the F021 definition validator before it is returned; a failure regenerates once with the `field_errors` map appended and a second failure returns `502 unavailable` with `provider_error: uncompilable_plan` while storing the rejected plan on the request row (FR-F039-04).
- **SR-S078-03:** `GET /api/v1/ai/queries/{id}` returns the stored question, plan, `plan_hash`, status, sources, `excluded_sources`, and `last_execution`; another actor in the tenant receives `403 denied` and a foreign tenant receives `404 not_found` (FR-F039-05).
- **SR-S078-04:** `POST /api/v1/ai/queries/{id}/execute` executes the stored plan through the F021 read path under the caller's permissions, returns F021 rows plus `meta { computed_at, duration_ms, restricted_sources, hidden_columns, truncated }`, publishes `ai-query.executed.v1`, and returns `409 conflict` with `current_plan_hash` on a `plan_hash` mismatch (FR-F039-06).
- **SR-S078-05:** Applying a `report_definition` proposal creates the report through F021 `POST /api/v1/reports` with `report-editor` checked at apply time; the proposal diff groups changes by `sources`, `joins`, `filters`, `group_by`, `aggregates`, and `calculated_fields` and is marked `stale` when the baseline moved (FR-F039-11, FR-F039-13).
- **SR-S078-06:** The web app ships `AiFormulaPanel`, `AiQueryPanel`, `ProposalCard`, `FormulaDiff`, `PlanDiff`, `PreviewTable`, `ApplyConfirmDialog`, and `AiSettingsPage` with loading, empty, error, denied, disabled, not-entitled, rate-limited, stale-baseline, and expired states, cancellable generation, and no prompt text in telemetry (FR-F039-16).
- **SR-S078-07:** Both panels, the diff view, and the settings page pass axe with zero serious or critical violations; diff additions and removals carry text labels and `ins`/`del` semantics rather than color alone; generation start, completion, and failure are announced through a polite live region; `Apply` opens a focus-trapped confirmation naming the target (NFR-F039-03).
- **SR-S078-08:** The evaluation harness under `testing/features/F039/evaluation/` runs with `AI_PROVIDER=recorded` and a socket guard, and enforces zero permission-leakage failures, zero grounding failures, refusal ≥ 0.98 of 40 cases, formula exact-match ≥ 0.85 of 120 cases, and plan compilability ≥ 0.95 of 80 cases, failing on a missing cassette rather than calling a live model (NFR-F039-05).
- **SR-S078-09:** Performance gates hold: retrieval scope for 20 sheets and 400 columns under 300 ms p95, compile and generate under 6 s p95 excluding provider latency, apply under 800 ms p95, and `GET /api/v1/ai/queries/{id}` under 300 ms p95 (NFR-F039-01).

## Surfaces

- Infrastructure/container: no new services; the evaluation lane runs in CI with `AI_PROVIDER=recorded` and network egress denied for the test process
- Rust service/API: `crates/domain/src/ai-assist/query/{prompt.rs, compile.rs, validate.rs, execute.rs}`; `services/api/src/ai-assist/{handlers_query.rs, dto_query.rs}` mounted by the S077 router
- Data/migration: none; queries and plans reuse the `ai_requests` and `ai_proposals` tables created in S077
- React/UI: `apps/web/src/features/ai-assist/{AiFormulaPanel.tsx, AiQueryPanel.tsx, ProposalCard.tsx, FormulaDiff.tsx, PlanDiff.tsx, PreviewTable.tsx, ApplyConfirmDialog.tsx, AiSettingsPage.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: MSW handlers for the seven routes; `testing/fixtures/ai_assist.rs` tenants and sheets including `Finance FY26` readable only by the admin; cassette sets `formula/`, `plan/`, `refusal/`, `leakage/`, `grounding/`

## TDD harness

- Test path: `testing/features/F039/{frontend,e2e,accessibility,performance,evaluation}/`
- Feature flag: `F039_FEATURE` with the F048 `ai-assist` entitlement seeded `active`
- Targeted command: `cargo xtask test-feature F039`
- Full command: `cargo xtask test-all`
- First failing tests: `question_compiles_to_valid_report_definition`, `uncompilable_plan_regenerates_once_then_unavailable`, `execute_rejects_mismatched_plan_hash`, `execute_drops_restricted_sources_for_viewer`, `plan_diff_groups_changes_by_definition_section`, `expired_proposal_shows_regenerate`, `leakage_suite_reports_zero_failures`, `recorded_provider_fails_on_missing_cassette`

## Exit criteria

- [ ] Requirement tests SR-S078-01 through SR-S078-09 written first and observed failing
- [ ] Tasks T155 and T156 complete and wired
- [ ] Frontend, E2E, accessibility, performance, and evaluation lanes pass in targeted and full modes
- [ ] Production call path named: `services/api/src/ai-assist/handlers_query.rs` mounted by `services/api/src/ai-assist/routes.rs`; `apps/web/src/features/ai-assist/routes.ts` registered in the app router and the panels mounted by the F035 formula editor and the F021 reports list
- [ ] Positive control recorded: an injected leak makes the leakage suite fail, and restoring the filter makes it pass
- [ ] Handoff evidence recorded in the F039 ticket
