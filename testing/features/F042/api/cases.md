# F042 api cases

File: `testing/features/F042/api/{scan_tests.rs,audit_tests.rs,ownership_tests.rs,dependency_tests.rs,selftest_tests.rs}`. Each test builds a scratch repository, stages or commits generated content, runs the prebuilt `xtask` binary, and asserts exit code, stderr, and `--json`. Flag `F042_FEATURE`.

- `mixed_case_token_with_zero_width_joiner_detected` — FR-F042-01: `policy.token` with the token index and original column.
- `fullwidth_token_detected_with_original_column` — FR-F042-01: NFKC folds full-width letters; column points at the first full-width character.
- `finding_output_masks_token` — FR-F042-14: message contains `token #1 (c*****)` style masking and asterisks in the context line.
- `binary_blob_skipped` — FR-F042-02: staged file with a NUL byte and a token is not reported.
- `token_across_window_boundary_detected` — FR-F042-13: 3 MiB blob with the token at offset 1,048,570 → exactly one finding.
- `staged_policy_file_skipped_but_message_not` — FR-F042-02, FR-F042-03: `automation/README.md` staged → 0 findings; same text as message → 1 finding.
- `scissors_tail_ignored_in_message` — FR-F042-03: token after the scissors line → exit 0.
- `range_reports_author_email_part` — FR-F042-04: finding labelled `commit:<sha7> author email`.
- `range_invalid_exits_two` — FR-F042-04: `audit-range nope..nope` → exit 2 with git error.
- `pr_missing_body_file_exits_two` — FR-F042-05.
- `glob_double_star_matches_nested_not_sibling_prefix` — FR-F042-06: `sheets/**` matches `sheets/a/b.rs`, not `sheetsx/b.rs`.
- `staged_path_outside_active_globs_rejected` — FR-F042-06: message names active ids.
- `policy_file_never_outside` — FR-F042-06: staged `.githooks/pre-commit` passes while the only active item owns `services/api/src/sheets/**`.
- `empty_inprogress_skips_with_exit_zero` — FR-F042-06.
- `two_features_overlapping_globs_rejected` — FR-F042-07.
- `story_and_its_task_may_overlap` — FR-F042-07: S900 and T900 both own the same glob → no finding.
- `staged_path_matched_by_two_features_is_ambiguous` — FR-F042-07.
- `active_item_with_unarchived_dependency_rejected` — FR-F042-08.
- `archived_dependency_satisfies_gate` — FR-F042-08: dependency in `work/archived` with `status: done` → no finding.
- `conflicting_active_items_rejected` — FR-F042-08.
- `self_test_passes_on_clean_checkout` — FR-F042-09: summary `policy self-test passed (N controls)`.
- `self_test_fails_when_control_is_broken` — FR-F042-09: policy compiled with no tokens → `policy.selftest token_variants`.
- `self_test_reports_hook_not_executable` — FR-F042-09: mode 0644 hook → `hooks.not_executable`.
- `self_test_reports_hook_syntax_error` — FR-F042-09: hook with unbalanced `if` → `hooks.syntax`.
- `usage_error_exits_two` — FR-F042-12: `audit-message` without a file → exit 2.

Evidence: JUnit output and captured stdout/stderr under `testing/evidence/F042/api/`.
