# F047 database cases

File: `testing/features/F047/database/{migration_tests.rs,constraint_tests.rs}`. Flag `F047_FEATURE`.

- `mcp_tables_exist_with_checks_and_indexes` — T187: `mcp_confirmations`, `mcp_audit`, `mcp_rate_limits` exist with the status, decision, outcome, and bucket check constraints and the indexes from ticket section 4.
- `mcp_audit_rows_are_immutable` — FR-F047-11: `UPDATE` and `DELETE` on `mcp_audit` raise `audit_immutable`; `INSERT` succeeds.
- `audit_partitions_created_three_months_ahead` — FR-F047-11: the migration creates monthly partitions for the current and next three months; a row past the last partition fails until the monthly job runs.
- `open_confirmation_unique_per_arguments_hash` — FR-F047-08: a second `pending` row for the same `(tenant_id, token_id, tool, arguments_hash)` violates `mcp_confirmations_open_idx`; the same tuple is allowed once the first is `consumed`.
- `consumed_requires_consumed_at` — FR-F047-10: `status = 'consumed'` with a null `consumed_at` violates the check, and a non-null `consumed_at` on a `pending` row does too.
- `approved_requires_approved_at` — FR-F047-09: `status in ('approved','consumed')` with a null `approved_at` violates the check.
- `confirmation_indexes_used_for_sweeper` — NFR-F047-04: `EXPLAIN` on the expiry sweep uses `mcp_confirmations(tenant_id, status, expires_at)`.
- `audit_index_used_for_actor_scoped_page` — FR-F047-14: `EXPLAIN` on a member's audit page uses `mcp_audit(tenant_id, actor_id, occurred_at desc)`.
- `rate_bucket_upsert_is_single_statement` — FR-F047-12: concurrent refills on one `(tenant_id, token_id, bucket)` row converge with no lost update.
- `rollback_drops_mcp_tables` — T187: `sqlx migrate revert` removes the three tables, their partitions, and the immutability trigger.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F047/database/`.
