# F039 database cases

File: `testing/features/F039/database/{ai_assist_migration_tests.rs,constraint_tests.rs,retention_tests.rs}`. Flag `F039_FEATURE`. PostgreSQL 18, one schema per worker.

- `ai_assist_tables_exist_with_constraints` — T153: `ai_requests`, `ai_proposals`, `ai_settings`, `ai_usage` exist with tenant columns, `envelope_hash bytea not null`, and the confidence, `per_user_daily_requests`, `timeout_ms`, and `retention_days` check constraints.
- `proposal_status_transition_guarded` — FR-F039-12: `pending → applied` and `pending → rejected` succeed; `applied → pending`, `rejected → applied`, and `expired → applied` are rejected by the conditional update.
- `applied_proposal_requires_actor_and_version` — FR-F039-11: setting `status = 'applied'` without `applied_at`, `applied_by`, or `applied_target_version` violates the check constraint.
- `expires_at_derived_from_created_at` — FR-F039-12: inserted proposals carry `expires_at = created_at + interval '24 hours'`; a different value is rejected.
- `usage_primary_key_is_tenant_day_actor_kind` — FR-F039-15: a duplicate `(tenant_id, usage_day, actor_id, kind)` row violates the primary key; counters are non-negative.
- `proposals_cascade_on_request_delete` — FR-F039-01: deleting an `ai_requests` row removes its proposals.
- `budget_rollup_uses_usage_day_index` — NFR-F039-01: `EXPLAIN` on the monthly token sum for one tenant uses `ai_usage(tenant_id, usage_day)`.
- `pending_proposal_scan_uses_status_expiry_index` — NFR-F039-04: `EXPLAIN` on the expiry job's selection uses `ai_proposals(tenant_id, status, expires_at)`.
- `purge_clears_request_text_after_retention` — NFR-F039-02: with `retention_days = 30`, the nightly job nulls `input_text`, `output_text`, and `rejected_plan` on older rows while keeping counters and `envelope_hash`.
- `settings_row_is_one_per_tenant` — FR-F039-14: a second `ai_settings` row for the same tenant violates the primary key.
- `rollback_drops_ai_assist_tables` — T153: `sqlx migrate revert` removes the four tables and their indexes with no orphaned types.

Evidence: migration log, constraint violation output, and `EXPLAIN` plans under `testing/evidence/F039/database/`.
