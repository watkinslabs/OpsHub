# F001 api cases

File: `testing/features/F001/api/{workspace_tests.rs,workflow_tests.rs,gate_tests.rs}`. No HTTP routes; the "api" lane exercises the command-line and workflow contract. Flag `F001_FEATURE`.

- `workspace_members_match_contract` — FR-F001-02: parsed root `Cargo.toml` lists exactly the ten members with `edition = "2024"` and `lints.workspace = true`.
- `cargo_build_workspace_exits_zero` — FR-F001-01: `cargo build --workspace` in the fixture clone exits 0 and `target/debug/{api,worker,realtime,mcp,xtask}` exist.
- `clippy_warning_fails_build` — FR-F001-03: adding `let unused = 1;` to `crates/domain/src/lib.rs` makes `cargo clippy -- -D warnings` exit 1; reverting exits 0.
- `web_build_writes_index_html` — FR-F001-04: `pnpm --filter web build` exits 0 and `apps/web/dist/index.html` exists.
- `target_dir_override_isolates_lanes` — FR-F001-13: two builds with `CARGO_TARGET_DIR=.agent-target/a` and `/b` create both dirs and share nothing.
- `gates_workflow_declares_five_required_jobs` — FR-F001-06: `gates.yml` parses with jobs `validate-work`, `rust`, `web`, `policy`, `line-limit`.
- `validate_work_job_runs_commands_in_order` — FR-F001-07: step commands are `validate-work`, `validate-plan`, `validate-tickets`, `check-contracts`, `check-migrations` in order; invalid ticket fixture fails with `BLOCKED:`.
- `rust_job_uses_postgres18_and_nats_services` — FR-F001-10: services `postgres:18` and `nats:2.11`; env `DATABASE_URL`, `NATS_URL`; artifact `rust-junit`.
- `web_job_runs_lint_typecheck_test_build` — FR-F001-11: step order lint, typecheck, test with junit reporter, build; artifact `web-build`.
- `docs_only_change_skips_matrix_but_not_policy` — FR-F001-12: docs-only diff sets `docs_only=true`; `rust` and `web` skipped, `validate-work`, `policy`, `line-limit` run.
- `policy_job_blocks_attribution_token` — FR-F001-08: poisoned commit body → `audit-range` output starts `BLOCKED:` and job exits 1.
- `policy_job_passes_clean_history` — FR-F001-08: clean fixture history → `self-test`, `audit-range`, `audit-pr` all exit 0.
- `line_limit_job_blocks_501_lines` — FR-F001-09: 501-line file → output `<path>: 501 lines; limit is 500`, exit 1.
- `line_limit_job_allows_500_lines` — FR-F001-09: 500-line file → exit 0.
- `workflow_pins_actions_and_read_permissions` — NFR-F001-02: every `uses:` has a 40-hex SHA; top-level `permissions.contents == read`; `cargo deny check advisories` present.
- `job_rerun_is_idempotent` — NFR-F001-04: running `line-limit` twice yields identical output; no `retry` or `continue-on-error` keys in the workflow.

Evidence: command transcripts and parsed workflow JSON under `testing/evidence/F001/api/`.
