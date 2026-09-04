---
id: T154
type: task
status: planned
parent_epic: E008
parent_feature: F039
parent_story: S077
depends_on: [S077]
owned_paths: [crates/domain/src/ai-assist/retrieval/**, crates/domain/src/ai-assist/query/**, testing/features/F039/api/**]
feature_flag: F039_FEATURE
branch: t154-permission-filtered-retrieval
started_at: null
finished_at: null
---

# T154 — Permission-filtered retrieval

## Identity

- Parent story: `S077` formula help
- Owner: platform
- Branch: `t154-permission-filtered-retrieval`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 7; `docs/capability-contracts.md` rows F003 and F039

## Objective

Build the retrieval layer that decides what the model is allowed to see: resolve the caller's read scope from F003, assemble schema cards and samples only from readable sheets, columns, and rows, redact sensitive values, hash the envelope, and compile natural-language questions into validated F021 report definitions. This layer is the second seam F040 consumes and is the only place an envelope is constructed.

## Specification

- Owned files: `crates/domain/src/ai-assist/retrieval/{mod.rs, scope.rs, schema_card.rs, redaction.rs, envelope.rs}`; `crates/domain/src/ai-assist/query/{mod.rs, prompt.rs, compile.rs, validate.rs, execute.rs}`.
- Contract/input: `RetrievalScope::resolve(actor: ActorContext, candidates: Candidates) -> Scope { readable_sheets: Vec<SheetId>, readable_columns: HashMap<SheetId, Vec<ColumnId>>, denied_sheets: Vec<(SheetId, DeniedReason)> }` using exactly one batched F003 `POST /api/v1/authz/check`; `SchemaCard::build(sheet, scope, sample_budget) -> SchemaCard { sheet_id, name, columns: Vec<ColumnCard { column_id, label, column_type, samples: Vec<Value> }> }` with at most 3 samples per column, 200 samples per envelope, and 20 sheets per envelope, samples drawn only from rows the caller can read; `Redactor::apply(envelope, profile: Strict|Standard) -> (Envelope, envelope_hash)`; `QueryCompiler::compile(question, scope, completion) -> Result<ReportDefinition, CompileError>`.
- Output/behavior: the redactor replaces email, E.164 phone, and 13–19 digit card matches with `<redacted:email>`, `<redacted:phone>`, `<redacted:card>` and under `strict` drops every column whose F007 metadata sets `sensitive: true`; redaction runs on the serialized envelope and its BLAKE3 hash is returned as `envelope_hash` so no envelope content is persisted. `compile` maps the completion into an F021 `ReportDefinition` restricted to `scope.readable_sheets`, rejects any alias referencing a denied sheet, runs the F021 definition validator (sources 1–20, joins forming a tree rooted at `sources[0]`, filter depth ≤ 4 and ≤ 50 predicates, `group_by` ≤ 3, `aggregates` ≤ 20, `calculated_fields` ≤ 25 parsed with F035), and on failure returns `CompileError { field_errors }` so T153 can request exactly one regeneration; a second failure surfaces `AiError::UncompilablePlan → 502 unavailable` and the rejected plan is stored on the `ai_requests` row. `execute` runs a stored plan through the F021 ad-hoc read path under the caller's live permissions and returns rows plus `meta { computed_at, duration_ms, restricted_sources, hidden_columns, truncated }`. `plan_hash` is the BLAKE3 hash of the canonicalized plan and a mismatch on execute returns `409 conflict` with `current_plan_hash`.
- Dependencies: F003 batched `authz/check` and field-level ACL; F007 column metadata including `sensitive`; F021 definition validator and read path; F035 parser for calculated fields; T153 provides the transport that sends the finished envelope.
- Feature flag: `F039_FEATURE`; the retrieval layer is a library module with no routes of its own and is called from the T153 handlers.
- Rollback: no schema change; disabling `F039_FEATURE` removes every caller.

## TDD

- Failing test first: `testing/features/F039/api/retrieval_tests.rs::scope_resolves_from_single_batched_authz_check`, `::envelope_excludes_unreadable_sheet_values`, `::envelope_excludes_field_acl_hidden_columns`, `::samples_come_only_from_readable_rows`, `::sample_budget_capped_at_two_hundred_values`, `::sheet_budget_capped_at_twenty`, `::strict_profile_redacts_email_and_sensitive_columns`, `::standard_profile_keeps_sensitive_columns_but_redacts_patterns`, `::envelope_hash_is_stable_and_content_free`; `testing/features/F039/api/query_tests.rs::question_compiles_to_valid_report_definition`, `::plan_referencing_denied_sheet_is_rejected`, `::uncompilable_plan_regenerates_once_then_unavailable`, `::excluded_sources_report_denied_reason`, `::execute_rejects_mismatched_plan_hash`, `::execute_drops_restricted_sources_for_viewer`, `::execute_publishes_ai_query_executed`, `::foreign_tenant_query_returns_not_found`
- Targeted command: `cargo xtask test-feature F039`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/ai_assist.rs` with `Launch plan`, `Risks`, admin-only `Finance FY26`, a `sensitive` `Salary` column, and a viewer, sheet-editor, report-editor, and tenant-admin; `recorded` cassettes under `testing/features/F039/evaluation/cassettes/plan/`; fixed clock and fixed hash salt

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Envelope construction exists in exactly one module and a grep gate proves no other module builds a `PromptEnvelope`
- [ ] Permission-negative tests pass for viewer, denied sheet, hidden column, and cross-tenant cases
- [ ] Owned-path check passes and `crates/domain/src/ai-assist/provider/**` is left to T153
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S077
- [ ] `finished_at` recorded
