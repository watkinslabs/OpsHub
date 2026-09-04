---
id: S077
type: story
status: planned
parent_epic: E008
parent_feature: F039
depends_on: [F039]
owned_paths: [crates/domain/src/ai-assist/provider/**, crates/domain/src/ai-assist/retrieval/**, crates/domain/src/ai-assist/formula/**, crates/persistence/src/ai-assist/**, services/api/src/ai-assist/**, services/worker/src/ai-assist/**, services/api/migrations/*_ai-assist_*.sql, testing/features/F039/api/**, testing/features/F039/database/**]
feature_flag: F039_FEATURE
branch: s077-formula-help
started_at: null
finished_at: null
---

# S077 — Formula help

## Identity

- Parent feature: `F039` AI formulas/queries
- Owner: platform
- Branch: `s077-formula-help`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 7; `docs/capability-contracts.md` row F039
- Child tasks: `T153` provider boundary, `T154` permission-filtered retrieval

## Vertical slice

As a sheet editor, I want to describe a calculation in plain language and get back a formula with an explanation, the fields it references, and a preview computed from rows I can already read, so that I can review the exact change and apply it to my column myself instead of guessing at `IF`, `DATEDIFF`, and cross-sheet `LOOKUP` syntax.

This slice delivers the whole backend spine that F040 later reuses: the `AiProvider` egress boundary with budgets and a circuit breaker, the permission-filtered retrieval and redaction layer, the normalized `ai_requests`/`ai_proposals`/`ai_settings`/`ai_usage` schema with its child tables and the `crates/persistence/src/ai-assist/` repositories that own them, and the proposal apply/reject lifecycle wired to F035.

## Requirements

- **SR-S077-01:** `POST /api/v1/ai/formulas` accepts `{ sheet_id, column_id?, prompt, result_type? }`, writes one `ai_requests` row and one pending `ai_proposals` row of kind `formula` with its `ai_proposal_referenced_fields` and `ai_proposal_limitations` rows in one `UnitOfWork` through `AiRequestRepository` and `AiProposalRepository`, publishes `ai-proposal.created.v1`, and returns the formula, explanation, `referenced_fields`, `confidence`, `limitations`, `preview`, and `expires_at` with the arrays reassembled from those rows (covers FR-F039-01).
- **SR-S077-02:** The preview calls F035 `POST /api/v1/formulas/evaluate` for the first 5 readable rows and surfaces `status` and `error_code` per row; an unparseable formula is regenerated once with the F035 parser message and a second failure returns `502 unavailable` with `provider_error: unusable_output` (FR-F039-02).
- **SR-S077-03:** Every envelope is built from a `RetrievalScope` resolved by one batched F003 `POST /api/v1/authz/check`, carries schema cards for at most 20 readable sheets with at most 3 sample values per column and 200 values total, and contains no value from a sheet, column, or row the caller cannot read; cards and samples are read through the F005/F007 `SheetRepository`, `ColumnRepository`, and `RowRepository` named queries under the caller's context and never through a generated SQL string (FR-F039-07).
- **SR-S077-04:** The `strict` redaction profile removes email, E.164 phone, and 13–19 digit card values and drops `sensitive` columns before egress, replacing each with `<redacted:kind>`, and stores only `ai_requests.envelope_hash` (FR-F039-08, NFR-F039-02).
- **SR-S077-05:** All model traffic goes through the `AiProvider` trait with `Budget { max_input_tokens, max_output_tokens, timeout_ms, max_cost_micros }`; adapters `bedrock`, `vertex`, `azure-foundry`, `self-hosted`, `recorded`, and `stub` are the only implementations and no handler builds a client directly (FR-F039-09).
- **SR-S077-06:** Provider failures map to `unavailable`, `rate_limited`, `invalid` (refusal), one repair retry on malformed output, and a per-tenant circuit breaker that opens after 5 consecutive failures for 60 s (FR-F039-10, NFR-F039-04).
- **SR-S077-07:** `POST /api/v1/ai/proposals/{id}/apply` requires `Idempotency-Key`, `If-Match`, and `sheet-editor` at apply time, writes through F035 `PUT /api/v1/columns/{id}/formula`, and publishes `ai-proposal.applied.v1`; `POST /api/v1/ai/proposals/{id}/reject` stores the reason and publishes `ai-proposal.rejected.v1`; a non-pending proposal returns `409 conflict` (FR-F039-11, FR-F039-12).
- **SR-S077-08:** Each proposal stores `baseline`, `proposed`, and an ordered `diff` as `jsonb` documents plus its referenced fields and limitations as rows; reading a proposal recomputes the diff against the live baseline and sets `stale: true` when the target version moved (FR-F039-13).
- **SR-S077-09:** `PATCH /api/v1/tenants/{id}/ai-settings` by a `tenant-admin` writes `ai_settings` and replaces its `ai_setting_allowed_kinds` rows in one `UnitOfWork` through `AiSettingsRepository`, rejects a `(provider_id, model_id)` pair absent from `ai_provider_models` with `422 invalid`, keeps `allowed_kinds` as a JSON array on the wire, and `enabled: false` turns every F039 route into `403 denied` with `reason: "ai_disabled"` (FR-F039-14).
- **SR-S077-10:** Usage is metered into `ai_usage` per `(tenant_id, usage_day, actor_id, kind)` by `AiUsageRepository::increment_usage_for_day`, and `ai_setting_allowed_kinds`, `per_user_daily_requests` (`count_requests_for_actor_day`), `monthly_token_budget` (`sum_tokens_for_month`), the F048 `ai-assist` entitlement, and `F039_FEATURE` are all checked before any provider call (FR-F039-15, NFR-F039-01).

## Surfaces

- Infrastructure/container: deployment config `ai.adapter` selecting one of `bedrock`, `vertex`, `azure-foundry`, `self-hosted`; endpoint and credentials via the F004 secret manager keys `ai/<adapter>/endpoint` and `ai/<adapter>/api_key`; `AI_PROVIDER=recorded` in every test profile
- Data access: `crates/persistence/src/ai-assist/{mod.rs, request_repository.rs, proposal_repository.rs, settings_repository.rs, usage_repository.rs, provider_model_repository.rs, query_execution_repository.rs}` hold every SQL statement for this slice — `AiRequestRepository` owns `ai_requests` and `ai_request_sources`, `AiProposalRepository` owns `ai_proposals`, `ai_proposal_referenced_fields`, and `ai_proposal_limitations`, `AiSettingsRepository` owns `ai_settings` and `ai_setting_allowed_kinds`, `AiUsageRepository` owns `ai_usage`, `AiProviderModelRepository` owns `ai_provider_models`, and `AiQueryExecutionRepository` owns `ai_query_executions` and its two child tables; the domain services, the `services/api/src/ai-assist` handlers, and the three worker jobs depend on those traits and contain no `sqlx::query*` call, and multi-table writes run in one `UnitOfWork` (decision section 2.1)
- Rust service/API: `crates/domain/src/ai-assist/{mod.rs, models.rs, errors.rs, service.rs, diff.rs, usage.rs, provider/{mod.rs, budget.rs, breaker.rs, schemas.rs, adapters/*.rs}, retrieval/{scope.rs, schema_card.rs, redaction.rs, envelope.rs}, formula/{prompt.rs, generate.rs, preview.rs}}`; `services/api/src/ai-assist/{routes.rs, handlers_formula.rs, handlers_proposal.rs, handlers_settings.rs, dto.rs}`; `services/worker/src/ai-assist/{mod.rs, expire_proposals.rs, roll_usage.rs, purge_request_text.rs}`
- Data/migration: `services/api/migrations/<ts>_ai-assist_create_tables.sql` and `.down.sql` creating `ai_provider_models`, `ai_requests`, `ai_request_sources`, `ai_proposals`, `ai_proposal_referenced_fields`, `ai_proposal_limitations`, `ai_settings`, `ai_setting_allowed_kinds`, `ai_usage`, `ai_query_executions`, `ai_query_execution_restricted_sources`, and `ai_query_execution_hidden_columns` with the foreign keys, `check` constraints, and indexes in F039 section 4
- React/UI: none in this story; the formula panel and diff view ship in S078 through T155
- Mocks/fixtures: `testing/fixtures/ai_assist.rs`; `recorded` cassettes under `testing/features/F039/evaluation/cassettes/formula/`; `stub` adapter scripting every `ProviderError` variant; socket guard

## TDD harness

- Test path: `testing/features/F039/{api,database}/`
- Feature flag: `F039_FEATURE` with the F048 `ai-assist` entitlement seeded `active`
- Targeted command: `cargo xtask test-feature F039`
- Full command: `cargo xtask test-all`
- First failing tests: `formula_request_creates_pending_proposal`, `preview_uses_f035_evaluate_for_five_readable_rows`, `unparseable_formula_regenerates_once_then_unavailable`, `envelope_excludes_unreadable_sheet_values`, `strict_profile_redacts_email_and_sensitive_columns`, `provider_timeout_maps_to_unavailable`, `breaker_opens_after_five_consecutive_failures`, `apply_requires_sheet_editor_and_matching_version`, `reject_sets_status_and_publishes_rejected`, `daily_limit_blocks_before_provider_call`, `allowed_kind_rows_replace_in_one_transaction`, `referenced_field_row_rejects_duplicate_column`, `settings_reject_unknown_provider_model`

## Exit criteria

- [ ] Requirement tests SR-S077-01 through SR-S077-10 written first and observed failing
- [ ] Tasks T153 and T154 complete and wired through `services/api/src/router.rs` and `services/worker/src/registry.rs`
- [ ] Unit, API, database, and permission-negative tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/ai-assist/routes.rs` mounted at `/api/v1/ai` and `/api/v1/tenants/{id}/ai-settings`; `services/worker/src/ai-assist/expire_proposals.rs`, `roll_usage.rs`, and `purge_request_text.rs` registered in the worker registry
- [ ] No prompt or completion text appears in logs, events, audit rows, or telemetry
- [ ] `cargo xtask check-persistence` passes: all SQL for this slice lives in `crates/persistence/src/ai-assist/`
- [ ] Handoff evidence recorded in the F039 ticket
