# F031 database cases

File: `testing/features/F031/database/migration_tests.rs`. Flag `F031_FEATURE`.

- `portfolio_tables_exist_with_constraints` — T121: `portfolios`, `portfolio_projects`, `portfolio_rollups` exist with tenant, version, audit, and soft-delete columns.
- `duplicate_portfolio_name_rejected` — FR-F031-01: unique partial index blocks case-insensitive duplicate per workspace while `deleted_at is null`; allows after delete.
- `refresh_policy_check_rejects_unknown_value` — FR-F031-01: `refresh_policy = 'hourly'` violates the check constraint; `stale_after_seconds = 30` violates the range check.
- `membership_requires_existing_sheet` — FR-F031-04: foreign key rejects an unknown `project_sheet_id`; `on delete restrict` blocks hard delete of a member sheet.
- `membership_primary_key_prevents_duplicates` — FR-F031-04: inserting the same `(portfolio_id, project_sheet_id)` twice is rejected.
- `snapshot_unique_per_requested_version` — FR-F031-08: second snapshot with the same `(portfolio_id, requested_version)` is rejected.
- `snapshot_prune_keeps_three` — FR-F031-08: after five refreshes only the three newest `portfolio_rollups` rows remain.
- `rollup_index_used_for_latest_read` — NFR-F031-01: `EXPLAIN` on the latest-snapshot query uses `portfolio_rollups_portfolio_computed_idx`.
- `audit_and_outbox_rows_written_in_transaction` — FR-F031-11: failing outbox insert rolls back the membership write.
- `rollback_drops_tables` — T121: `sqlx migrate revert` removes the three tables and indexes.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F031/database/`.
