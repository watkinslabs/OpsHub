---
id: T271
type: task
status: planned
parent_epic: E001
parent_feature: F068
parent_story: S136
depends_on: [S136]
owned_paths: [automation/xtask/src/persistence.rs, crates/persistence/schema-policy.toml, testing/fixtures/persistence/**]
feature_flag: F068_FEATURE
branch: t271-check-persistence-gate
started_at: null
finished_at: null
---

# T271 — check-persistence gate

## Identity

- Parent story: `S136` Normalization and access gate
- Owner: platform
- Branch: `t271-check-persistence-gate`
- Decision references: `docs/architecture-decisions.md` section 2 (no array column, `jsonb` only for schema-less payloads) and section 2.1 (all SQL in `crates/persistence`, one class per table); `docs/capability-contracts.md` row F068 (module `persistence`, surface `cargo xtask check-persistence`)

## Objective

Implement `cargo xtask check-persistence` with its six rules, the `jsonb` allow-list, the baseline, and the F041 output and exit-code contract, plus the fixture trees that prove each rule without a database.

## Specification

- Owned paths: `automation/xtask/src/persistence.rs`, `crates/persistence/schema-policy.toml`, `testing/fixtures/persistence/**`
- Module shape: `check_persistence(args)`, `scan_sources`, `scan_migrations`, `scan_specs`, `catalog_tables`, `Policy` (serde model of `schema-policy.toml`), `Baseline`; reuses F041's `support::{OutputFormat, report}` and adds no dependency beyond `toml`
- Rule `persist.raw_sql`: outside `crates/persistence/src/**` and `services/api/migrations/**`, flag `sqlx::query`, `query!`, `query_as`, `query_scalar`, `query_file`, and any string literal matching `(?is)\b(select\s|insert\s+into|update\s+\w+\s+set|delete\s+from|create\s+table|alter\s+table|with\s+\w+\s+as)\b`
- Rule `persist.connection_type`: flag `PgPool`, `PgPoolOptions`, `PgConnection`, `PgRow`, `PgArguments`, `sqlx::Transaction`, `sqlx::Executor`, `sqlx::Acquire` outside `crates/persistence/**`, and any of them re-exported from `crates/persistence/src/lib.rs`
- Rule `persist.escape_hatch`: flag a `pub fn` in the crate named `query`, `execute`, `exec`, `raw`, or `sql`, or one taking a `&str` parameter named `sql`
- Rules `persist.table_unmapped` and `persist.table_double_write`: build the table inventory from the `Tables` and `Persistence` columns of `docs/capability-contracts.md`, build the specification inventory from `TABLE` and `CO_TABLES` constants in the crate, and require exactly one specification per table
- Rules `persist.array_column`, `persist.jsonb_unlisted`, `persist.policy_stale`: parse `create table` and `alter table ... add column` in `services/api/migrations/**`; any array type is a finding naming the owning feature; any `jsonb` column absent from `schema-policy.toml` is a finding; any policy entry whose column no longer exists is a finding
- Policy file: `crates/persistence/schema-policy.toml` ships `cells.value`, `tenants.settings`, `views.config`, `sheet_user_layouts.layout`, `outbox_events.payload`, `notifications.payload`, `workflow_run_steps.payload`, `integration_connections.last_error`, `integration_events.detail`, `audit_events.before`, `audit_events.after`, and `audit_events.field_diff`, each with category, owning feature, and reason; F029's `capabilities`, `scopes`, `missing_scopes`, and `granted_scopes` array columns are reported, not exempted
- Output: sorted `BLOCKED: <code> <path>:<line>: <message>` on stderr; `check-persistence passed (<n> items)` and exit 0; `check-persistence failed: <n> findings` and exit 1; usage or I/O error and exit 2; `REFUSED: persist.baseline_widened` and exit 3 when a run adds a finding the baseline does not record or `--write-baseline` runs without `XTASK_ROLE=maintainer`; `--json` prints one object `{ command, ok, checked, findings, duration_ms }`; ASCII, `NO_COLOR`, 200-column limit
- Integration points not owned here: the dispatch arm `Some("check-persistence") => persistence::check_persistence(args)` in `automation/xtask/src/main.rs` (F041) and the gate step in `.github/workflows/gates.yml` (F001), both recorded verbatim in `crates/persistence/README.md`
- Dependencies: F041's reporter, output rules, and exit codes; `docs/capability-contracts.md` as the table inventory; T269's specification constants as the class inventory
- Feature flag: `F068_FEATURE` gates the harness lane; the gate itself always runs in CI

## TDD

- Failing test first: `testing/features/F068/e2e/gate_e2e.rs::clean_tree_passes_with_exit_zero`, `::sql_literal_in_handler_is_raw_sql`, `::sqlx_query_macro_outside_crate_is_raw_sql`, `::pool_type_outside_crate_is_connection_type`, `::lib_reexporting_pgpool_is_connection_type`, `::pub_fn_named_query_is_escape_hatch`, `::catalog_table_without_spec_is_unmapped`, `::two_specs_on_one_table_is_double_write`, `::array_column_in_migration_is_reported_with_owning_feature`, `::jsonb_column_absent_from_policy_is_unlisted`, `::stale_policy_entry_is_reported`, `::baseline_widening_refuses_with_exit_three`, `::unknown_flag_exits_two`; `testing/features/F068/frontend/output_tests.rs::findings_sorted_by_path_line_code`, `::json_object_shape_matches_contract`
- Targeted command: `cargo xtask test-feature F068`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/persistence/trees/{clean,raw_sql,connection_leak,escape_hatch,double_write,unmapped_table}/` copied into a temporary directory per case; `migrations/{arrays,jsonb_listed,jsonb_unlisted,stale_policy}/*.sql`; `catalog/{matching,missing_table}.md`; `baseline.json`; no database and no network in any case

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Every rule fires on its fixture tree with the expected code, path, and line, and the clean tree exits 0
- [ ] Gate runs over the real repository in under 2 seconds and produces byte-identical output on two runs
- [ ] Owned-path check passes; every file ≤ 500 lines; lint and format gates pass
- [ ] Handoff evidence recorded in S136
- [ ] `finished_at` recorded
