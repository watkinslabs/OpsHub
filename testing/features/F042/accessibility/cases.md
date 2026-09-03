# F042 accessibility cases

The surface is a CLI, so accessibility means masked, plain output that people and tools can read safely. File: `testing/features/F042/accessibility/output_tests.rs`. Flag `F042_FEATURE`.

- `findings_never_contain_token` — FR-F042-14, NFR-F042-03: every failing case's stdout and stderr grepped for every generated token → no match.
- `no_color_disables_ansi` — NFR-F042-03: `NO_COLOR=1` or non-TTY → no `0x1b` bytes.
- `blocked_prefix_and_plain_summary` — NFR-F042-03: each finding starts with `BLOCKED:`; summary says `passed` or `failed`.
- `context_line_truncated_to_200_chars` — NFR-F042-03: a 5,000-character staged line yields a finding line ≤ 200 characters.
- `author_email_masked_in_output` — NFR-F042-02: range finding shows `f***@example.test`, never the full address.

Evidence: captured output under `testing/evidence/F042/accessibility/`.
