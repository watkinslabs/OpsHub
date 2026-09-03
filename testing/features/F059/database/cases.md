# F059 database cases

File: `testing/features/F059/database/migration_tests.rs`. Flag `F059_FEATURE`.

- `publishing_tables_exist_with_constraints` — T233: `publications`, `publication_tokens`, `publication_views` exist with tenant, version, and audit columns.
- `expiry_beyond_30_days_rejected` — FR-F059-01: check constraint rejects `expires_at > created_at + 30 days`.
- `second_active_publication_same_target_rejected` — FR-F059-01: partial unique index blocks a second active `(target, access)`.
- `duplicate_token_hash_rejected` — FR-F059-02: unique `token_hash` index.
- `one_current_token_per_publication` — FR-F059-02: second token with `superseded_at is null` rejected.
- `refresh_interval_check_constraint` — FR-F059-01: `refresh_interval_s = 30` rejected.
- `views_index_used_for_counts` — FR-F059-11: `EXPLAIN` on `view_count_7d` uses `(publication_id, viewed_at desc)`.
- `token_table_has_no_plaintext_column` — NFR-F059-02: schema inspection finds only `token_hash bytea`.
- `rollback_drops_tables` — T233: `sqlx migrate revert` removes the three tables and indexes.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F059/database/`.
