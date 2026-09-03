---
id: T004
type: task
status: planned
parent_epic: E001
parent_feature: F001
parent_story: S002
depends_on: [T003]
owned_paths: [.github/workflows/**, testing/features/F001/api/**, testing/features/F001/e2e/**]
feature_flag: F001_FEATURE
branch: t004-line-attribution-gates
started_at: null
finished_at: null
---

# T004 — Line/attribution gates

## Identity

- Parent story: `S002` Quality gates
- Owner: platform
- Branch: `t004-line-attribution-gates`

## Decision references

- `docs/architecture-decisions.md` sections 9, 10; `docs/capability-contracts.md` row F001

## Objective

Add the `policy` and `line-limit` jobs to `gates.yml`, wire all five jobs as required status checks, and prove that forbidden attribution and oversized files block a merge.

## Specification

- Owned paths: `.github/workflows/gates.yml` (jobs `policy`, `line-limit`), `.github/workflows/required-checks.md` (documented branch-protection settings applied by repository admins)
- Contract/input: `policy` job checks out with `fetch-depth: 0`, writes `${{ github.event.pull_request.title }}` and body to `title.txt` and `body.txt`, runs `cargo xtask self-test`, `cargo xtask audit-range origin/main..HEAD`, `cargo xtask audit-pr title.txt body.txt`; `line-limit` job runs `cargo xtask validate-tickets` (which includes the 500-line scan) and fails on `limit is 500`.
- Output/behavior: a commit body, PR title, or PR body containing a forbidden attribution token fails `policy` with output beginning `BLOCKED:`; a 501-line file fails `line-limit` with `<path>: 501 lines; limit is 500`; both jobs always run, including docs-only changes; branch protection on `main` requires `validate-work`, `rust`, `web`, `policy`, `line-limit`, blocks direct pushes, and requires maintainer review for `.github/workflows/**`.
- Dependencies: T003 workflow skeleton; F042 commands `audit-range`, `audit-pr`, `self-test`; F041 `validate-tickets`.
- Feature flag: `F001_FEATURE` (gates are not flag-controlled)

## TDD

- Failing test first: `testing/features/F001/api/gate_tests.rs::policy_job_blocks_attribution_token`, `::policy_job_passes_clean_history`, `::line_limit_job_blocks_501_lines`, `::line_limit_job_allows_500_lines`; `testing/features/F001/e2e/gates.spec.ts::poisoned_pr_cannot_merge`, `::non_maintainer_push_to_main_rejected`
- Targeted command: `cargo xtask test-feature F001`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: fixture clone with a poisoned commit, a 501-line file, and a clean commit; branch-protection assertions read via `gh api repos/{owner}/{repo}/branches/main/protection`

## Exit criteria

- [ ] Tests written before the jobs and observed failing
- [ ] Poisoned and oversized fixture PRs blocked; clean PR merges
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S002
- [ ] `finished_at` recorded
