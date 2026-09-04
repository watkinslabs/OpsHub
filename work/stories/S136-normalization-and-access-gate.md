---
id: S136
type: story
status: planned
parent_epic: E001
parent_feature: F068
depends_on: [F001]
owned_paths: [automation/xtask/src/persistence.rs, crates/persistence/schema-policy.toml, testing/fixtures/persistence/**, testing/features/F068/requirements/**, testing/features/F068/frontend/**, testing/features/F068/e2e/**, testing/features/F068/accessibility/**, testing/features/F068/performance/**]
feature_flag: F068_FEATURE
branch: s136-normalization-and-access-gate
started_at: null
finished_at: null
---

# S136 — Normalization and access gate

## Identity

- Parent feature: `F068` Persistence layer and data access classes
- Owner: platform
- Branch: `s136-normalization-and-access-gate`
- Decision references: `docs/architecture-decisions.md` section 2 (normalization, arrays, `jsonb` allow-list) and section 2.1 (one class per table, no SQL outside the crate); `docs/capability-contracts.md` row F068 (module `persistence`, surface `cargo xtask check-persistence`)

## Vertical slice

As a platform maintainer, I want `cargo xtask check-persistence` to fail the build when SQL, a pool, or a connection type appears outside `crates/persistence/**`, when a catalog table has no repository or two, when a migration declares an array column, or when a `jsonb` column is missing from the allow-list, so that decisions 2 and 2.1 are enforced by the build on every branch instead of by a reviewer reading a diff.

## Requirements

- **SR-S136-01:** `persist.raw_sql` reports any `sqlx::query`, `query!`, `query_as`, `query_scalar`, or `query_file` call and any SQL string literal matching the `select`, `insert into`, `update ... set`, `delete from`, `create table`, `alter table`, or `with ... as` pattern outside `crates/persistence/src/**` and `services/api/migrations/**` (FR-F068-14).
- **SR-S136-02:** `persist.connection_type` reports `PgPool`, `PgPoolOptions`, `PgConnection`, `PgRow`, `PgArguments`, `sqlx::Transaction`, `sqlx::Executor`, and `sqlx::Acquire` outside `crates/persistence/**`, and reports any of them re-exported from `crates/persistence/src/lib.rs`; `persist.escape_hatch` reports a `pub fn` named `query`, `execute`, `exec`, `raw`, or `sql`, or one taking a `&str` parameter named `sql` (FR-F068-14, FR-F068-13).
- **SR-S136-03:** `persist.table_unmapped` and `persist.table_double_write` compare the `Tables` and `Persistence` columns of `docs/capability-contracts.md` against the `TABLE` and `CO_TABLES` constants found in the crate: a catalog table with no specification and a table claimed by two specifications are both findings, so one class per table is checked rather than assumed (FR-F068-14, NFR-F068-05).
- **SR-S136-04:** `persist.array_column` reports any array type declared by a `create table` or `alter table ... add column` in `services/api/migrations/**`, naming the owning feature; `persist.jsonb_unlisted` reports any `jsonb` column absent from `crates/persistence/schema-policy.toml`, and `persist.policy_stale` reports an entry whose column no longer exists (FR-F068-14, FR-F068-15).
- **SR-S136-05:** `crates/persistence/schema-policy.toml` ships with exactly the eleven columns decision section 2 permits across its five categories — typed cell values, view and widget settings, event payloads, provider response snapshots, and diffs — each with its category, owning feature, and reason; the F029 array columns are reported rather than exempted (FR-F068-15).
- **SR-S136-06:** Output follows the F041 rules: sorted `BLOCKED: <code> <path>:<line>: <message>` lines on stderr, a single summary line or a single `--json` object on stdout, exit 0 with no findings, 1 with findings, 2 for usage or I/O errors, and 3 with `REFUSED: persist.baseline_widened` when a run adds a finding the baseline does not record or `--write-baseline` runs without `XTASK_ROLE=maintainer` (FR-F068-16).
- **SR-S136-07:** Every static rule is proved without a database over fixture trees in `testing/fixtures/persistence/`, and the rules that need one run against a throwaway PostgreSQL 18; the gate itself opens no connection, which is asserted with `OPSHUB_DATABASE_URL` unset and a loopback listener that fails the test on any accepted connection (FR-F068-14, NFR-F068-02).
- **SR-S136-08:** The gate completes in under 2 seconds over the whole repository, reads each file once, streams files over 1 MiB, produces byte-identical output on two runs of an unchanged tree, and its output is ASCII, honours `NO_COLOR`, and stays within 200 columns (NFR-F068-01, NFR-F068-03, NFR-F068-04).
- **SR-S136-09:** `crates/persistence/README.md` documents the four-step recipe for adding a repository, the fixed statement shapes, the `automation/xtask/src/main.rs` dispatch line, and the `.github/workflows/gates.yml` step verbatim, so the two edits in files this feature does not own are mechanical (FR-F068-16, NFR-F068-03).

## Surfaces

- Rust gate: `automation/xtask/src/persistence.rs` with `check_persistence`, `scan_sources`, `scan_migrations`, `scan_specs`, `catalog_tables`, `Policy`, and `Baseline`, reusing F041's `support::{OutputFormat, report}` reporter
- Policy data: `crates/persistence/schema-policy.toml` listing the permitted `jsonb` columns with category, owning feature, and reason
- Integration points not owned here: the one-line dispatch arm in `automation/xtask/src/main.rs` (F041) and the gate step in `.github/workflows/gates.yml` (F001), both recorded verbatim in `crates/persistence/README.md`
- Fixtures: `testing/fixtures/persistence/trees/{clean,raw_sql,connection_leak,escape_hatch,double_write,unmapped_table}/`, `migrations/{arrays,jsonb_listed,jsonb_unlisted,stale_policy}/*.sql`, `catalog/{matching,missing_table}.md`, `baseline.json`
- Harness lanes owned here: `testing/features/F068/{requirements,frontend,e2e,accessibility,performance}/`

## TDD harness

- Test path: `testing/features/F068/{requirements,frontend,e2e,accessibility,performance}/`
- Feature flag: `F068_FEATURE`
- Targeted command: `cargo xtask test-feature F068`
- Full command: `cargo xtask test-all`
- First failing tests: `sql_literal_in_handler_is_raw_sql`, `pool_type_outside_crate_is_connection_type`, `catalog_table_without_spec_is_unmapped`, `two_specs_on_one_table_is_double_write`, `array_column_in_migration_is_reported_with_owning_feature`, `jsonb_column_absent_from_policy_is_unlisted`, `baseline_widening_refuses_with_exit_three`, `gate_opens_no_database_connection`

## Exit criteria

- [ ] Requirement tests SR-S136-01 through SR-S136-09 written first and observed failing
- [ ] Tasks T271 and T272 complete, with the gate dispatched from `main.rs` and running in `gates.yml`
- [ ] `cargo xtask check-persistence` exits 0 over the repository with the S135 crate in place, and exits 1 on each fixture tree with the expected code, path, and line
- [ ] Static lanes run with no Docker; the database lane runs against `postgres:18` per session with one database per worker
- [ ] All files ≤ 500 lines; handoff evidence recorded in the F068 ticket
