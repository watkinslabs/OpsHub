# F066 accessibility cases

There is no page to audit with axe; the accessible surface is command output and the runbook an on-call engineer reads at 03:00. File: `testing/features/F066/accessibility/output_a11y_tests.rs`. Flag `F066_FEATURE`.

- `output_is_ascii_only` — NFR-F066-03: every byte of the static and budget output on all fixtures is ASCII, so a screen reader and a plain terminal render it identically.
- `no_color_is_honoured` — NFR-F066-03: `NO_COLOR=1` removes all escape sequences from both modes; the exit code and the words are unchanged.
- `state_is_never_colour_only` — NFR-F066-03: `ok`, `guarded`, `exhausted`, and `insufficient_data` appear as words in their own column, and `REFUSED:` and `BLOCKED:` prefixes carry the meaning without styling.
- `no_line_exceeds_200_characters` — NFR-F066-03: the widest finding message and the widest report row stay within the limit on every fixture.
- `json_is_a_structural_equivalent` — NFR-F066-03: every fact in the text output — objective, target, ratio, remaining minutes, state, exceptions, findings — is present in the `--json` object, so a tool or reader that cannot parse the table loses nothing.
- `runbook_headings_are_hierarchical_and_anchored` — NFR-F066-03, FR-F066-11: `infra/slo/runbook.md` has one heading level per section, one anchor per alert severity, and every generated alert's `runbook` annotation resolves to an existing anchor.
- `runbook_tables_are_plain_text` — NFR-F066-03: the burn-rate and policy tables use header rows and separators only, with no nested markup, and read in order.
- `findings_name_the_file_and_line` — NFR-F066-03: each `BLOCKED:` line carries a path and line so the reader can navigate without visual scanning of a diff.

Evidence: captured output bytes, the `NO_COLOR` comparison, and the runbook anchor list under `testing/evidence/F066/accessibility/`.
