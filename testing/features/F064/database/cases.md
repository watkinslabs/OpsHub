# F064 database cases

File: `testing/features/F064/database/{migration_tests.rs,constraint_tests.rs,append_only_tests.rs}`. Flag `F064_FEATURE`. PostgreSQL 18.

- `billing_tables_exist_with_constraints` — T253: `subscriptions`, `invoices`, `usage_records`, `billing_webhook_events` exist with the tenant, version, and audit columns named in ticket section 4.
- `one_subscription_per_tenant` — FR-F064-01: a second `subscriptions` row for the same `tenant_id` violates the unique constraint, so the synthetic free response can never shadow a real row.
- `plan_check_matches_tenant_plan_values` — FR-F064-02: `plan` accepts only `free`, `team`, `enterprise`, the same set as `tenants.plan` in FR-F002-02; `status` accepts only the six lifecycle values.
- `webhook_event_id_unique_per_provider` — FR-F064-09: a duplicate `(provider, provider_event_id)` insert raises inside the applying transaction, which is what makes replay protection structural rather than a code check.
- `usage_records_reject_update_and_delete` — FR-F064-12: `usage_records_no_update` and `usage_records_no_delete` raise on a direct `UPDATE` and `DELETE`, including from a superuser session.
- `adjustment_without_reason_rejected` — FR-F064-12: `kind: adjustment` without `corrects_record_id`, or with a reason shorter than 10 or longer than 500 characters, violates the check constraint.
- `sample_quantity_non_negative` — FR-F064-11: a negative quantity is allowed only for `kind: adjustment`.
- `usage_unique_key_blocks_double_meter` — NFR-F064-04: a repeated `(tenant_id, metric, period_date, kind, source_ref)` insert is rejected, so a meter re-run after a restart is a no-op.
- `usage_partition_created_for_period_year` — NFR-F064-01: inserting a 2027 `period_date` lands in the 2027 range partition and a query for one month prunes to a single partition.
- `dunning_index_used_for_ladder_scan` — FR-F064-13: `EXPLAIN` on the daily ladder scan uses the partial index `subscriptions(dunning_next_action_at) where dunning_stage > 0`.
- `invoice_provider_id_unique` — FR-F064-10: a repeated `provider_invoice_id` is rejected, so a redelivered `invoice.finalized` upserts rather than duplicates.
- `rollback_drops_billing_tables` — T253: `sqlx migrate revert` removes the four tables, their partitions, rules, and indexes, and leaves the F048 `entitlements` table intact.

Evidence: migration log, rule failure output, and `EXPLAIN` plans under `testing/evidence/F064/database/`.
- `credit_code_hash_unique_and_plaintext_absent` — FR-F064-16: `credit_codes(code_hash)` is unique and the table has no column capable of holding plaintext.
- `credit_redemption_claim_is_atomic` — FR-F064-17: the conditional update on `redeemed_at is null` and the `credit_ledger` insert commit together; a forced conflict rolls back both.
- `credit_ledger_is_append_only` — FR-F064-18: update and delete on `credit_ledger` are rejected at the database level, as `usage_records` are.

