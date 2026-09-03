# F043 database cases

No PostgreSQL table exists for this feature; persistence is `.lanes/<ID>.toml`, `.lanes/slots.toml`, `.lanes/history.log`, `work/inprogress/**`, and `testing/evidence/<ID>/**`, so this lane holds those persistence cases instead of migration cases. File: `testing/features/F043/database/{lanefile_tests.rs,evidence_tests.rs}`. Flag `F043_FEATURE`.

- `lane_file_written_atomically` — FR-F043-04: a simulated crash after the temp file exists leaves no `.lanes/T900.toml`; the temp file is cleaned by `--repair`.
- `concurrent_claims_get_distinct_slots` — FR-F043-05: two processes claiming T900 and T901 at once → slots 0 and 1, `slots.toml` consistent.
- `slots_exhausted_at_100` — FR-F043-05.
- `history_log_append_only` — FR-F043-15, NFR-F043-04: line count grows by exactly one per command; earlier lines unchanged.
- `repair_reconciles_missing_worktree` — NFR-F043-04: worktree directory deleted by hand → `--repair` recreates it from the branch.
- `lane_directories_git_ignored` — NFR-F043-02: `git status --porcelain` shows nothing after claim and collection.
- `second_collection_identical_file_list` — FR-F043-10: two manifests equal except `collected_at` and `head_commit`.
- `evidence_kept_on_abandon_unless_purged` — FR-F043-12.

Evidence: test log under `testing/evidence/F043/database/`.
