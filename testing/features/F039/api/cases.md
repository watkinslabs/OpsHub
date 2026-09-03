# F039 api cases

File: `testing/features/F039/api/{provider_tests.rs,retrieval_tests.rs,formula_tests.rs,query_tests.rs,proposal_tests.rs,settings_tests.rs,usage_tests.rs,negative_tests.rs}`. Flag `F039_FEATURE`, `AI_PROVIDER=recorded`, socket guard active.

- `budget_timeout_maps_to_unavailable` — FR-F039-10: `stub` adapter exceeds `timeout_ms` → `502 unavailable`, `ai.provider-failed` audit row, no proposal written.
- `malformed_output_repairs_once_then_unavailable` — FR-F039-10: completion failing `provider/schemas/formula.json` triggers exactly one repair call; a second failure → `502 unavailable` `unusable_output`.
- `refusal_maps_to_invalid_with_field_error` — FR-F039-10: `ProviderError::Refused` → `422 invalid` with `field_errors.prompt = "refused"` and no retry.
- `rate_limited_sets_retry_after` — FR-F039-10: `ProviderError::RateLimited` → `429 rate_limited` with `Retry-After`.
- `breaker_opens_after_five_consecutive_failures` — NFR-F039-04: five failures → every route `503 unavailable` with `retry_after_seconds`; a sixth call makes no provider request.
- `breaker_closes_after_sixty_seconds` — NFR-F039-04: advancing the fixed clock 60 s lets the next call through.
- `no_adapter_constructed_outside_provider_module` — FR-F039-09: grep gate over `crates` and `services` finds no model HTTP client outside `ai-assist/provider/adapters/`.
- `scope_resolves_from_single_batched_authz_check` — FR-F039-07: one `POST /api/v1/authz/check` call for 20 candidate sheets; the recorded call count is exactly 1.
- `envelope_excludes_unreadable_sheet_values` — FR-F039-07: viewer without `Finance FY26` → envelope holds two schema cards and no `Finance FY26` name, column label, or value.
- `envelope_excludes_field_acl_hidden_columns` — FR-F039-07: a column hidden by F003 field-level ACL is absent from the card and from `referenced_fields`.
- `samples_come_only_from_readable_rows` — FR-F039-07: row-level denial on 40 of 200 rows → no sample originates from those rows.
- `sample_budget_capped_at_two_hundred_values` — FR-F039-07: 20 sheets of 40 columns → envelope carries 200 samples and records `sample_truncated: true`.
- `strict_profile_redacts_email_and_sensitive_columns` — FR-F039-08: `Owner email` values become `<redacted:email>` and the `Salary` column is dropped entirely.
- `envelope_hash_is_stable_and_content_free` — FR-F039-08, NFR-F039-02: same inputs → same `envelope_hash`; the stored row contains no envelope text.
- `formula_request_creates_pending_proposal` — FR-F039-01: `ai_requests` and pending `ai_proposals` rows written and `ai-proposal.created.v1` published; the column is untouched.
- `preview_uses_f035_evaluate_for_five_readable_rows` — FR-F039-02: five F035 evaluate calls against readable rows; a sixth row is not evaluated.
- `unparseable_formula_regenerates_once_then_unavailable` — FR-F039-02: the F035 parser message is appended to the second envelope; a second failure → `502 unavailable`.
- `preview_error_caps_confidence_at_half` — FR-F039-02: one preview row with `status: error` → stored `confidence` ≤ `0.5`.
- `question_compiles_to_valid_report_definition` — FR-F039-03: plan passes the F021 validator and carries aliases only for readable sheets.
- `plan_referencing_denied_sheet_is_rejected` — FR-F039-03: a completion naming `Finance FY26` is rejected before validation and the sheet is listed in `excluded_sources` with reason `denied`.
- `uncompilable_plan_regenerates_once_then_unavailable` — FR-F039-04: `field_errors` appended once; second failure → `502 unavailable` `uncompilable_plan` with `rejected_plan` stored.
- `execute_rejects_mismatched_plan_hash` — FR-F039-06: stale `plan_hash` → `409 conflict` with `current_plan_hash` and no execution.
- `execute_drops_restricted_sources_for_viewer` — FR-F039-06: viewer execution lists `meta.restricted_sources` and returns no row from those sheets.
- `execute_publishes_ai_query_executed` — FR-F039-06: `ai-query.executed.v1` carries `query_id`, `row_count`, `duration_ms`, `source_count` and no question text.
- `apply_requires_sheet_editor_and_matching_version` — FR-F039-11: viewer apply → `403 denied`; sheet-editor with current `If-Match` → F035 `PUT /formula` called once and `ai-proposal.applied.v1` published.
- `apply_stale_version_returns_conflict_with_recomputed_diff` — FR-F039-11, FR-F039-13: baseline moved to version 5 → `409 conflict` with `current_version` and a `stale: true` diff; the proposal stays pending.
- `apply_is_idempotent_for_same_key` — FR-F039-11: replaying `Idempotency-Key` returns the first result; a different body with the same key → `409 conflict`.
- `reject_sets_status_and_publishes_rejected` — FR-F039-12: reason stored, `ai-proposal.rejected.v1` published, second reject → `409 conflict`.
- `expired_proposal_apply_returns_conflict` — FR-F039-12: clock advanced 24 h and the expiry job run → `409 conflict` with `current_status: expired`.
- `disabled_settings_denies_every_route` — FR-F039-14: `enabled: false` → all seven routes `403 denied` with `reason: "ai_disabled"`.
- `non_admin_cannot_patch_ai_settings` — FR-F039-14: sheet-editor `PATCH /ai-settings` → `403 denied`.
- `daily_limit_blocks_before_provider_call` — FR-F039-15: 51st request in a day → `429 rate_limited` with `limit: "per_user_daily"` and zero provider calls recorded.
- `monthly_token_budget_blocks_before_provider_call` — FR-F039-15: budget exhausted → `429 rate_limited` with `limit: "tenant_monthly"` and `resets_at`.
- `missing_entitlement_denies_router` — FR-F039-15: F048 `ai-assist` set to `none` → `403 denied` with `reason: "not_entitled"`.
- `foreign_tenant_ids_return_not_found` — NFR-F039-02: tenant B proposal and query IDs → `404` on get, execute, apply, and reject.
- `no_prompt_text_in_logs_events_or_audit` — NFR-F039-02: captured log lines, outbox payloads, and `audit_events` rows contain neither the prompt nor the completion.

Evidence: JUnit output, recorded provider call counts, and cassette manifests under `testing/evidence/F039/api/`.
