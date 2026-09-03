# F048 api cases

File: `testing/features/F048/api/{entitlement_tests.rs,flag_tests.rs,evaluate_tests.rs,guard_tests.rs}`. Flag `F048_FEATURE`.

- `entitlement_list_synthesizes_none_rows` — FR-F048-01: two stored rows → ten modules returned, missing ones `state: none`, `version: 0`.
- `entitlement_upsert_rejects_unknown_limit_key` — FR-F048-02: `data-shuttle` with `limits.max_widgets` → 400 `invalid`, `field_errors.limits.max_widgets`.
- `entitlement_trial_requires_end_date` — FR-F048-02: `state: trial` without `trial_ends_at` → 400 with `field_errors.trial_ends_at`.
- `entitlement_unknown_module_not_found` — FR-F048-02: PUT `/entitlements/control-tower` → 404 `not_found`.
- `entitlement_member_upsert_denied` — NFR-F048-02: member role PUT → 403 `denied`, no row written.
- `entitlement_cross_tenant_body_invalid` — FR-F048-15: body carrying tenant B id → 400; tenant B GET shows no tenant A rows.
- `entitlement_upsert_writes_audit_and_outbox` — FR-F048-11: PUT → one `audit_events` row with before/after and one `entitlement.updated.v1` outbox row.
- `flag_list_returns_registry_with_caller_override` — FR-F048-03: 11 seeded keys; tenant A sees its override, not tenant B's.
- `flag_override_set_and_clear` — FR-F048-04: PATCH override on → evaluate `reason: override`; PATCH `override: null` → `reason: default`.
- `flag_platform_field_denied_for_tenant_admin` — FR-F048-04: tenant-admin PATCH `rollout_state` → 403, version unchanged.
- `flag_invalid_transition_conflicts` — FR-F048-05: `draft`→`general` → 409 `field_errors.rollout_state = invalid_transition`.
- `flag_retire_requires_cleanup_ticket` — FR-F048-05: `retired` without `cleanup_ticket` or with 10-char procedure → 409.
- `flag_kill_suspends_all_overrides` — FR-F048-06: kill → `default_enabled false`, `internal`, every override `suspended`, `feature-flag.updated.v1 { killed: true }`.
- `flag_expired_override_ignored` — FR-F048-13: `expires_at` in the past → evaluate uses default; list shows `override.expired: true`.
- `evaluate_marks_expired_trial` — FR-F048-09: `bridge` trial ended → `allowed: false`, `reason: trial_expired`.
- `evaluate_flag_disabled_blocks_active_module` — FR-F048-09: `data-shuttle` active but `F052_FEATURE` draft → `reason: flag_disabled`.
- `evaluate_rejects_more_than_50_keys` — FR-F048-07: 51 keys → 400; 21 modules → 400.
- `decide_flag_truth_table` — FR-F048-08: every rollout state × override combination yields the specified `enabled`/`reason`.
- `decide_flag_percentage_bucket_is_stable` — FR-F048-08: fixture tenant buckets equal precomputed murmur3 values across 1,000 runs.
- `module_guard_denies_before_handler` — FR-F048-10: probe route behind `RequireModule(Bridge)` → 403 with `field_errors.module`, probe counter 0.
- `module_guard_cache_invalidated_by_event` — FR-F048-12: allow → publish `entitlement.updated.v1` suspending → next request denied without waiting for TTL.
- `guard_span_and_metric_recorded` — NFR-F048-04: denial increments `entitlement_denied_total{module="bridge",reason="suspended"}`; span has `tenant_id`, `module`, `correlation_id`.
- `override_reason_not_logged` — NFR-F048-02: log capture contains no override reason text.

Evidence: JUnit output and request logs under `testing/evidence/F048/api/`.
