# F041 accessibility cases

The surface is a CLI, so accessibility means output that screen readers and tools can consume. File: `testing/features/F041/accessibility/output_tests.rs`. Flag `F041_FEATURE`.

- `no_color_env_disables_ansi` — NFR-F041-03: with `NO_COLOR=1` no byte `0x1b` appears in stderr; without a TTY the same holds.
- `status_never_conveyed_by_color_alone` — NFR-F041-03: every finding line starts with the literal `BLOCKED:` and the summary line contains `passed` or `failed`.
- `lines_never_exceed_200_chars` — NFR-F041-03: a fixture with a 1,000-character offending line produces a finding line ≤ 200 characters ending in `…`.
- `ascii_only_output_by_default` — NFR-F041-03: all stderr/stdout bytes < 0x80 unless the offending source text itself is non-ASCII.
- `json_findings_equal_text_findings` — NFR-F041-03: the set of `(code, path, line)` in JSON equals the parsed text output.

Evidence: captured output under `testing/evidence/F041/accessibility/`.
