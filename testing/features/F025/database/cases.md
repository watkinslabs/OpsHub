# F025 database cases

File: `testing/features/F025/database/{migration_tests.rs,constraint_tests.rs}`. Flag `F025_FEATURE`.

- `report_exports_table_exists_with_constraints` — FR-F025-09: `report_exports` exists with `tenant_id`, `source_kind`, `format`, `options`, `scope_key`, `status`, `progress_pct`, `attempts`, `version`, and audit columns.
- `idempotency_key_unique_per_requester` — FR-F025-12: a second row with the same `(tenant_id, requested_by, idempotency_key)` violates the unique index.
- `completed_row_requires_storage_and_expiry` — FR-F025-09: `status: completed` without `storage_key`, `checksum`, or `expires_at` violates the check constraint.
- `format_must_match_source_kind` — FR-F025-05, FR-F025-06: `dashboard` with `csv` and `report` with `png` are both rejected by check constraints.
- `progress_and_attempts_bounded` — FR-F025-12: `progress_pct` 101 and `attempts` 5 violate their checks.
- `claim_scan_uses_pending_index` — NFR-F025-04: `EXPLAIN` on the queued claim over 50,000 rows uses `report_exports(status, created_at) where status in ('queued','running')`.
- `expiry_scan_uses_partial_index` — FR-F025-12: `EXPLAIN` on the nightly sweep uses `report_exports(expires_at) where status = 'completed'`.
- `actor_history_index_used` — FR-F025-07: the export center listing uses `report_exports(tenant_id, requested_by, created_at desc)`.
- `rollback_drops_report_exports` — FR-F025-09: `sqlx migrate revert` removes the table and its three indexes and leaves F010 `export_jobs` untouched.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F025/database/`.
