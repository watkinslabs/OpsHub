# F042 frontend cases

No UI: covered by CLI output cases. File: `testing/features/F042/frontend/output_tests.rs`. Flag `F042_FEATURE`.

- `json_shape_for_audit_commands` — FR-F042-12: `audit-staged --json` has `command, ok, checked{files,bytes}, findings[{code,path,line,column,message}], duration_ms`.
- `exit_codes_zero_one_two` — FR-F042-12: clean → 0; token → 1; bad range → 2.
- `two_runs_byte_identical` — NFR-F042-04: text output of `audit-range` on the same history equal across runs.
- `ownership_skip_message_on_empty_inprogress` — FR-F042-06: stdout `check-ownership skipped: no active items`.

Evidence: captured output under `testing/evidence/F042/frontend/`.
