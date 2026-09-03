# F004 frontend cases

No UI: covered by `api/` and `e2e/`. This lane holds CLI and compose output tests in `testing/features/F004/frontend/cli_tests.rs`. Flag `F004_FEATURE`.

- `compose_ps_json_reports_eight_healthy` — FR-F004-01: `docker compose ps --format json` parses to eight entries with `Health = "healthy"`.
- `config_missing_var_exits_78_without_value` — FR-F004-02: unset `OPSHUB_DATABASE_URL` → exit 78; stderr contains the variable name and no URL fragment.
- `env_example_covers_every_config_field` — FR-F004-02: every `RuntimeConfig` field has a matching commented line in `.env.example`.
- `image_version_flag_prints_crate_version` — FR-F004-04: `docker run --rm opshub/api --version` prints the `Cargo.toml` version.
- `worker_replay_cli_output_and_exit_codes` — FR-F004-11: `replay --id` prints the new run id; second call prints `already replayed` and exits 65.
- `worker_dead_letters_lists_or_empty` — FR-F004-11: with none → `No dead letters`; with two → a plain-text table with id, kind, attempts, dead_at.
- `enqueue_sample_then_metrics_show_success` — FR-F004-13: `enqueue-sample` then scrape shows `job_runs_total{kind="sample",status="succeeded"} 1`.
- `cli_honours_no_color` — NFR-F004-03: `NO_COLOR=1` output contains no ANSI escapes; state shown as `ok` / `error`.

Evidence: CLI transcripts under `testing/evidence/F004/frontend/`.
