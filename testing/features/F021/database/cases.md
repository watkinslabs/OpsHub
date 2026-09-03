# F021 database cases

File: `testing/features/F021/database/migration_tests.rs`. Flag `F021_FEATURE`.

- `reports_tables_exist_with_constraints` — T081: `reports`, `report_sources`, `report_filters`, `report_snapshots`, `report_snapshot_rows` exist with tenant, version, audit, and soft-delete columns; `aggregate_policy` check constraint.
- `duplicate_report_name_same_folder_rejected` — FR-F021-01: partial unique index blocks case-insensitive duplicate while `deleted_at is null`.
- `source_alias_unique_per_report` — FR-F021-02: second `report_sources` row with alias `projects` for the same report violates `(report_id, alias)`.
- `second_active_snapshot_rejected` — FR-F021-07: inserting a second `queued` snapshot for one report violates `report_snapshots_active_idx`.
- `snapshot_rows_ordered_by_seq` — FR-F021-09: `(snapshot_id, seq)` primary key; page query uses the index per `EXPLAIN`.
- `source_sheet_index_used_for_stale_fanout` — FR-F021-13: `EXPLAIN` on "reports referencing sheet X" uses `report_sources_sheet_id_idx`.
- `snapshot_and_outbox_rows_written_in_transaction` — FR-F021-14: failing outbox insert rolls back the report write.
- `retention_prunes_to_three_succeeded` — FR-F021-07: prune query deletes oldest snapshot rows in batches of 10,000.
- `rollback_drops_report_tables` — T081: `sqlx migrate revert` removes the five tables and indexes.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F021/database/`.
