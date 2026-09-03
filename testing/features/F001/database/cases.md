# F001 database cases

File: `testing/features/F001/database/ci_database_tests.rs`. Flag `F001_FEATURE`.

Only three cases: F001 is a tooling feature that creates no tables or migrations. The lane proves the CI database service and offline SQLx mode that later features' migration tests depend on.

- `ci_postgres18_service_accepts_connections` — FR-F001-10: with `DATABASE_URL` from the `rust` job, `SELECT version()` returns a string starting `PostgreSQL 18`.
- `migrations_dir_exists_and_is_empty` — FR-F001-07: `services/api/migrations/` contains only `.gitkeep`; `cargo xtask check-migrations` prints `migration check passed: no migrations created`.
- `sqlx_offline_build_needs_no_database` — FR-F001-13: with `DATABASE_URL` unset and `SQLX_OFFLINE=true` from `.cargo/config.toml`, `cargo build --workspace` exits 0.

Evidence: connection log and command output under `testing/evidence/F001/database/`.
