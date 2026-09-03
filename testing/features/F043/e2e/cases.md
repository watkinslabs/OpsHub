# F043 e2e cases

File: `testing/features/F043/e2e/lanes.spec.sh`. Runs the full lane protocol in a scratch repository with a stub harness script that records its environment and writes junit output. Flag `F043_FEATURE`.

- `two_lanes_run_concurrently_without_shared_state` — FR-F043-07, FR-F043-08, FR-F043-09: claim T900 and T902, run `test-feature` in both worktrees at once, assert distinct schemas, prefixes, ports, and two manifests.
- `full_lifecycle_claim_test_collect_release` — FR-F043-02, FR-F043-11: end to end for T900; final state archived, worktree gone, branch present, slot free.
- `outside_lane_test_feature_uses_defaults` — FR-F043-08: from the repository root no `OPSHUB_TEST_*` variables are exported.
- `commit_inside_lane_passes_ownership_gate` — FR-F043-02: a commit in `.worktrees/t900-alpha` touching an owned path passes `pre-commit`; touching an unowned path fails.
- `abandon_then_reclaim` — FR-F043-12: abandon T900, claim again → new slot, fresh worktree, no stale lane file.

Evidence: transcripts and both manifests under `testing/evidence/F043/e2e/`.
