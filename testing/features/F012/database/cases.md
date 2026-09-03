# F012 database cases

File: `testing/features/F012/database/migration_tests.rs`. Flag `F012_FEATURE`.

- `dependency_tables_exist_with_constraints` — T045: `row_dependencies` and `schedule_results` exist with tenant, version, audit columns, and `(sheet_id, row_id)` primary key.
- `duplicate_pair_rejected_by_index` — FR-F012-04: second `(tenant_id, predecessor_row_id, successor_row_id)` violates `row_dependencies_pair_idx`.
- `invalid_kind_rejected` — FR-F012-01: `kind = 'XX'` or `lag_unit = 'weeks'` fails the check constraint.
- `self_link_rejected_by_check` — FR-F012-02: equal predecessor and successor violates the table check.
- `dependency_requires_existing_rows_and_sheet` — FR-F012-02: foreign keys reject orphan row ids; `on delete restrict` blocks hard delete of a linked row.
- `schedule_results_cascade_on_row_purge` — FR-F012-08: purging a row removes its `schedule_results` entry.
- `side_indexes_used_for_graph_load` — NFR-F012-01: `EXPLAIN` on predecessor and successor lookups uses `row_dependencies_sheet_pred_idx` / `_succ_idx`.
- `shift_transaction_rolls_back_on_outbox_failure` — FR-F012-12: failing outbox insert reverts all cell updates and the audit row.
- `rollback_drops_tables` — T045: `sqlx migrate revert` removes both tables and indexes.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F012/database/`.
