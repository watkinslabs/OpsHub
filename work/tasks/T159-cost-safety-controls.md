---
id: T159
type: task
status: planned
parent_epic: E008
parent_feature: F040
parent_story: S080
depends_on: [S080]
owned_paths: [crates/domain/src/ai-insights/**, crates/persistence/src/ai-insights/**, services/api/src/ai-insights/**, services/worker/src/ai-insights/**, apps/web/src/features/ai-insights/**, testing/features/F040/api/**, testing/features/F040/frontend/**, testing/features/F040/performance/**]
feature_flag: F040_FEATURE
branch: t159-cost-safety-controls
started_at: null
finished_at: null
---

# T159 — Cost and safety controls

## Identity

- Parent story: `S080` Assisted actions
- Owner: platform
- Branch: `t159-cost-safety-controls`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 7; `docs/capability-contracts.md` row F040

## Objective

Implement action proposal and execution together with the per-tenant cost, rate, and blast-radius controls: budget reservation before any provider call, scan rate limits and caps, the circuit breaker, and an action runner that re-checks permissions at execution time.

## Specification

- Owned paths: `crates/domain/src/ai-insights/{proposal.rs, executor.rs, budget.rs, safety.rs}`; `crates/persistence/src/ai-insights/action_run_repository.rs`; `services/api/src/ai-insights/handlers_action.rs` propose path; `services/worker/src/ai-insights/action_run.rs`; `apps/web/src/features/ai-insights/{ProposeActionDialog.tsx, ActionPreviewDiff.tsx, ConfirmActionDialog.tsx, ActionRunTimeline.tsx, BudgetBanner.tsx}`
- Contract/input: `ProposeActionRequest { insight_id, action_kind, parameters }`; `ActionResponse { id, status, risk_class, target_count, preview, preview_hash, expires_at, approval_id?, version }`; `ScanGuard { record_cap: 20_000, prompt_token_cap: 150_000, insight_cap: 200, detector_timeout: 60s, scan_timeout: 600s }`; budget reservation through the F039 provider boundary reading the tenant monthly ceiling from `ai_settings`.
- Output/behavior: `POST /api/v1/ai/actions` renders a `before`/`after` diff per target, writes one `ai_action_targets` row per target with the version it was rendered from, stores `preview_hash`, the derived `target_count` (1–25), `risk_class`, and `expires_at = now + 24h`, publishes `ai-action.proposed.v1`, and writes nothing to any target; an unknown `action_kind` returns `400 invalid` `not_allowed`, a target absent from the insight's evidence returns `400 invalid` `target_not_in_evidence`, and more than 25 targets returns `400 invalid`. `safety.rs` enforces 4 on-demand scans per tenant per hour and one per identical scope per 15 minutes (`429 rate_limited` with `retry_after_seconds`), the per-scan caps above, and a circuit breaker that opens for 15 minutes after 5 consecutive provider errors (`503 unavailable`). `budget.rs` reserves the estimated spend before the first provider call and aborts the scan with `429 rate_limited` when the monthly ceiling would be exceeded, discarding partial results; it records `input_tokens`, `output_tokens`, and `cost_micros` per insight. `executor.rs` and `action_run.rs` consume `ai-action.confirmed.v1`, write one `ai_action_runs` row per attempt keyed by `idempotency_key`, re-check the confirming actor's permission on every target at execution time, fail the whole run with `error_class: denied` and no partial writes when a permission was lost, apply through the F008 row-update, F018 draft-create, F020 approval, and F037 notification services, record one `ai_action_run_targets` row per applied target with its resulting version, run at 1 concurrent per tenant with a 30 s timeout, and dead-letter after 2 retries. Metrics `ai_insight_scans_total{detector,result}`, `ai_action_runs_total{action_kind,status}`, and `ai_evidence_rejected_total{reason}` are emitted; the UI renders the diff, confirm dialog, run timeline, and the remaining-budget banner for `tenant-admin`.
- Data access: `proposal.rs`, `executor.rs`, `budget.rs`, `safety.rs`, `handlers_action.rs`, and `action_run.rs` hold no SQL, no `sqlx::query*` call, and no pool — proposals and their targets go through `AiActionRepository::insert_proposal_with_targets`, `list_action_targets`, and `targets_outside_evidence`; attempts and applied targets go through `ActionRunRepository` in `crates/persistence/src/ai-insights/action_run_repository.rs` (`start_attempt`, `record_applied_target`, `finish_attempt`, `find_run_by_idempotency_key`, `count_active_runs_for_tenant`, `list_run_targets`), which owns `ai_action_runs` and `ai_action_run_targets`; scan spacing and hourly counts read `AiScanRepository::find_recent_scan_for_scope` and `count_scans_in_window`; one attempt's run row, applied-target rows, and the target-service writes share a single `UnitOfWork`, so a lost permission rolls the whole attempt back with no partial writes (decision section 2.1).
- Dependencies: T157 scan pipeline and schema; T158 gate transitions and `ai-action.confirmed.v1`; F039 provider boundary budget API; F008, F018, F020, F037 target services; F004 job transport and shared cache for limiter and breaker state.
- Feature flag: `F040_FEATURE` gates the propose route, the runner, and the UI surfaces.

## TDD

- Failing test first: `testing/features/F040/api/proposal_tests.rs::propose_action_writes_nothing_to_targets`, `::unknown_action_kind_rejected`, `::target_outside_evidence_rejected`, `::more_than_twenty_five_targets_rejected`, `::preview_hash_is_stable_for_same_preview`; `testing/features/F040/api/safety_tests.rs::fifth_scan_in_an_hour_is_rate_limited`, `::same_scope_within_fifteen_minutes_is_rate_limited`, `::scan_aborts_at_twenty_thousand_records`, `::detector_timeout_at_sixty_seconds_marks_partial`, `::five_provider_errors_open_circuit_for_fifteen_minutes`; `testing/features/F040/api/budget_tests.rs::budget_exhausted_blocks_scan_before_provider_call`, `::partial_scan_results_discarded_on_budget_abort`, `::insight_records_token_usage_and_cost_micros`; `testing/features/F040/api/executor_tests.rs::run_denied_when_permission_lost_after_confirm`, `::run_is_idempotent_for_repeated_idempotency_key`, `::run_dead_letters_after_two_retries`, `::run_target_rows_record_resulting_versions`, `::run_target_outside_proposal_violates_foreign_key`; `testing/features/F040/frontend/ActionPreviewDiff.test.tsx::renders_before_and_after_for_each_target`; `testing/features/F040/performance/scan_bench.rs::scan_twenty_thousand_rows_under_ten_minutes`
- Targeted command: `cargo xtask test-feature F040`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/ai_insights.rs` with a tenant whose monthly ceiling has 100 micros remaining, a 20,000-row generator, F008/F018/F020/F037 recorders, a provider stub that can force consecutive errors and report token usage, and per-worker limiter and breaker state

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Propose route, runner, approval-driven execution, and UI wired behind the flag; OpenAPI regenerated without drift
- [ ] Metrics and spans present with `scan_id`, `insight_id`, `action_id`, and `correlation_id`
- [ ] Owned-path check, file limit, lint, and performance gates pass
- [ ] Handoff evidence recorded in S080
- [ ] `finished_at` recorded
