# F041 e2e cases

File: `testing/features/F041/e2e/hooks.spec.sh` (shell, run by `cargo xtask test-feature F041`). Each case creates a scratch clone with `cargo xtask install-hooks` and commits through the real hooks. Flag `F041_FEATURE`.

- `pre_commit_blocks_invalid_ticket` — FR-F041-06, FR-F041-15: staging a task with a dependency cycle → `git commit` fails, output contains `depends.cycle`.
- `pre_commit_passes_clean_backlog` — FR-F041-15: staging a valid new task listed in the plan → commit succeeds.
- `pre_push_runs_validate_plan` — FR-F041-13: a commit that deletes `work/tasks/T900-alpha.md` without editing the plan → push rejected with `plan.missing_item`.
- `ci_job_annotates_findings` — NFR-F041-04: running the `gates.yml` validate step script with `GITHUB_ACTIONS=true` on the cycle fixture prints `::error file=work/tasks/T900-alpha.md,line=8::depends.cycle …`.
- `scaffold_then_validate` — FR-F041-09: `scaffold-plan` on a fixture plan, then `validate-work` reports only `content.too_thin`.

Evidence: hook transcripts under `testing/evidence/F041/e2e/`.
