---
id: F039
type: feature
status: planned
priority: P1
owner: platform
estimate: 3
target_milestone: M7
parent_epic: E008
depends_on: [F035, F021, F048]
blocks: []
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/ai-assist/**, services/api/src/ai-assist/**, services/worker/src/ai-assist/**, apps/web/src/features/ai-assist/**, services/api/migrations/*_ai-assist_*.sql, testing/features/F039/**]
feature_flag: F039_FEATURE
flag_default: off
branch: f039-ai-formulas-queries
started_at: null
finished_at: null
---

# F039 — AI formulas/queries

## 1. Identity and dates

- Branch: `f039-ai-formulas-queries`
- Capability area: AI capabilities (spec 5.10 AI-01, AI-03; section 10 provider-neutral adapter decision)
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 7; `docs/capability-contracts.md` row F039
- Aggregate: `ai-query`
- Module slug: `ai-assist`

## 2. Requirement specification

### Problem and user outcome

People who can describe what they want in a sentence still cannot write `SUMIF` over a linked sheet or assemble a five-source report with joins and filters. They abandon the formula editor and the report builder and ask an analyst instead. The blocking risk is not the writing — it is trust: an assistant that can read work data must never read a row the asking user cannot read, and must never write a formula, column, or report without the user seeing exactly what changes.

As a sheet or report user, I want to describe a formula or a question in plain language, see the generated formula or query plan with the fields it touches and a preview computed from rows I can already read, and then apply or reject it as a reviewable diff, so that I get analyst-grade output without granting the assistant access I do not have and without silent edits to my sheets.

F039 owns the model provider boundary, the permission-filtered retrieval layer, the proposal/diff lifecycle, and the offline evaluation harness. F040 consumes those four seams for insights and assisted actions and adds nothing to them.

### Functional requirements

- **FR-F039-01:** `POST /api/v1/ai/formulas` with `{ sheet_id, column_id?, prompt (1–2000 chars), result_type? }` from an actor holding `resource-viewer` on `sheet_id` creates one `ai_requests` row (`kind: formula`) and one `ai_proposals` row (`kind: formula`) and returns `201` with `{ request_id, proposal_id, formula, explanation, referenced_fields: [{ sheet_id, column_id, label }], confidence: 0.0–1.0, limitations: [string], preview, expires_at }`; the response never contains provider identifiers, prompt text, or values outside the caller's read scope.
- **FR-F039-02:** `preview` in FR-F039-01 is computed by calling F035 `POST /api/v1/formulas/evaluate` once per preview row for the first 5 rows of `sheet_id` the caller can read, returning `[{ row_id, value, display, status, error_code? }]`; a preview row whose evaluation returns `status: error` is kept with its F035 `error_code` and the proposal `confidence` is capped at `0.5`; a formula that fails F035 `POST /api/v1/formulas/parse` is regenerated once with the parser message appended to the envelope, and a second parse failure returns `502 unavailable` with `provider_error: unusable_output`.
- **FR-F039-03:** `POST /api/v1/ai/queries` with `{ question (1–2000 chars), workspace_id?, sheet_ids?: [uuid] (0–20) }` compiles the question into an F021 `ReportDefinition` and returns `201` with `{ request_id, query_id, plan, plan_explanation, sources: [{ alias, sheet_id, name }], excluded_sources: [{ sheet_id, reason: "denied"|"not_found"|"over_limit" }], estimated_rows, plan_hash, requires_preview }`; the route compiles only and never reads row data, and `requires_preview` is `true` whenever any source sheet carries a column marked `sensitive` in F007 metadata.
- **FR-F039-04:** The compiled plan is validated before it is returned by running it through the F021 definition validator (sources 1–20, joins forming a tree rooted at `sources[0]`, filter tree depth ≤ 4 and ≤ 50 predicates, `group_by` ≤ 3, `aggregates` ≤ 20, `calculated_fields` ≤ 25 parsed with F035); a plan that fails validation is regenerated once with the `field_errors` map appended to the envelope, and a second failure returns `502 unavailable` with `provider_error: uncompilable_plan` and stores the rejected plan on the `ai_requests` row for support.
- **FR-F039-05:** `GET /api/v1/ai/queries/{id}` returns `{ request_id, question, plan, plan_explanation, plan_hash, status: compiled|executed|expired, sources, excluded_sources, last_execution: { executed_at, row_count, duration_ms, restricted_sources, hidden_columns } | null, version }` to the requesting actor only; another actor in the same tenant receives `403 denied` and a foreign tenant receives `404 not_found`.
- **FR-F039-06:** `POST /api/v1/ai/queries/{id}/execute` with `{ plan_hash, cursor?, limit? (1–500, default 100) }` executes the stored plan through the F021 ad-hoc read path under the caller's own permissions and returns rows in the F021 row shape plus `meta { computed_at, duration_ms, restricted_sources, hidden_columns, truncated }`; a `plan_hash` that does not match the stored plan returns `409 conflict` with `current_plan_hash`, and execution publishes `ai-query.executed.v1` with `{ query_id, row_count, duration_ms, source_count }`.
- **FR-F039-07:** Every retrieval that feeds the provider is built by the retrieval layer as a `RetrievalScope` resolved from one batched F003 `POST /api/v1/authz/check` for the candidate sheets, columns, and rows; the resulting prompt envelope contains only schema cards (`sheet_id`, name, and for each readable column `column_id`, label, type, and up to 3 sample values drawn from rows the caller can read) and never contains a value from a sheet, column, or row the caller cannot read; the number of sheets in one envelope is capped at 20 and the sample budget at 200 values.
- **FR-F039-08:** Before an envelope leaves the process, the redaction profile from `ai_settings.redaction_profile` (`strict` default, or `standard`) removes values matching email, E.164 phone, and 13–19 digit card patterns, drops every column whose F007 metadata sets `sensitive: true` under `strict`, and replaces each removed value with the token `<redacted:kind>`; the redaction pass runs on the serialized envelope, and its output hash is stored as `ai_requests.envelope_hash` so a leak is traceable without storing the envelope.
- **FR-F039-09:** All provider traffic passes through the `AiProvider` trait (`complete(envelope, budget) -> Completion`) implemented by the deployment-selected adapters `bedrock`, `vertex`, `azure-foundry`, `self-hosted`, plus the test-only `recorded` and `stub` adapters; `budget` carries `max_input_tokens`, `max_output_tokens`, `timeout_ms` (default 20000), and `max_cost_micros`; the trait is the only egress point and no handler, worker, or React surface constructs a provider client directly.
- **FR-F039-10:** Provider failures map to stable errors: `ProviderError::Timeout`, `::Overloaded`, `::TransportFailed` → `502 unavailable`; `::RateLimited` → `429 rate_limited` with `Retry-After`; `::Refused` (safety filter) → `422 invalid` with `field_errors.prompt = "refused"`; `::MalformedOutput` → one repair attempt with the JSON schema error appended, then `502 unavailable`; five consecutive provider failures for a tenant open a circuit breaker for 60 s during which every AI route returns `503 unavailable` with `retry_after_seconds`.
- **FR-F039-11:** `POST /api/v1/ai/proposals/{id}/apply` with `Idempotency-Key` and `If-Match: <target_version>` applies a `formula` proposal through F035 `PUT /api/v1/columns/{id}/formula` and a `report_definition` proposal through F021 `POST /api/v1/reports`, requires the caller to hold the downstream write role (`sheet-editor` or `report-editor`) checked at apply time rather than at generation time, records `applied_at`, `applied_by`, `applied_target_version`, sets `status: applied`, and publishes `ai-proposal.applied.v1`; a stale `If-Match` returns `409 conflict` with `current_version` and the diff is recomputed against the new baseline.
- **FR-F039-12:** `POST /api/v1/ai/proposals/{id}/reject` with `{ reason: string(0–500) }` sets `status: rejected`, stores the reason, and publishes `ai-proposal.rejected.v1`; a proposal is `expired` 24 hours after creation and both `apply` and `reject` on an `expired`, `applied`, or `rejected` proposal return `409 conflict` with `current_status`; expiry is enforced by the `ai-assist.expire_proposals` worker job running every 15 minutes.
- **FR-F039-13:** Every proposal stores `baseline` (the current formula expression or report definition, `null` when creating), `proposed`, and a computed `diff` as an ordered list of `{ path, op: add|remove|replace, before, after }`; `GET` on a proposal recomputes the diff against the live baseline and marks it `stale: true` when the baseline version changed since generation, so the review UI never shows a diff against a version that no longer exists.
- **FR-F039-14:** `PATCH /api/v1/tenants/{id}/ai-settings` by a `tenant-admin` with `If-Match` writes `ai_settings` `{ enabled, provider_id, model_id, monthly_token_budget (0–100000000), per_user_daily_requests (0–1000, default 50), timeout_ms (1000–60000), redaction_profile, retention_days (1–365, default 30), allowed_kinds: subset of ["formula","query"], sensitive_preview_required }` and publishes an audit event; `enabled: false` makes every other F039 route return `403 denied` with `reason: "ai_disabled"`; a non-admin receives `403 denied`.
- **FR-F039-15:** Usage is metered per request into `ai_usage` keyed by `(tenant_id, usage_day, actor_id, kind)` with `request_count`, `tokens_in`, `tokens_out`, `cost_micros`; a request that would exceed `per_user_daily_requests` or the remaining `monthly_token_budget` returns `429 rate_limited` with `{ limit: "per_user_daily"|"tenant_monthly", resets_at }` before any provider call is made; the module is additionally gated by the F048 `ai-assist` entitlement and the `F039_FEATURE` flag, and a tenant without entitlement receives `403 denied` with `reason: "not_entitled"`.
- **FR-F039-16:** The web app renders an `Ask for a formula` panel in the F035 formula editor and an `Ask a question` panel on the reports list; both show the prompt box, a generating state with a cancel control, the proposal card (formula or plan, explanation, referenced fields, confidence, limitations), the diff view, the preview table, and `Apply`, `Reject`, and `Regenerate` actions, plus loading, empty, error, denied, disabled, not-entitled, rate-limited, stale-baseline, and expired states.

### Non-functional requirements

- **NFR-F039-01 Performance:** `RetrievalScope` construction for 20 sheets and 400 columns completes in under 300 ms p95; `POST /api/v1/ai/formulas` and `POST /api/v1/ai/queries` respond in under 6 s p95 measured excluding provider latency and under 25 s p99 including it; `POST /api/v1/ai/proposals/{id}/apply` p95 under 800 ms excluding the downstream F035 recalculation job; `GET /api/v1/ai/queries/{id}` p95 under 300 ms.
- **NFR-F039-02 Security/privacy:** retrieval is permission-filtered per FR-F039-07 and redacted per FR-F039-08; no prompt, envelope, or completion text is written to application logs; `ai_requests` retains `input_text` and `output_text` only for `ai_settings.retention_days` and the F027 sweep deletes them afterwards; provider envelopes carry an opaque `tenant_hash` rather than tenant, user, sheet, or workspace names; adapters are configured to disable provider-side training and prompt retention; cross-tenant proposal and query IDs return `not_found`.
- **NFR-F039-03 Accessibility:** the prompt panel, proposal card, and diff view pass axe with zero serious or critical violations; diff additions and removals carry text markers and `ins`/`del` semantics rather than color alone; the generating state announces start, completion, and failure through a polite live region; `Apply` and `Reject` are reachable and operable by keyboard with visible focus and the confirmation dialog traps focus.
- **NFR-F039-04 Reliability/observability:** provider calls are bounded by `timeout_ms`, retried at most once for `MalformedOutput` and never for `Refused`, and protected by the per-tenant circuit breaker of FR-F039-10; the expiry job is idempotent; metrics `ai_requests_total{kind,status}`, `ai_provider_latency_ms{adapter}`, `ai_provider_failures_total{adapter,class}`, `ai_proposal_outcomes_total{kind,outcome}`, `ai_tokens_total{tenant,direction}`; every request carries a tracing span with `request_id`, `correlation_id`, and `envelope_hash` and no prompt content.
- **NFR-F039-05 Evaluation and determinism:** the harness under `testing/features/F039/evaluation/` runs with `AI_PROVIDER=recorded` and a socket guard that fails any outbound connection, so no test ever reaches a live model; suites are permission leakage (0 failures required), grounding/citation (every referenced field present in the envelope, 0 failures), refusal on prompts asking for data outside scope (≥ 0.98 of 40 cases), formula exact-match after normalization (≥ 0.85 of 120 cases), and plan compilability (≥ 0.95 of 80 cases); a missing cassette fails the test rather than falling back to a live call.

### Scope

Included: the `AiProvider` trait and adapters, budgets and circuit breaker, permission-filtered retrieval and redaction, formula generation with F035 parse and preview, natural-language compilation to an F021 `ReportDefinition`, plan execution under caller permissions, the proposal/diff lifecycle with apply and reject, tenant AI settings, usage metering and limits, the two web panels with the diff review surface, and the offline evaluation harness.

Excluded: insight generation, scheduled scans, evidence records, and assisted write actions (F040); the formula parser, evaluator, and dependency graph (F035); report storage, snapshots, and the report editor (F021); entitlement records and flag administration (F048); permission model and audit storage (F003); data enrichment columns and AI-authored dashboards (F040 and later phases); model hosting, fine-tuning, or embedding stores of any kind.

## 3. UX specification

- Entry points: `Ask for a formula` button in the F035 formula editor on a `formula` column; `Ask a question` button on `/reports`; review route `/ai/proposals/:proposalId`; admin route `/admin/ai-settings`.
- Primary flow (formula): user opens the formula editor on column `Days late`, types "days between the due date and today, blank when done", sees a generating state, then a card with `IF([Status]@row = "Done", "", DATEDIFF([Due date]@row, TODAY()))`, an explanation, chips for `Status` and `Due date`, confidence `0.82`, and a 5-row preview; user clicks `Apply`, confirms, and the column recalculates.
- Primary flow (query): user types "open risks per owner across the launch sheets", sees the compiled plan rendered as sources, joins, filters, grouping, and aggregates with an `Excluded: Finance FY26 (no access)` notice, clicks `Preview rows` to execute under their own permissions, then `Save as report` which applies the proposal.
- Diff view: two-column formula diff with word-level `ins`/`del` marks, or a plan diff grouped by `sources`, `joins`, `filters`, `group_by`, `aggregates`, `calculated_fields`; each changed line is labelled `Added`, `Removed`, or `Changed` in text; a stale baseline shows a banner `The column changed since this was generated` with `Regenerate`.
- States: loading skeleton for the panel; empty prompt box with three example prompts per surface; error banner with `correlation_id` and `Retry`; denied page for actors without `resource-viewer`; `AI is turned off for this tenant` when `ai_settings.enabled` is false; `Your plan does not include AI assist` when the F048 entitlement is missing; `You have used 50 of 50 requests today, resets 00:00 UTC` on `rate_limited`; `This suggestion expired` with `Regenerate` on an expired proposal.
- Responsive: the panel is a right-hand drawer above 1024 px and a full-height sheet below; the diff stacks to one column below 768 px and fits 320 px.
- Keyboard: the prompt box submits on `Ctrl+Enter`; the proposal card is a labelled region; `Apply` opens a focus-trapped confirmation naming the target column or report; cancelling generation returns focus to the prompt box; `prefers-reduced-motion` removes the generating shimmer.
- Font/icon/design tokens: Inter variable; Lucide icons `Sparkles`, `FunctionSquare`, `Search`, `GitCompare`, `Check`, `X`, `RotateCcw`; tokens from `apps/web/src/design/tokens.css`.

## 4. Technical specification

### Rust backend

- Domain entities in `crates/domain/src/ai-assist/`: `AiRequest { id, tenant_id, actor_id, kind: Formula|Query, input_text, envelope_hash, output_text, provider_id, model_id, status: Pending|Succeeded|Failed, error_code, tokens_in, tokens_out, cost_micros, latency_ms, correlation_id, created_at }`, `AiProposal { id, tenant_id, request_id, kind: Formula|ReportDefinition, target: ColumnTarget|WorkspaceTarget, baseline: Option<Json>, proposed: Json, diff: Vec<DiffOp>, explanation, referenced_fields, confidence: f32, limitations: Vec<String>, status: Pending|Applied|Rejected|Expired, applied_at, applied_by, applied_target_version, reject_reason, expires_at, version }`, `AiSettings { tenant_id, enabled, provider_id, model_id, monthly_token_budget, per_user_daily_requests, timeout_ms, redaction_profile: Strict|Standard, retention_days, allowed_kinds, sensitive_preview_required, version }`, `AiUsage { tenant_id, usage_day, actor_id, kind, request_count, tokens_in, tokens_out, cost_micros }`.
- Provider boundary in `crates/domain/src/ai-assist/provider/{mod.rs, budget.rs, breaker.rs, adapters/{bedrock.rs, vertex.rs, azure_foundry.rs, self_hosted.rs, recorded.rs, stub.rs}}`: `trait AiProvider { fn id(&self) -> &'static str; async fn complete(&self, envelope: PromptEnvelope, budget: Budget) -> Result<Completion, ProviderError>; }`; `Completion { json: serde_json::Value, tokens_in, tokens_out, cost_micros, latency_ms }` validated against the per-kind JSON schema in `provider/schemas/`; `Budget { max_input_tokens, max_output_tokens, timeout_ms, max_cost_micros }`; `CircuitBreaker` keyed by `(tenant_id, adapter)` opening after 5 consecutive failures for 60 s.
- Retrieval in `crates/domain/src/ai-assist/retrieval/{scope.rs, schema_card.rs, redaction.rs, envelope.rs}`: `RetrievalScope::resolve(actor, candidates) -> Scope { readable_sheets, readable_columns, denied_sheets }` using one batched F003 `authz/check`; `SchemaCard::build(sheet, scope, sample_budget)` drawing samples only from readable rows; `Redactor::apply(envelope, profile) -> (Envelope, envelope_hash)`.
- Use cases in `crates/domain/src/ai-assist/service.rs`: `generate_formula`, `compile_query`, `execute_query`, `apply_proposal`, `reject_proposal`, `expire_proposals`, `update_settings`, `meter_usage`, `check_limits`.
- API endpoints (`services/api/src/ai-assist/`): `POST /api/v1/ai/formulas`, `POST /api/v1/ai/queries`, `GET /api/v1/ai/queries/{id}`, `POST /api/v1/ai/queries/{id}/execute`, `POST /api/v1/ai/proposals/{id}/apply`, `POST /api/v1/ai/proposals/{id}/reject`, `PATCH /api/v1/tenants/{id}/ai-settings`. DTOs: `FormulaRequest`, `FormulaProposalResponse`, `QueryRequest`, `QueryPlanResponse`, `ExecuteQueryRequest`, `Page<ReportRow>`, `ApplyProposalRequest`, `RejectProposalRequest`, `ProposalResponse`, `AiSettingsRequest`, `AiSettingsResponse`.
- Worker jobs (`services/worker/src/ai-assist/`): `expire_proposals` every 15 minutes; `roll_usage` nightly closing the previous `usage_day` and emitting the tenant budget metric; `purge_request_text` nightly deleting `input_text` and `output_text` older than `retention_days`.
- Events: `ai-proposal.created.v1`, `ai-proposal.applied.v1`, `ai-proposal.rejected.v1`, `ai-query.executed.v1`, published through the outbox with the standard envelope; payloads carry IDs, kind, and counts only, never prompt or completion text.
- Authorization: `resource-viewer` on every referenced sheet for generation and execution; the downstream write role (`sheet-editor` for formulas, `report-editor` for reports) checked at apply time; `tenant-admin` for `ai-settings`; F048 `ai-assist` entitlement plus `F039_FEATURE` gate the router; cross-tenant IDs map to `not_found`.
- Error mapping: `AiError::Disabled → 403 denied`, `::NotEntitled → 403 denied`, `::LimitExceeded → 429 rate_limited`, `::UnusableOutput → 502 unavailable`, `::UncompilablePlan → 502 unavailable`, `::PlanHashMismatch → 409 conflict`, `::ProposalNotPending → 409 conflict`, `::StaleBaseline → 409 conflict`, `::NotFound → 404 not_found`, `ProviderError::Refused → 422 invalid`, `AuthzError::Denied → 403 denied`.
- Seam with F040: F040 depends on `crates/domain/src/ai-assist/provider` and `crates/domain/src/ai-assist/retrieval` as library modules and owns `ai-insights` paths only; F039 owns no insight, scan, evidence, or assisted-action code and F040 adds no adapter, retrieval, or proposal storage of its own.

### PostgreSQL/SQLx

- Migration `*_ai-assist_*.sql` creates `ai_requests(id uuid pk, tenant_id uuid not null, actor_id uuid not null, kind text not null check (kind in ('formula','query')), input_text text, envelope_hash bytea not null, output_text jsonb, rejected_plan jsonb, provider_id text not null, model_id text not null, status text not null, error_code text, tokens_in int not null default 0, tokens_out int not null default 0, cost_micros bigint not null default 0, latency_ms int, correlation_id uuid not null, created_at timestamptz not null)`, `ai_proposals(id uuid pk, tenant_id uuid not null, request_id uuid not null references ai_requests(id) on delete cascade, kind text not null, target_kind text not null, target_id uuid, baseline jsonb, proposed jsonb not null, diff jsonb not null, explanation text not null, referenced_fields jsonb not null, confidence real not null check (confidence >= 0 and confidence <= 1), limitations jsonb not null default '[]', status text not null default 'pending', applied_at timestamptz, applied_by uuid, applied_target_version bigint, reject_reason text, expires_at timestamptz not null, version bigint not null default 1, audit fields)`, `ai_settings(tenant_id uuid pk, enabled boolean not null default false, provider_id text not null, model_id text not null, monthly_token_budget bigint not null default 5000000, per_user_daily_requests int not null default 50 check (per_user_daily_requests between 0 and 1000), timeout_ms int not null default 20000 check (timeout_ms between 1000 and 60000), redaction_profile text not null default 'strict', retention_days int not null default 30 check (retention_days between 1 and 365), allowed_kinds text[] not null default '{formula,query}', sensitive_preview_required boolean not null default true, version bigint not null default 1, audit fields)`, `ai_usage(tenant_id uuid, usage_day date, actor_id uuid, kind text, request_count int not null default 0, tokens_in bigint not null default 0, tokens_out bigint not null default 0, cost_micros bigint not null default 0, primary key (tenant_id, usage_day, actor_id, kind))`.
- Invariants: a proposal's `status` may move only `pending → applied|rejected|expired`, enforced by a conditional update and asserted by a trigger test; `applied` requires `applied_at`, `applied_by`, and `applied_target_version` non-null (check constraint); `expires_at` is always `created_at + interval '24 hours'`; `ai_usage` counters are non-negative.
- Indexes: `ai_requests(tenant_id, created_at desc)`, `ai_requests(tenant_id, actor_id, created_at desc)`, `ai_proposals(tenant_id, status, expires_at)`, `ai_proposals(request_id)`, `ai_usage(tenant_id, usage_day)` for the budget rollup.
- Audit events: `ai.formula-requested`, `ai.query-compiled`, `ai.query-executed`, `ai.proposal-applied`, `ai.proposal-rejected`, `ai.settings-updated`, `ai.limit-exceeded`, `ai.provider-failed`; each records actor, target, and diff and excludes prompt text.
- Retention/deletion: `purge_request_text` nulls `input_text`, `output_text`, and `rejected_plan` past `retention_days`; `ai_requests` rows are kept for 400 days as usage evidence; `ai_proposals` cascade on request delete; rollback drops the four tables and their indexes.

### React/TypeScript

- Routes and surfaces in `apps/web/src/features/ai-assist/`: `AiFormulaPanel.tsx` mounted by the F035 formula editor, `AiQueryPanel.tsx` mounted by the reports list, `ProposalCard.tsx`, `FormulaDiff.tsx`, `PlanDiff.tsx`, `PreviewTable.tsx`, `ApplyConfirmDialog.tsx`, `AiSettingsPage.tsx` at `/admin/ai-settings`, plus `api.ts`, `hooks.ts`, `routes.ts`.
- State: TanStack Query keys `['ai-proposal', proposalId]`, `['ai-query', queryId]`, `['ai-query-rows', queryId, cursor]`, `['ai-settings', tenantId]`; generation is a mutation with an `AbortController` bound to the cancel control; applying invalidates the F035 column key and the F021 reports list key.
- API client: generated `AiAssistApi` with `generateFormula`, `compileQuery`, `getQuery`, `executeQuery`, `applyProposal`, `rejectProposal`, `updateAiSettings`.
- Telemetry: `ai_prompt_submitted`, `ai_proposal_shown`, `ai_proposal_applied`, `ai_proposal_rejected`, `ai_proposal_regenerated`, `ai_query_previewed`, `ai_limit_hit` with `kind`, `request_id`, and `confidence` bucket; no prompt text is sent to telemetry.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F039-01 through FR-F039-16 in `testing/features/F039/requirements/cases.md`
- [ ] Failure/edge-case tests: unparseable formula twice, uncompilable plan twice, malformed provider JSON then repair, provider refusal, provider timeout, circuit breaker open and close, `plan_hash` mismatch, stale `If-Match` on apply, expired proposal, daily and monthly limit exhaustion
- [ ] Permission-negative and tenant-isolation tests: sheet the caller cannot read never appears in the envelope or the plan, a viewer cannot apply a formula proposal, another actor cannot read a foreign proposal, cross-tenant proposal and query IDs return `not_found`, revoking access between generation and apply blocks the apply
- [ ] Rust unit tests: `crates/domain/src/ai-assist/` retrieval scope resolution, schema card sampling, redaction patterns and hashing, diff computation, budget and circuit breaker, provider error mapping
- [ ] API contract/integration tests: all seven routes with success and every mapped error code against the `recorded` adapter
- [ ] Database migration/constraint tests: status transition guard, applied-columns check, expiry derivation, usage primary key, rollback
- [ ] React component tests: `ProposalCard`, `FormulaDiff`, `PlanDiff`, `PreviewTable`, `ApplyConfirmDialog`, `AiSettingsPage` states including disabled, not-entitled, rate-limited, stale, expired
- [ ] Browser E2E tests: generate and apply a formula, compile and preview a query then save it as a report, reject a proposal, hit the daily limit
- [ ] Accessibility tests: axe on both panels, the diff view, and the settings page; live-region announcements; diff not color-only
- [ ] Performance/load tests: retrieval scope for 20 sheets, request path excluding provider latency, apply path, query read
- [ ] Evaluation tests: permission leakage, grounding, refusal, formula exact-match, plan compilability suites under `testing/features/F039/evaluation/`

### Fast fanout configuration

- Test harness path: `testing/features/F039/`
- Feature flag: `F039_FEATURE` with the F048 `ai-assist` entitlement seeded `active`
- Fixture/seed factory: `testing/fixtures/ai_assist.rs` builds tenants A and B, a viewer, a sheet-editor, a report-editor, a tenant-admin, sheets `Launch plan` (200 rows, columns `Status`, `Due date`, `Owner`, `Days late`), `Risks` (120 rows), and `Finance FY26` (readable only by the admin, used for the leakage suite), a sensitive-marked `Salary` column, 20 sheets for the scope benchmark, and seeded `ai_settings`
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC, fixed `envelope_hash` salt, fixed cassette ordering
- Mock/stub contracts: `recorded` adapter replaying `testing/features/F039/evaluation/cassettes/<suite>/<prompt_hash>.json`; `stub` adapter returning scripted `Completion` and `ProviderError` values for error-path tests; socket guard failing any outbound connection; F035 parse/evaluate and F021 validator/read paths exercised for real against the seeded tenant
- Parallel isolation: one schema per test worker, tenant ID per test, cassette directory read-only
- Targeted command: `cargo xtask test-feature F039`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F039/`

## 6. Acceptance criteria

```gherkin
Feature: Permission-aware AI formulas and natural-language queries

Scenario: Formula proposal is previewed and applied as a diff
  Given a sheet-editor on sheet "Launch plan" with a formula column "Days late"
  When they ask for "days between the due date and today, blank when done"
  Then a pending proposal is stored with the formula, referenced fields, and a 5-row preview from the F035 evaluate route
  And ai-proposal.created.v1 is published and nothing is written to the column
  When they apply the proposal with the current column version
  Then the column formula is set through F035, status is applied, and ai-proposal.applied.v1 is published

Scenario: Retrieval never includes sheets the asker cannot read
  Given a viewer with read access to "Launch plan" and "Risks" but not "Finance FY26"
  When they ask "open risks per owner across the launch sheets"
  Then the prompt envelope contains schema cards for two sheets only
  And the response lists "Finance FY26" under excluded_sources with reason denied
  And no value from "Finance FY26" appears in the plan, the explanation, or the executed rows

Scenario: Stale baseline blocks a silent overwrite
  Given a pending formula proposal generated against column version 4
  When another user changes the column formula so its version becomes 5
  And the first user applies the proposal with If-Match 4
  Then the response is 409 conflict with current_version 5 and the proposal stays pending
  And the recomputed diff is returned marked stale

Scenario: Evaluation harness runs offline against recorded completions
  Given AI_PROVIDER is recorded and the outbound socket guard is active
  When the permission-leakage, grounding, refusal, formula, and plan suites run
  Then no network connection is attempted, leakage and grounding failures are zero, and the formula and plan thresholds are met
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F035 (parse, evaluate, `PUT /formula`, error codes), F021 (`ReportDefinition` validator, ad-hoc read path, row shape and meta), F048 (`ai-assist` entitlement and `F039_FEATURE` evaluation); F003 batched `authz/check` and audit storage; F007 column metadata for `sensitive`; F027 retention sweep
- Blocks: F040 (insights and assisted actions build on the provider, retrieval, proposal, and evaluation seams)
- Conflicts with: none; `ai-assist` and `ai-insights` module paths are disjoint
- External dependencies: one deployment-configured model endpoint per adapter; tests never call it
- Risks and mitigations: permission leakage through samples, mitigated by scope-first retrieval, the redaction pass, and a zero-failure leakage suite; model output that does not parse or compile, mitigated by schema validation, the F035 parser, the F021 validator, and one bounded repair attempt; silent mutation, mitigated by proposal-only writes with `If-Match` and apply-time role checks; runaway cost, mitigated by per-request budgets, daily and monthly limits checked before egress, and usage metering; provider outage, mitigated by timeout, circuit breaker, and a stable `unavailable` error; evaluation drift when a prompt changes, mitigated by cassettes keyed on the envelope hash so a changed prompt fails loudly instead of silently re-recording
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F035, F021, and F048 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F039/`
- [ ] Migration file name and owned paths claimed, including `services/worker/src/ai-assist/**`
- [ ] Cassette sets recorded under `testing/features/F039/evaluation/cassettes/` and the socket guard in place
- [ ] F048 `ai-assist` entitlement and limit schema registered

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, performance, and evaluation gates pass
- [ ] Permission-leakage and grounding suites report zero failures with a positive control proving the suites fail on an injected leak
- [ ] Audit and outbox events verified for generation, execution, apply, reject, and settings changes; no prompt text in logs, events, or telemetry
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F039_FEATURE`, revoke the `ai-assist` entitlement, run the down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Users can ask for a formula in the F035 editor or a question on the reports list and receive a reviewable proposal: formula or compiled report plan, explanation, referenced fields, confidence, limitations, and a preview computed only from rows they can already read. Nothing is written until they apply the diff. Tenant admins control the provider, model, redaction profile, retention, budgets, and per-user daily limits.
- Migration adds `ai_requests`, `ai_proposals`, `ai_settings`, and `ai_usage`; rollback drops them. The module is off by default behind `F039_FEATURE` and the F048 `ai-assist` entitlement, and every model call is bounded by a per-request budget, a timeout, and a per-tenant circuit breaker.
