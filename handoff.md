# OpsHub handoff

Status: READY FOR IMPLEMENTATION. Planning/specification phase complete. Product code has not started.

## Current state

- Repository root: `/home/nd/ent/OpsHub`.
- Git repository initialized on `main`; remote: `watkinslabs/OpsHub`.
- No commit or push has been made. Every file is untracked.
- PostgreSQL 18 is the selected database version.
- Architecture decisions are frozen in `docs/architecture-decisions.md`.
- Product requirements and build order are in `docs/product-capability-spec.md`.
- Generated contract catalog: `docs/capability-contracts.md`.
- Delivery index: `work/plan.md`.
- Rules: the repository rules file at the root, and `MANIFEST.md`.

## Backlog

- 9 epics in `work/epics/`.
- 61 feature tickets in `work/tickets/`.
- 122 stories in `work/stories/`.
- 244 tasks in `work/tasks/`.
- 61 feature-gated harness manifests in `testing/features/`, each with seven lane `cases.md` files.
- Every backlog file is hand-written specification. No generated stub remains: `validate-work` passes
  436 items with zero findings, which enforces 8+ FR and 4+ NFR per feature, 5+ SR per story, named
  failing tests per task, gherkin scenarios, catalog routes/events/tables reproduced in the ticket,
  `depends_on` equal to the plan row, module-scoped disjoint `owned_paths`, and feature-specific
  harness cases in every lane.
- Tickets include branch, ownership, aggregate, module slug, lifecycle timestamps, TDD, requirements,
  contracts, acceptance, exit, and rollback sections.

## Covered product scope

Core sheets/work records, typed columns, formulas, views, forms, comments, files, sharing, permissions, live collaboration, workflows, approvals, notifications, reports, dashboards, project/portfolio management, resources, enterprise identity, integrations, APIs, MCP, mobile/PWA, publishing, conditional formatting, update requests, advanced modules, and permission-aware AI.

## Automation

Run from repository root:

```text
CARGO_TARGET_DIR=/tmp/opshub-xtask-target cargo run --quiet --manifest-path automation/xtask/Cargo.toml -- validate-decisions
CARGO_TARGET_DIR=/tmp/opshub-xtask-target cargo run --quiet --manifest-path automation/xtask/Cargo.toml -- validate-plan
CARGO_TARGET_DIR=/tmp/opshub-xtask-target cargo run --quiet --manifest-path automation/xtask/Cargo.toml -- validate-work
CARGO_TARGET_DIR=/tmp/opshub-xtask-target cargo run --quiet --manifest-path automation/xtask/Cargo.toml -- check-contracts
CARGO_TARGET_DIR=/tmp/opshub-xtask-target cargo run --quiet --manifest-path automation/xtask/Cargo.toml -- test-all
CARGO_TARGET_DIR=/tmp/opshub-xtask-target cargo run --quiet --manifest-path automation/xtask/Cargo.toml -- self-test
```

All six pass as of this handoff:

```text
validate-decisions   architecture decisions passed
validate-plan        plan/file parity passed
validate-work        work validation passed: 436 items
check-contracts      contract checks passed: 61 rows
self-test            content + policy self-test passed
test-all             all 61 feature harnesses valid
```

Verify this claim by running them; do not trust it. Two of these gates were failing while a previous
handoff asserted they passed.

Harnesses are manifests and test cases; executable production tests begin with implementation.

## Gate notes for the next session

- `check-contracts` requires each ticket to name its catalog aggregate backticked. Section 1 of every
  ticket carries an `- Aggregate:` line for this. Rewriting a ticket without it fails the gate.
- `validate-work` only inspects files that exist. A plan row whose file was never created is invisible
  to it and is caught solely by `validate-plan`. Run both.
- `CATCH_ALL_EXEMPT` in `automation/xtask/src/content.rs` lists the non-module roots that may be owned
  directly (`.github/workflows/**`, `.githooks/**`, `infra/**`, `openapi/**`, `.lanes/**`,
  `.worktrees/**`, `.agent-target/**`, `testing/evidence/**`), matching FR-F041-08. The content
  self-test pins it: adding a source-tree root to that list fails `self-test`.

## Rules to preserve

- Do not generate backlog files until decision validation passes.
- Keep every file at 500 lines or fewer.
- Keep testing code under `testing/`, outside live code, and feature gated.
- Use one feature per ticket; archive completed tickets from the active folder.
- Never weaken commit, push, PR, ownership, dependency, or policy gates.
- Do not claim implementation from a green harness manifest.

## Next session

First command:

```text
git status --short && sed -n '1,120p' "$(ls | grep -i '^cla.*\.md$')" && sed -n '1,120p' work/plan.md
```

Next work: choose the lowest-order feature in `work/plan.md`, create its branch, claim its owned paths, write failing executable tests in `testing/features/F###/`, then implement the Rust/API/data/UI vertical slice.
