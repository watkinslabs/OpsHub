# F043 api cases

File: `testing/features/F043/api/{claim_tests.rs,target_tests.rs,fixture_tests.rs,artifacts_tests.rs}`. Each test builds a scratch repository with `main`, a bare `origin`, and the `fixtures/graph` work tree, then runs the prebuilt `xtask` binary with `XTASK_NOW=2026-09-03T00:00:00Z` and `XTASK_OWNER=fixture@example.test`. Flag `F043_FEATURE`.

- `claim_refused_when_dependency_not_archived` — FR-F043-01: `REFUSED: lane.precondition T901: depends_on T900 is not archived`, exit 3.
- `claim_refused_when_paths_overlap_active_feature` — FR-F043-01: active F901 owns the same glob → refused.
- `claim_refused_when_status_not_planned` — FR-F043-01: `status: blocked` → refused.
- `claim_moves_file_and_sets_started_at_from_xtask_now` — FR-F043-02: diff of old and new file is exactly two lines.
- `claim_creates_branch_and_worktree_from_origin_main` — FR-F043-03: `git worktree list` shows the path; `base_commit` equals `origin/main`.
- `claim_refuses_existing_branch` — FR-F043-03: `lane.branch_exists`.
- `second_claim_fails_with_lane_exists` — FR-F043-04.
- `allocate_target_idempotent_export_lines` — FR-F043-06.
- `allocate_target_json_shape` — FR-F043-06.
- `allocate_target_non_owner_refused` — FR-F043-13.
- `fixture_values_deterministic_for_lane` — FR-F043-07: two runs identical; values match the UUIDv5 and crc32 computed in the test.
- `port_block_derived_from_slot` — FR-F043-07: slot 3 → `OPSHUB_TEST_PORT_BASE=20030`.
- `port_in_use_refused` — FR-F043-07: listener on 20005 → `lane.port_in_use 20005`.
- `tenant_ids_differ_between_lanes` — FR-F043-07.
- `current_lane_detected_from_nested_directory` — FR-F043-08.
- `manifest_lists_files_sorted_with_sha256` — FR-F043-09: hashes equal `sha256sum` of fixtures.
- `lane_status_from_junit_and_axe` — FR-F043-09: one failing junit → `api: fail`; missing lane → `missing`.
- `artifacts_over_cap_refused` — FR-F043-10.
- `symlink_escape_refused` — FR-F043-10, NFR-F043-02.
- `release_done_requires_passing_manifest` — FR-F043-11.
- `release_done_refuses_dirty_worktree` — FR-F043-11: `lane.dirty`.
- `release_done_archives_and_frees_slot` — FR-F043-11: file in `work/archived`, `finished_at` set, slot free, branch still exists.
- `abandon_restores_planning_file_bytes` — FR-F043-12.
- `non_owner_release_refused` — FR-F043-13.
- `owner_override_recorded_in_lane_history` — FR-F043-13, FR-F043-15.
- `list_prints_sorted_lanes` — FR-F043-14.

Evidence: JUnit output and captured stdout/stderr under `testing/evidence/F043/api/`.
