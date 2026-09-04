---
id: T265
type: task
status: planned
parent_epic: E000
parent_feature: F067
parent_story: S133
depends_on: [S133]
owned_paths: [automation/xtask/src/load/**, testing/load/datasets/**, testing/load/seed/**, testing/evidence/F067/**, testing/features/F067/database/**, testing/features/F067/performance/**]
feature_flag: F067_FEATURE
branch: t265-seed-generator
started_at: null
finished_at: null
---

# T265 — Seed generator

## Identity

- Parent story: `S133` Load profiles and seeds
- Owner: platform
- Branch: `t265-seed-generator`
- Decision references: `docs/architecture-decisions.md` sections 1, 2, 9; `docs/capability-contracts.md` row F067

## Objective

Build the deterministic composite dataset generator behind `cargo xtask load-test seed`: dataset declarations, a seeded value stream, repository-backed loading, the dataset manifest, the archive cache with restore, and `--verify`.

## Specification

- Owned paths: `automation/xtask/src/load/{dataset.rs, seed.rs}` plus the shared `mod.rs` entry, `testing/load/datasets/{smoke.toml, tier1.toml, full.toml}`, `testing/load/seed/{plan.toml, words.txt, cache/}`, `testing/evidence/F067/datasets/`
- Contract/input: `cargo xtask load-test seed --dataset <smoke|tier1|full> --seed <u64> [--verify] [--rebuild]`; environment `LOAD_ENV_URL`, `LOAD_ENV_TOKEN`; `Dataset { name, tenants, users, max_dimension_sheets, typical_sheets, rows_per_sheet, columns_per_sheet, cell_density, expected_counts }` parsed from the dataset TOML.
- Output/behavior: `smoke` builds 10 tenants, 1,000 users, one 5,000-row × 50-column sheet and 50 typical sheets; `tier1` builds 1,000 tenants, 100,000 users, one 100,000-row × 500-column sheet at 30% cell density and 200 typical sheets of 2,000 rows × 30 columns at 80% density; `full` builds 10,000 tenants, 1,000,000 users, 10 max-dimension sheets and 2,000 typical sheets, landing about 4 million rows and 250 million cells. Values come from a ChaCha20 stream keyed by `(seed, table_ordinal, tenant_ordinal)`; UUIDv7 ids use the fixed base `2026-01-01T00:00:00Z` plus the row ordinal; rows are written through the owning `crates/persistence` repositories — `TenantRepository`, `UserRepository`, `GroupRepository`, `SheetRepository`, `RowRepository`, `CellRepository` — in dependency order, one `UnitOfWork` per tenant batch of 100 across 8 connections, so `seed.rs` holds no SQL string, `sqlx::query*` call, or connection of its own (decision 2.1) and no table gains a second writer; `session_replication_role = replica` during the load and the closing foreign-key validation, index build, and `VACUUM (ANALYZE)` are steps of the environment provisioning script. Seed-time settings `maintenance_work_mem = 2GB`, `max_wal_size = 32GB`, `checkpoint_timeout = 30min`, `autovacuum = off` are applied and reverted by that provisioning script, and the steady-state settings under measurement (`max_connections = 400`, `shared_buffers = 16GB`, `work_mem = 32MB`, `checkpoint_timeout = 5min`) are read back and recorded by the generator in the manifest. Budgets `smoke` < 90 s, `tier1` < 25 min, `full` < 4 h are hard timeouts exiting 2 with `dataset.timeout`; a produced count differing from the declaration exits 2 with `dataset.count_mismatch`. On success the generator writes `testing/evidence/F067/datasets/<dataset>-<seed>.json` with counts, per-table crc32c checksums, `generator_sha256`, `postgres_version`, and `duration_s`, and caches `pg_dump -Fc` under `testing/load/seed/cache/<dataset>-<seed>.manifest` so a repeat restores `tier1` in under 12 min. `--verify` re-derives checksums from a 1% seeded sample and exits 2 with `dataset.drift`; `--rebuild` ignores the cache. Generated addresses use `@load.invalid` and names come from `testing/load/seed/words.txt`; a `LOAD_ENV_URL` host in the production allowlist refuses to start.
- Dependencies: F002 `tenants`, `users`, `groups`, `group_members` and F006 `sheets`, `rows`, `cells` schemas exist on the load environment; no migration is owned here.
- Feature flag: `F067_FEATURE` gates the `load-test` subcommand; the generator never touches a non-load environment.

## TDD

- Failing test first: `testing/features/F067/database/seed_tests.rs::seed_is_deterministic_for_same_value`, `::seed_differs_for_different_value`, `::dataset_counts_match_declaration`, `::repository_load_preserves_cell_density`, `::foreign_keys_valid_after_load`, `::seed_cache_restore_matches_fresh_build`, `::verify_detects_mutated_table`, `::production_host_refused`; `testing/features/F067/database/manifest_tests.rs::manifest_records_counts_checksums_and_generator_sha`; `testing/features/F067/performance/seed_budget_tests.rs::smoke_seed_under_ninety_seconds`, `::budget_overrun_exits_dataset_timeout`
- Targeted command: `cargo xtask test-feature F067`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/load.rs` throwaway PostgreSQL 18 database per worker, a scaled-down `smoke` variant for budget tests, a mutated-table fixture for `--verify`, and a fake production allowlist

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] `smoke`, `tier1`, and `full` each built once with a committed manifest under `testing/evidence/F067/datasets/`
- [ ] Determinism reproduced on a second machine and PostgreSQL 18 patch version
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S133
- [ ] `finished_at` recorded
