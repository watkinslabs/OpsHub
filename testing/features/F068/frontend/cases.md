# F068 frontend cases

F068 ships no React component, no client, and no route — a repository is reached only through handlers other features own. This lane is therefore a negative-control lane plus the rendering contract for the one surface a person reads: the `check-persistence` output, which must appear identically as sorted `BLOCKED:` lines and as a single JSON object under the F041 output rules. File: `testing/features/F068/frontend/output_tests.rs`. Flag `F068_FEATURE`.

- `web_app_and_openapi_are_unchanged` — NFR-F068-02: the branch adds no file under `apps/web/` and leaves `openapi/v1.json` byte-identical, because this feature owns no route and no screen.
- `no_typescript_client_references_the_crate` — FR-F068-13: no file under `apps/web/src/` mentions `Repository`, `UnitOfWork`, `PgPool`, or a table name; the browser reaches data through `/api/v1` only.
- `findings_sorted_by_path_line_code` — FR-F068-16: a fixture tree with findings in three files produces stderr ordered exactly as `sort -k2,2 -k3,3n`, so two runs are diffable.
- `text_and_json_findings_carry_the_same_fields` — FR-F068-16: every `BLOCKED:` line has a matching entry in the `--json` findings array with the same `code`, `path`, `line`, and `message`, and neither rendering carries a finding the other omits.
- `json_object_shape_matches_contract` — FR-F068-16: the `--json` output parses as exactly one object with keys `command`, `ok`, `checked`, `findings`, `duration_ms`, with no trailing text and no log lines interleaved on stdout.
- `success_prints_a_single_summary_line` — FR-F068-16: the clean fixture tree prints `check-persistence passed (94 items)` on stdout, leaves stderr empty, and exits 0.
- `refusal_appears_in_both_renderings` — FR-F068-16: a baseline-widening run prints `REFUSED: persist.baseline_widened` on stderr, sets `ok: false` with the matching finding in the JSON object, and exits 3.
- `two_runs_are_byte_identical` — NFR-F068-04: text output of two consecutive runs over an unchanged tree is equal byte for byte, including ordering and the item count.

Evidence: captured stdout and stderr under `testing/evidence/F068/frontend/`.
