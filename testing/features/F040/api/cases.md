# F040 api cases

File: `testing/features/F040/api/{scan_tests.rs,detector_tests.rs,evidence_tests.rs,insight_read_tests.rs,gate_tests.rs,risk_tests.rs,reject_tests.rs,proposal_tests.rs,safety_tests.rs,budget_tests.rs,executor_tests.rs,injection_tests.rs,sanitize_tests.rs}`. Flag `F040_FEATURE`.

- `scan_rejects_scope_over_twenty_thousand_records` — FR-F040-01: an estimated 20,001-record scope → 400 `invalid` with `field_errors.scope = "scope_too_large"`.
- `scan_returns_queued_scan_id` — FR-F040-01: 202 with `scan_id`, `detectors`, `estimated_records`; the job appears on the queue.
- `scan_resumes_after_restart_without_duplicates` — NFR-F040-04: cancel after detector 3 and re-run → no duplicate insights, same `scan_id`.
- `schedule_risk_flags_rows_due_within_seven_days` — FR-F040-02: 12 seeded rows flagged, a row at 8 days or 60% complete is not.
- `stalled_work_needs_fourteen_quiet_days` — FR-F040-02: a comment on day 13 clears the candidate; silence to day 14 does not.
- `overallocation_uses_iso_weeks_within_four_weeks` — FR-F040-02: 101% in week 3 flagged, 100% and week 5 not.
- `missing_data_requires_ten_percent_null` — FR-F040-02: 30/200 null flagged; 19/200 not.
- `throughput_trend_needs_five_nonzero_weeks` — FR-F040-02: 8 weeks with 4 non-zero produce no candidate; a 25% slope over 5 does.
- `approval_bottleneck_flags_three_day_pending` — FR-F040-02: 5 approvals pending 4 days flagged with their approval ids as evidence.
- `insight_requires_at_least_one_evidence_row` — FR-F040-03: a narration with empty `evidence_indexes` → nothing persisted.
- `evidence_records_source_version_and_deep_link` — FR-F040-03: each evidence row carries `source_version`, `observed_at`, and a server-generated `deep_link`.
- `out_of_range_evidence_index_discards_insight` — FR-F040-04: index 99 on 4 candidates → no row, no event, audit `ai-insight.evidence-rejected`.
- `model_text_with_foreign_uuid_discards_insight` — FR-F040-04: a UUID in `summary` absent from the retrieval set discards the insight.
- `rescan_same_fingerprint_increments_occurrence_count` — FR-F040-05: second scan → `occurrence_count 2`, one `ai-insight.generated.v1` total.
- `insight_hidden_when_evidence_row_unreadable` — FR-F040-06: the viewer's list omits the insight citing the private sheet; the manager's includes it.
- `insight_list_filters_and_pages` — FR-F040-06: `kind=stalled_work&severity=high` narrows; cursor pages 120 insights sorted by severity then `last_seen_at`.
- `foreign_tenant_insight_returns_not_found` — FR-F040-07: tenant B insight id → 404 on get and dismiss.
- `dismiss_kind_for_scope_suppresses_for_thirty_days` — FR-F040-08: re-scan inside 30 days produces no insight for that fingerprint.
- `propose_action_writes_nothing_to_targets` — FR-F040-09: the F008 recorder shows zero calls; row versions unchanged.
- `preview_hash_is_stable_for_same_preview` — FR-F040-09: identical previews hash equal; a changed `after` value changes the hash.
- `unknown_action_kind_rejected` — FR-F040-10: `delete_rows` → 400 `not_allowed`.
- `target_outside_evidence_rejected` — FR-F040-10: a row id absent from the insight evidence → 400 `target_not_in_evidence`.
- `more_than_twenty_five_targets_rejected` — FR-F040-09: 26 targets → 400 `invalid`.
- `confirm_requires_human_principal` — FR-F040-11: a service token → 403 `denied` with `reason: human_confirmation_required`, no run row.
- `confirm_requires_workflow_editor_role` — FR-F040-11: a `resource-viewer` → 403 `denied`.
- `confirm_rejects_stale_preview_hash_with_rerendered_diff` — FR-F040-11: a target edited after preview → 409 `conflict` with the new diff.
- `confirm_rejects_expired_proposal_and_marks_expired` — FR-F040-11: 24h+1m old → 409 `proposal_expired`, status `expired`.
- `confirm_is_idempotent_for_repeated_key` — NFR-F040-04: the same `Idempotency-Key` twice → one `ai-action.confirmed.v1` and one run.
- `create_workflow_draft_is_high_risk` — FR-F040-12: `risk_class: high`; six targets on `set_field` also `high`.
- `high_risk_confirm_requests_approval_before_running` — FR-F040-12: approval created, status `awaiting_approval`, the F018 recorder shows no draft.
- `approval_denied_marks_action_rejected` — FR-F040-12: `approval.decided.v1` with `denied` → `rejected` and `ai-action.rejected.v1`.
- `run_denied_when_permission_lost_after_confirm` — FR-F040-13: revoking edit on one target → run `denied`, zero rows changed.
- `applied_targets_records_resulting_versions` — FR-F040-13: four rows updated → four ids with post-update versions.
- `run_is_idempotent_for_repeated_idempotency_key` — NFR-F040-04: replay → unique violation on `ai_action_runs(tenant_id, idempotency_key)`, one application.
- `run_dead_letters_after_two_retries` — NFR-F040-04: three failures → dead-letter, action `failed`, metric recorded.
- `reject_records_reason_and_publishes_event` — FR-F040-14: reason stored, `ai-action.rejected.v1` published.
- `reject_applied_action_returns_conflict` — FR-F040-14: rejecting an applied action → 409.
- `fifth_scan_in_an_hour_is_rate_limited` — FR-F040-15: 429 `rate_limited` with `retry_after_seconds`.
- `same_scope_within_fifteen_minutes_is_rate_limited` — FR-F040-15: identical scope at minute 14 → 429; at minute 15 → 202.
- `five_provider_errors_open_circuit_for_fifteen_minutes` — FR-F040-15: sixth call → 503 `unavailable`; recovery after 15 minutes.
- `budget_exhausted_blocks_scan_before_provider_call` — NFR-F040-05: stub records zero calls; response 429.
- `insight_records_token_usage_and_cost_micros` — NFR-F040-05: usage fields match the stub accounting; ≤ 15,000 prompt tokens per 1,000-row pass.
- `injected_comment_cannot_create_confirmed_action` — FR-F040-16: no `ai_actions` row reaches `confirmed` without a confirm call.
- `injected_row_text_cannot_reference_other_tenant_records` — NFR-F040-02: tenant B ids absent from insights, events, logs, and the prompt transcript.
- `injected_payload_cannot_add_action_kind_outside_allowlist` — FR-F040-10: `share_externally` never accepted.
- `narration_breaking_response_schema_is_discarded` — FR-F040-04: a non-conforming narration is dropped, not coerced.
- `injection_block_writes_audit_and_metric` — FR-F040-16: `ai-insight.injection-blocked` audit and `ai_injection_blocked_total{vector}` increment.
- `escapes_html_in_summary` — FR-F040-16: `<img onerror=...>` stored escaped; markdown links and images stripped; `deep_link` values preserved.

Evidence: JUnit output and provider stub transcripts under `testing/evidence/F040/api/`.
