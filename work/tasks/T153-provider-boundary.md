---
id: T153
type: task
status: planned
parent_epic: E008
parent_feature: F039
parent_story: S077
depends_on: [S077]
owned_paths: [crates/domain/src/ai-assist/provider/**, crates/domain/src/ai-assist/formula/**, services/api/src/ai-assist/**, services/worker/src/ai-assist/**, services/api/migrations/*_ai-assist_*.sql, testing/features/F039/api/**, testing/features/F039/database/**]
feature_flag: F039_FEATURE
branch: t153-provider-boundary
started_at: null
finished_at: null
---

# T153 — Provider boundary

## Identity

- Parent story: `S077` formula help
- Owner: platform
- Branch: `t153-provider-boundary`
- Decision references: `docs/architecture-decisions.md` sections 2, 7; `docs/capability-contracts.md` row F039

## Objective

Create the `ai-assist` schema and the single model-egress boundary: the `AiProvider` trait, budgets, JSON-schema validated completions with one repair attempt, the per-tenant circuit breaker, usage metering and limit checks, the formula generation path with F035 preview, and the proposal apply/reject lifecycle. This boundary is the seam F040 consumes; F040 adds no adapter of its own.

## Specification

- Owned files: `services/api/migrations/<ts>_ai-assist_create_tables.sql` and `.down.sql`; `crates/domain/src/ai-assist/{mod.rs, models.rs, errors.rs, service.rs, diff.rs, usage.rs}`; `crates/domain/src/ai-assist/provider/{mod.rs, budget.rs, breaker.rs, schemas.rs, adapters/{bedrock.rs, vertex.rs, azure_foundry.rs, self_hosted.rs, recorded.rs, stub.rs}}`; `crates/domain/src/ai-assist/formula/{prompt.rs, generate.rs, preview.rs}`; `services/api/src/ai-assist/{mod.rs, routes.rs, handlers_formula.rs, handlers_proposal.rs, handlers_settings.rs, dto.rs}`; `services/worker/src/ai-assist/{mod.rs, expire_proposals.rs, roll_usage.rs, purge_request_text.rs}`.
- Contract/input: `trait AiProvider { fn id(&self) -> &'static str; async fn complete(&self, envelope: PromptEnvelope, budget: Budget) -> Result<Completion, ProviderError>; }`; `Budget { max_input_tokens, max_output_tokens, timeout_ms (default 20000), max_cost_micros }`; `Completion { json, tokens_in, tokens_out, cost_micros, latency_ms }`; `ProviderError` variants `Timeout`, `Overloaded`, `TransportFailed`, `RateLimited { retry_after }`, `Refused`, `MalformedOutput { detail }`; adapter selected by deployment config `ai.adapter` with credentials from secret manager keys `ai/<adapter>/endpoint` and `ai/<adapter>/api_key`.
- Output/behavior: routes `POST /api/v1/ai/formulas`, `POST /api/v1/ai/proposals/{id}/apply`, `POST /api/v1/ai/proposals/{id}/reject`, `PATCH /api/v1/tenants/{id}/ai-settings`, plus the router mount consumed by T154 and S078. `complete` output is validated against `provider/schemas/formula.json` or `plan.json`; a schema failure triggers exactly one repair call with the validation error appended, then `AiError::UnusableOutput → 502 unavailable`. Five consecutive failures per `(tenant_id, adapter)` open the breaker for 60 s and every route then returns `503 unavailable` with `retry_after_seconds`. `check_limits` runs before egress and returns `429 rate_limited` with `{ limit, resets_at }` for `per_user_daily` or `tenant_monthly`; the F048 `ai-assist` entitlement and `F039_FEATURE` gate the router with `403 denied` and `reason`. Formula generation writes an `ai_requests` row and a pending `ai_proposals` row, previews 5 readable rows through F035 `POST /api/v1/formulas/evaluate`, regenerates once on an F035 parse failure, and publishes `ai-proposal.created.v1`. Apply requires `Idempotency-Key`, `If-Match`, and apply-time `sheet-editor`, writes through F035 `PUT /api/v1/columns/{id}/formula`, and publishes `ai-proposal.applied.v1`; reject publishes `ai-proposal.rejected.v1`; a non-pending proposal returns `409 conflict` with `current_status`. DDL creates `ai_requests`, `ai_proposals`, `ai_settings`, `ai_usage` with the checks and indexes in F039 section 4. No prompt, envelope, or completion text is logged, audited, or emitted in events.
- Dependencies: F035 parse, evaluate, and `PUT /formula`; F003 authorization and audit writes; F048 entitlement and flag evaluation; F004 secret manager and job transport; T154 supplies the envelope this boundary sends.
- Feature flag: `F039_FEATURE` gates the routes and the three worker jobs; the migration runs regardless.
- Rollback: disable `F039_FEATURE`, set the `ai-assist` entitlement to `none`, and run the down migration dropping the four tables.

## TDD

- Failing test first: `testing/features/F039/api/provider_tests.rs::budget_timeout_maps_to_unavailable`, `::malformed_output_repairs_once_then_unavailable`, `::refusal_maps_to_invalid_with_field_error`, `::rate_limited_sets_retry_after`, `::breaker_opens_after_five_consecutive_failures`, `::breaker_closes_after_sixty_seconds`, `::no_adapter_constructed_outside_provider_module`; `testing/features/F039/api/formula_tests.rs::formula_request_creates_pending_proposal`, `::preview_uses_f035_evaluate_for_five_readable_rows`, `::unparseable_formula_regenerates_once_then_unavailable`, `::preview_error_caps_confidence_at_half`, `::apply_requires_sheet_editor_and_matching_version`, `::apply_stale_version_returns_conflict_with_recomputed_diff`, `::reject_sets_status_and_publishes_rejected`, `::expired_proposal_apply_returns_conflict`, `::daily_limit_blocks_before_provider_call`, `::disabled_settings_denies_every_route`; `testing/features/F039/database/ai_assist_migration_tests.rs::ai_assist_tables_exist_with_constraints`, `::proposal_status_transition_guarded`, `::rollback_drops_ai_assist_tables`
- Targeted command: `cargo xtask test-feature F039`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/ai_assist.rs`; `stub` adapter scripting every `ProviderError` variant; `recorded` adapter replaying `testing/features/F039/evaluation/cassettes/formula/`; fixed clock `2026-09-03T00:00:00Z`; seeded `ai_settings` and F048 entitlement

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; routes and the three jobs registered behind the flag; OpenAPI regenerated without drift
- [ ] A grep gate proves no HTTP client to a model endpoint exists outside `crates/domain/src/ai-assist/provider/adapters/`
- [ ] Owned-path check passes and `crates/domain/src/ai-assist/retrieval/**` is left to T154
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S077
- [ ] `finished_at` recorded
