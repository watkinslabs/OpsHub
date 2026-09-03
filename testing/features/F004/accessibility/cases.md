# F004 accessibility cases

File: `testing/features/F004/accessibility/operator_output_tests.rs`. No browser UI; these cases verify operator-facing output is usable by screen readers and without colour. Flag `F004_FEATURE`.

- `readyz_json_uses_words_for_state` — NFR-F004-03: `components.*.status` is `ok` or `error` with a `reason` string; no numeric-only or colour-coded state.
- `log_state_words_not_colour` — NFR-F004-03: JSON log lines carry `level` and `status` as words; the human formatter never relies on colour alone.
- `no_color_respected` — NFR-F004-03: `NO_COLOR=1` removes ANSI sequences from `opshub-worker` and `make` output.
- `runbook_heading_hierarchy_and_plain_tables` — NFR-F004-03: `infra/backup/restore.md` has one `#`, ordered `##` steps, and tables with header rows; no images without alt text.
- `cli_help_reads_linearly` — NFR-F004-03: `opshub-worker --help` wraps at 100 columns and lists commands with one-line descriptions.

Evidence: output transcripts and markdown lint reports under `testing/evidence/F004/accessibility/`.
