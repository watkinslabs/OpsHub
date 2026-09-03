# F042 database cases

No PostgreSQL table exists for this feature; persistence is the git index, git history, `.githooks/`, and `work/inprogress/`, so this lane holds git-index and hook persistence cases instead of migration cases. File: `testing/features/F042/database/index_tests.rs`. Flag `F042_FEATURE`.

- `staged_blob_read_from_index_not_worktree` — FR-F042-02: token added to the working tree after staging is not reported; token staged then removed from the worktree is reported.
- `deleted_staged_path_not_checked` — FR-F042-02: `git rm` of a file outside ownership produces no `ownership.outside`.
- `renamed_path_checked_at_destination` — FR-F042-06: rename into an unowned directory → `ownership.outside` on the new path.
- `working_tree_untouched_by_audits` — NFR-F042-02: `git status --porcelain` identical before and after every command.
- `only_git_subprocesses_spawned` — NFR-F042-02: `strace -f -e execve` shows only `git` executions with fixed argument lists.
- `hooks_path_persisted_in_git_config` — FR-F042-10: `git config core.hooksPath` equals `.githooks` after `install-hooks`.

Evidence: test log and strace summaries under `testing/evidence/F042/database/`.
