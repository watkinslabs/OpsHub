# F067 accessibility cases

F067 has no UI, so axe does not apply. The equivalent obligation for a command-line gate is that its result is legible without color, without a terminal, and without a human reading prose: machine-readable output, verdict words, distinct exit codes, and a plain-Markdown report.

File: `testing/features/F067/accessibility/{output_tests.rs,report_semantics_tests.rs}`. Flag `F067_FEATURE`. Fixtures: recorded run directories, a non-TTY and a `NO_COLOR` environment.

- `json_mode_emits_only_the_result_document` — NFR-F067-05: `--json` writes valid JSON on stdout and nothing else; progress and warnings go to stderr.
- `verdict_words_present_without_color` — NFR-F067-05: under `NO_COLOR` and a non-TTY the output still contains `pass`, `fail`, `skip`, or `regressed` as words, never color or a symbol alone.
- `exit_codes_distinguish_outcomes_without_text` — NFR-F067-05: a caller that reads only the exit status separates pass or skip (0), fail or regressed or aborted (1), input and collection errors (2), and role refusal (3).
- `skip_line_states_the_reason_in_words` — FR-F067-11: the skip line names the reason code and the human sentence, so a scrollback with no color still explains why nothing ran.
- `report_md_uses_heading_structure_and_table_headers` — FR-F067-16: the six sections are real Markdown headings in order and the metric tables use header rows rather than bolded first rows.
- `metric_ids_wrap_rather_than_truncate` — NFR-F067-05: at 80 columns the metric table wraps; no metric id is elided, so no verdict becomes unreadable.
- `token_never_printed_to_terminal_or_report` — NFR-F067-03: `LOAD_ENV_TOKEN` appears in no line of stdout, stderr, `commands.log`, or `report.md`.

Evidence: captured stdout, stderr, exit codes, and rendered reports under `testing/evidence/F067/accessibility/`.
