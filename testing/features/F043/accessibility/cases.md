# F043 accessibility cases

The surface is a CLI whose output is meant to be `eval`ed and read by people and tools. File: `testing/features/F043/accessibility/output_tests.rs`. Flag `F043_FEATURE`.

- `export_lines_eval_safe_with_spaces_and_quotes` — NFR-F043-03: branch `t900-it's a test` → `eval` in sh, bash, and zsh yields the exact values.
- `no_color_and_ascii_only` — NFR-F043-03: no `0x1b` bytes; all output < 0x80.
- `refusals_readable_without_color` — NFR-F043-03: `REFUSED:` prefix and full sentence naming the id and reason.
- `json_equivalent_for_every_command` — NFR-F043-03: `--json` on all five commands parses and carries the same values as text mode.

Evidence: captured output under `testing/evidence/F043/accessibility/`.
