# F067 database cases

F067 owns no table and adds no migration. This lane tests the seed generator against a throwaway PostgreSQL 18 database using tables other features own, and holds the negative control proving no migration was added.

File: `testing/features/F067/database/{seed_tests.rs,manifest_tests.rs,cache_tests.rs,no_migration_tests.rs}`. Flag `F067_FEATURE`. Fixture: one throwaway database per test worker, fixed seed `42`.

- `seed_is_deterministic_for_same_value` — FR-F067-04: two `smoke` builds at seed 42 produce identical crc32c per table across two machines.
- `seed_differs_for_different_value` — FR-F067-04: seed 43 changes every table checksum, so a seed collision cannot go unnoticed.
- `uuidv7_ids_derive_from_fixed_base` — FR-F067-04: ids derive from `2026-01-01T00:00:00Z` plus the row ordinal and repeat exactly on a rebuild.
- `dataset_counts_match_declaration` — FR-F067-03: `smoke` yields exactly 10 tenants, 1,000 users, 1 sheet of 5,000 rows × 50 columns, and 50 typical sheets; one row short → exit 2 `dataset.count_mismatch`.
- `tier1_max_dimension_sheet_is_full_width` — FR-F067-03: the `tier1` max-dimension sheet holds 100,000 rows and 500 columns, proving the per-sheet half of the spec section 6 target.
- `copy_load_preserves_cell_density` — FR-F067-03: 30% density on the max-dimension sheet and 80% on typical sheets within ±0.5 points, so the sparse `cells` layout is exercised.
- `foreign_keys_valid_after_load` — FR-F067-04: `session_replication_role = replica` during load, then every constraint validates and `VACUUM (ANALYZE)` runs on each touched table.
- `load_settings_applied_and_reverted` — FR-F067-04: `maintenance_work_mem`, `max_wal_size`, `checkpoint_timeout`, and `autovacuum` return to the measured steady-state values recorded in `environment.json`.
- `manifest_records_counts_checksums_and_generator_sha` — FR-F067-05: the dataset manifest carries counts, crc32c per table, `generator_sha256`, `postgres_version`, and `duration_s`.
- `seed_cache_restore_matches_fresh_build` — FR-F067-05: the `pg_dump -Fc` restore reproduces every table checksum of the original build.
- `verify_detects_mutated_table` — FR-F067-05: a single mutated cell is caught by the 1% seeded sample → exit 2 `dataset.drift`.
- `rebuild_ignores_cache` — FR-F067-05: `--rebuild` regenerates and rewrites the manifest even when a cache entry exists.
- `synthetic_addresses_only` — NFR-F067-03: every generated address ends in `@load.invalid` and every name comes from the checked-in word list.
- `production_host_refused` — NFR-F067-03: a `LOAD_ENV_URL` in the production allowlist exits 2 before opening a connection.
- `no_load_migration_added` — FR-F067-03: negative control — `services/api/migrations/` contains no `*_load_*.sql` file and F067 claims no migration glob.

Evidence: JUnit output, table checksum dumps, and generator timing logs under `testing/evidence/F067/database/`.
