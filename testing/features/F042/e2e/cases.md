# F042 e2e cases

File: `testing/features/F042/e2e/hooks.spec.sh`. Each case clones a scratch repository with a bare remote, runs `cargo xtask install-hooks`, and drives real `git commit` and `git push`. Flag `F042_FEATURE`.

- `commit_with_token_in_staged_file_rejected` — FR-F042-02, FR-F042-11: `git commit` fails at `pre-commit`; validators after `audit-staged` do not run (marker file absent).
- `commit_with_token_in_message_rejected` — FR-F042-03: `git commit -m` with a generated token fails at `commit-msg`.
- `push_new_branch_scans_whole_history` — FR-F042-04, FR-F042-11: token in the first commit of a new branch → push rejected.
- `push_existing_branch_scans_range_only` — FR-F042-11: token in a commit already on the remote does not block a later push.
- `no_verify_commit_caught_by_ci_range_audit` — NFR-F042-04: `git commit --no-verify` then the `gates.yml` validate script with `audit-range origin/main..HEAD` → exit 1.
- `install_hooks_twice_is_idempotent` — FR-F042-10.
- `pr_gate_script_reads_title_and_body_files` — FR-F042-05: the CI `pull request text gate` step script with a token in `PR_BODY` → exit 1.

Evidence: hook and push transcripts under `testing/evidence/F042/e2e/`.
