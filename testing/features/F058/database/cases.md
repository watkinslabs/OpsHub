# F058 database cases

File: `testing/features/F058/database/migration_tests.rs`. Flag `F058_FEATURE`.

- `mobile_tables_exist_with_constraints` — T229: `mobile_devices`, `mobile_sync_batches`, `mobile_sync_applied_ops`, `mobile_sync_rejections` exist with tenant, version, and audit columns.
- `duplicate_batch_id_rejected` — FR-F058-06: second `(device_id, batch_id)` violates the unique index.
- `duplicate_applied_op_rejected` — FR-F058-06: second `(device_id, client_op_id)` in `mobile_sync_applied_ops` rejected.
- `second_active_device_per_session_rejected` — FR-F058-02: two unrevoked devices for one `(user_id, session_id)` violate the partial unique index.
- `platform_check_constraint` — FR-F058-02: `platform = 'windows'` rejected.
- `batch_count_check_constraint` — FR-F058-04: `applied_count + rejected_count = 501` rejected.
- `rejection_index_used_for_queue_page` — NFR-F058-01: `EXPLAIN` on rejections by device uses `(device_id, created_at desc)`.
- `applied_ops_and_audit_in_one_transaction` — FR-F058-13: failing audit insert rolls back the applied op record and cell write.
- `rollback_drops_tables` — T229: `sqlx migrate revert` removes the four tables and indexes.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F058/database/`.
