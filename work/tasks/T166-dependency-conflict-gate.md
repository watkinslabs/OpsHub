---
id: T166
type: task
status: planned
parent_epic: E000
parent_feature: F042
parent_story: S083
depends_on: [T165]
owned_paths: [automation/xtask/src/policy.rs, .githooks/**, testing/features/F042/api/**, testing/features/F042/e2e/**, testing/features/F042/performance/**]
feature_flag: F042_FEATURE
branch: t166-dependency-conflict-gate
started_at: null
finished_at: null
---

# T166 — Dependency/conflict gate

## Identity

- Parent story: `S083` Staged/commit/PR audit
- Owner: platform
- Branch: `t166-dependency-conflict-gate`
- Decision references: `docs/architecture-decisions.md` sections 9–10; `docs/capability-contracts.md` row F042

## Objective

Add the dependency and conflict checks over active items, rewrite the three hook scripts to the documented fail-fast order, and implement idempotent `install-hooks`, so a commit or push cannot proceed while an active item is out of order.

## Specification

- Owned paths: `automation/xtask/src/policy.rs` (`ownership::{ActiveItem, OwnershipSet, load_active, check_dependencies}`, `install_hooks`), `.githooks/pre-commit`, `.githooks/commit-msg`, `.githooks/pre-push`
- Contract/input: `WorkGraph` from F041; active items are every file in `work/inprogress/`; archived items are files in `work/archived/` with `status: done|archived`
- Output/behavior: `depends.unmet <active id>: <dep id> is not archived` for each unmet dependency; `depends.conflict <a> conflicts_with <b>` when both are active; `pre-commit` runs `audit-staged` (token scan plus ownership), `validate-plan`, `validate-work`, `check-contracts` with `set -eu` so the first failure stops; `commit-msg` runs `audit-message "$1"`; `pre-push` reads `local_ref local_oid remote_ref remote_oid` lines, skips deleted refs, uses `local_oid` alone for new branches and `remote_oid..local_oid` otherwise, then runs the three validators; all scripts export `CARGO_TARGET_DIR=${CARGO_TARGET_DIR:-/tmp/opshub-xtask-target}`; `install-hooks` sets `core.hooksPath=.githooks`, chmod 0755, prints the path, and prints a `cargo build --manifest-path automation/xtask/Cargo.toml` hint when the target dir is cold
- Dependencies: T165 scanner and audit commands
- Feature flag: `F042_FEATURE`
- Budgets: `audit-staged` 200 files / 20 MiB < 1 s; `audit-range` 1,000 commits < 2 s

## TDD

- Failing test first: `testing/features/F042/api/dependency_tests.rs::active_item_with_unarchived_dependency_rejected`, `::conflicting_active_items_rejected`, `::archived_dependency_satisfies_gate`, `testing/features/F042/e2e/hooks.spec.sh::commit_with_token_in_message_rejected`, `::push_new_branch_scans_whole_history`, `::push_existing_branch_scans_range_only`, `::install_hooks_twice_is_idempotent`, `testing/features/F042/performance/audit_bench.rs::audit_staged_200_files_under_1s`, `::audit_range_1000_commits_under_2s`
- Targeted command: `cargo xtask test-feature F042`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/features/F042/fixtures/{unmet,conflict}`; scratch repository with a bare remote for push tests; generated 1,000-commit history with fixed dates

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Hooks pass `sh -n` and are executable; scratch clone rejects the fixtures through the real hooks
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S083
- [ ] `finished_at` recorded
