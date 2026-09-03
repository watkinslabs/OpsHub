# F043 frontend cases

No UI: covered by CLI output cases. File: `testing/features/F043/frontend/output_tests.rs`. Flag `F043_FEATURE`.

- `claim_summary_line_format` — FR-F043-02: stdout `claimed T900 on t900-alpha at .worktrees/t900-alpha (slot 0)`.
- `list_output_sorted_and_empty_message` — FR-F043-14: three lanes listed by id; none → `no active lanes`.
- `refusal_lines_use_refused_prefix_and_exit_three` — FR-F043-15: `REFUSED: lane.precondition …`, exit 3.
- `manifest_json_schema` — FR-F043-09: keys `id, branch, base_commit, head_commit, collected_at, owner, lanes, commands`; file records `path, sha256, bytes`.

Evidence: captured output under `testing/evidence/F043/frontend/`.
