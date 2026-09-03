---
id: T003
type: task
status: planned
parent_epic: E001
parent_feature: F001
parent_story: S002
depends_on: [T002]
owned_paths: [.github/workflows/**, testing/features/F001/api/**, testing/features/F001/performance/**]
feature_flag: F001_FEATURE
branch: t003-ci-matrix
started_at: null
finished_at: null
---

# T003 — CI matrix

## Identity

- Parent story: `S002` Quality gates
- Owner: platform
- Branch: `t003-ci-matrix`

## Decision references

- `docs/architecture-decisions.md` section 9; `docs/capability-contracts.md` row F001

## Objective

Create `.github/workflows/gates.yml` with the `validate-work`, `rust`, and `web` jobs, service containers, caches, concurrency, path filters, and evidence artifacts.

## Specification

- Owned paths: `.github/workflows/gates.yml`
- Contract/input: triggers `pull_request` and `push: branches: [main]`; `concurrency: { group: gates-${{ github.ref }}, cancel-in-progress: true }`; default `permissions: contents: read`; actions pinned by SHA; path filter step that sets `docs_only=true` when every changed path matches `docs/**` or `*.md` outside `work/`.
- Output/behavior: job `validate-work` runs `cargo xtask validate-work`, `validate-plan`, `validate-tickets`, `check-contracts`, `check-migrations` in order and fails on the first `BLOCKED:`; job `rust` (skipped when `docs_only`) starts services `postgres:18` (`opshub_test`) and `nats:2.11` (`-js`), exports `DATABASE_URL` and `NATS_URL`, runs `cargo fmt --all --check`, `cargo clippy --workspace --all-targets -- -D warnings`, `cargo deny check advisories`, `cargo sqlx database create`, `cargo test --workspace -- --format junit > rust-junit.xml`, uploads `rust-junit`; job `web` (skipped when `docs_only`) runs `pnpm install --frozen-lockfile`, `lint`, `typecheck`, `test -- --reporter=junit`, `build`, uploads `web-build`; caches keyed by `Cargo.lock` and `pnpm-lock.yaml` hashes; every job appends a markdown summary and uploads `testing/evidence/F001/**`.
- Dependencies: T001 and T002 so the commands succeed; F041/F042 xtask commands.
- Feature flag: `F001_FEATURE` (workflow is not gated)

## TDD

- Failing test first: `testing/features/F001/api/workflow_tests.rs::gates_workflow_declares_five_required_jobs`, `::validate_work_job_runs_commands_in_order`, `::rust_job_uses_postgres18_and_nats_services`, `::docs_only_change_skips_matrix_but_not_policy`; `testing/features/F001/performance/ci_budget_tests.rs::warm_workflow_under_15_minutes`
- Targeted command: `cargo xtask test-feature F001`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `gates.yml` parsed with `serde_yaml`; local workflow runner executes jobs against the fixture clone

## Exit criteria

- [ ] Tests written before the workflow and observed failing
- [ ] Workflow green on a PR and on `main`; artifacts `rust-junit` and `web-build` present
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S002
- [ ] `finished_at` recorded
