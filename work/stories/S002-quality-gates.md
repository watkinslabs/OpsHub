---
id: S002
type: story
status: planned
parent_epic: E001
parent_feature: F001
depends_on: [S001]
owned_paths: [.github/workflows/**, testing/features/F001/**]
feature_flag: F001_FEATURE
branch: s002-quality-gates
started_at: null
finished_at: null
---

# S002 — Quality gates

## Identity

- Parent feature: `F001` Repository and CI
- Owner: platform
- Branch: `s002-quality-gates`

## Decision references

- `docs/architecture-decisions.md` sections 9 (testing), 10 (ticket gate)
- `docs/capability-contracts.md` row F001

## Vertical slice

As a maintainer, I want every pull request into `main` to run the work-graph validators, Rust and web test matrices, the attribution policy audit, and the 500-line gate as required checks, so that invalid tickets, forbidden attribution, and broken builds never merge.

## Requirements

- **SR-S002-01:** `.github/workflows/gates.yml` defines jobs `validate-work`, `rust`, `web`, `policy`, `line-limit`; branch protection lists all five as required and a PR with any failing or missing check cannot merge (covers FR-F001-06).
- **SR-S002-02:** `validate-work` runs `cargo xtask validate-work`, `validate-plan`, `validate-tickets`, `check-contracts`, `check-migrations` in order and surfaces the first `BLOCKED:` output (FR-F001-07).
- **SR-S002-03:** `policy` runs `self-test`, `audit-range origin/main..HEAD`, and `audit-pr title.txt body.txt`; a forbidden attribution token in a commit body, PR title, or PR body fails the job with `BLOCKED:` (FR-F001-08).
- **SR-S002-04:** `line-limit` fails with `<path>: <n> lines; limit is 500` for a 501-line file and passes for 500 lines (FR-F001-09).
- **SR-S002-05:** `rust` runs fmt, clippy, `cargo deny check advisories`, and `cargo test --workspace` against `postgres:18` and `nats:2.11` service containers and uploads `rust-junit`; `web` runs lint, typecheck, Vitest JUnit, and build and uploads `web-build` (FR-F001-10, FR-F001-11, NFR-F001-02).
- **SR-S002-06:** Concurrency group `gates-${{ github.ref }}` cancels superseded runs; docs-only changes skip `rust` and `web` but never `validate-work`, `policy`, or `line-limit` (FR-F001-12).
- **SR-S002-07:** A full run completes under 15 minutes with warm caches and writes evidence to `testing/evidence/F001/` (NFR-F001-01, FR-F001-14).

## Surfaces

- Infrastructure/container: GitHub Actions service containers `postgres:18`, `nats:2.11` (CI only; F004 owns local compose)
- Rust service/API: none new; jobs invoke the F041/F042 xtask commands
- Data/migration: none; `cargo sqlx database create` runs in the `rust` job
- React/UI: none
- Mocks/fixtures: `testing/fixtures/platform.rs` builds a temporary clone with a poisoned commit, a 501-line file, and an invalid ticket; local workflow runner executes `gates.yml` jobs against it

## TDD harness

- Test path: `testing/features/F001/{api,e2e,performance}/`
- Feature flag: `F001_FEATURE`
- Targeted command: `cargo xtask test-feature F001`
- Full command: `cargo xtask test-all`
- First failing tests: `gates_workflow_declares_five_required_jobs`, `policy_job_blocks_attribution_token`, `line_limit_job_blocks_501_lines`, `validate_work_job_runs_commands_in_order`, `docs_only_change_skips_matrix_but_not_policy`

## Exit criteria

- [ ] Requirement tests SR-S002-01 through SR-S002-07 written first and failing
- [ ] Tasks T003 and T004 complete; `gates.yml` green on a PR and on `main`
- [ ] Command, E2E, and performance lanes pass in targeted and full modes
- [ ] Production call path named: `.github/workflows/gates.yml` triggered on `pull_request` and `push` to `main`, required checks configured on `main`
- [ ] Handoff evidence recorded in the F001 ticket
