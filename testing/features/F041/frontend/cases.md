# F041 frontend cases

No UI: covered by CLI output cases. File: `testing/features/F041/frontend/output_tests.rs`. Flag `F041_FEATURE`.

- `text_findings_sorted_by_path_line_code` — FR-F041-15: fixture with findings in three files → stderr order matches `sort -k2,2 -k3,3n`.
- `json_object_shape_matches_contract` — FR-F041-15: keys exactly `command, ok, checked, findings, duration_ms`; each finding has `code, path, line, message`.
- `success_prints_single_summary_line` — FR-F041-15: clean fixture → stdout `validate-work passed (26 items)`, empty stderr, exit 0.
- `two_runs_are_byte_identical` — NFR-F041-04: text mode output of two consecutive runs equal.

Evidence: captured output under `testing/evidence/F041/frontend/`.
