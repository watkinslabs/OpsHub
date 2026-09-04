# F066 frontend cases

F066 ships no React component and no client. Its rendered surface is the budget report, which must appear identically as a plain-text table and as JSON under the F041 output rules, so this lane tests that rendering and holds the control that `apps/web/` stays untouched. File: `testing/features/F066/frontend/report_render_tests.rs`. Flag `F066_FEATURE`.

- `text_and_json_report_carry_the_same_fields` — FR-F066-14, NFR-F066-03: every column of the `objective | target | 28d ratio | remaining | state` table has a matching key in the `--json` object, and every objective in the JSON appears in the table.
- `no_color_output_has_no_escape_sequences` — NFR-F066-03: with `NO_COLOR=1` the output contains no ANSI escape byte; without it, state is still printed as a word so colour is never the only signal.
- `state_column_is_a_word_not_a_symbol` — NFR-F066-03: `ok`, `guarded`, `exhausted`, and `insufficient_data` render verbatim for the four window fixtures.
- `no_report_line_exceeds_200_characters` — NFR-F066-03: the widest row of the exhausted fixture, including a live exception, stays within the limit.
- `json_is_exactly_one_object` — FR-F066-13: `--json` output parses as a single JSON value with no trailing text and no log lines interleaved on stdout.
- `web_app_and_openapi_are_unchanged` — NFR-F066-02: the feature branch adds no file under `apps/web/` and leaves `openapi/v1.json` byte-identical, because this feature owns no route and no screen.
- `refusal_message_appears_in_both_renderings` — FR-F066-14: the exhausted fixture prints `REFUSED: slo.budget_exhausted availability_core` on stderr and sets `ok: false` with the matching finding in the JSON object.

Evidence: captured stdout and stderr, parsed JSON, and the branch file list under `testing/evidence/F066/frontend/`.
