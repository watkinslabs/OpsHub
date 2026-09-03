---
id: E000
type: epic
status: planned
owner: platform
target_milestone: M0
branch: e000-developer-workflow-and-delivery-control-plane
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 1, 3, 8, 9, 10
- Capability contract: `docs/capability-contracts.md` tooling rows F041, F042, F043, F044
- Product spec: `docs/product-capability-spec.md` section 7 Phase 0, section 8 release gates, section 10 flag decision

# E000 — Developer workflow and delivery control plane

## Outcome

Before any product code exists, the repository must be able to police itself. This epic delivers the `cargo xtask` control plane that every later feature runs through: a validator that proves the backlog in `work/` is a complete, acyclic, buildable graph; a policy gate wired into `.githooks` and CI that rejects forbidden attribution text and changes outside a claimed ticket's `owned_paths`; a lane allocator that lets several agents or people work in parallel git worktrees with isolated build targets and fixture tenants without stepping on each other; and a contract and release verifier that detects drift between tickets, `docs/capability-contracts.md`, OpenAPI, migrations, and feature flags, and assembles the evidence needed to call a feature releasable. The result is deterministic, machine-readable, and nonzero on failure, so a clean checkout with only Rust stable installed can run the whole gate set in under two minutes.

## Scope

- Included: YAML front matter schema and hierarchy validation for epics, features, stories, and tasks (`validate-work`, `validate-plan`, `validate-tickets`); forbidden-token audit of staged content, commit messages, pushed ranges, and PR text (`audit-staged`, `audit-message`, `audit-range`, `audit-pr`); ownership, dependency, and conflict gates (`check-ownership`); positive-control `self-test`; lane claim and release with git worktrees (`claim-lane`, `release-lane`); per-lane `CARGO_TARGET_DIR` and fixture tenant allocation (`allocate-target`, `allocate-fixture`); evidence collection into `testing/evidence/<ID>/` (`collect-artifacts`); contract, migration, and flag drift detection (`check-contracts`, `check-migrations`, `check-flags`); release and rollback verification (`verify-release`); the `.githooks` scripts and the `install-hooks` command; the split of `automation/xtask/src` into `main.rs`, `policy.rs`, `backlog.rs`, `content.rs`, `lanes.rs`, `release.rs`, and `support.rs`.
- Excluded: the CI workflow file itself and the Rust/React workspace build (F001); the runtime services, compose stack, and health endpoints (F004); any HTTP API, database table, or React surface; generation of OpenAPI or MCP schemas (F028, F047); the scaffold templates in `content.rs` beyond keeping them consistent with the schema; hosting or remote artifact storage.

## Child features

- F041 Work-item schema: front matter, hierarchy, dependency, branch, filename, section, and line-limit validation of `work/**` and `work/plan.md`.
- F042 xtask audit/gates: forbidden-token policy over staged files, commit messages, pushed history, and PR text; owned-path, dependency, and conflict gates; positive-control self-test; `.githooks` wiring.
- F043 Fanout orchestration: lane claiming into `work/inprogress/` with git worktrees, per-lane build target directories, deterministic fixture tenants, and artifact collection.
- F044 Contract/release control: OpenAPI, event, generated-client, and MCP schema drift; migration naming, ordering, and destructive-change safety; feature-flag lifecycle; release and rollback evidence verification.

## Exit criteria

- [ ] On a clean checkout with only Rust stable, `cargo xtask validate-decisions`, `validate-plan`, `validate-work`, `validate-tickets`, `check-contracts`, `check-migrations`, `check-flags`, and `self-test` all exit 0 in under 120 s total, and each emits a JSON summary with `--json`.
- [ ] A commit that stages a file containing a blocked attribution token, or a commit message or PR body containing one, is rejected by the hook and by CI with a masked finding that names the file, line, and column.
- [ ] A staged change outside the `owned_paths` of the items in `work/inprogress/` is rejected; a change inside them passes; two items with overlapping `owned_paths` cannot both be claimed.
- [ ] Two agents can `claim-lane` two non-conflicting tasks, each receives its own worktree, `CARGO_TARGET_DIR`, fixture tenant ID, schema name, and port block, run `cargo xtask test-feature <F>` concurrently, and `collect-artifacts` produces two independent `testing/evidence/<ID>/manifest.json` files.
- [ ] `verify-release F006` (the first product feature to reach archive) refuses until every lane has evidence, contracts and migrations show no drift, the flag is registered, and rollback evidence exists, then writes `testing/evidence/F006/release.json`.
- [ ] The plan exit scenario holds: a clean checkout can validate the complete work graph, reject invalid or attributed changes, claim non-conflicting lanes, run targeted and full gates, and produce auditable release evidence.
