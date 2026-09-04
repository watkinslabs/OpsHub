# OpsHub

Work management platform: sheets and typed work records, views, forms, workflows and approvals,
reports and dashboards, project and portfolio management, enterprise identity, integrations, and
permission-aware AI.

**Status: specification complete, implementation not started.** This repository currently holds the
architecture decisions, the capability contract catalog, and a fully specified backlog with its test
harness manifests. No product code has been written yet. A green harness manifest is not evidence of
implementation.

## Layout

| Path | Contents |
|---|---|
| `docs/architecture-decisions.md` | Frozen architecture decisions. The gate every other document is checked against. |
| `docs/capability-contracts.md` | Contract catalog: aggregate, module slug, routes, events, tables, and roles per feature. |
| `docs/product-capability-spec.md` | Product requirements and build order. |
| `work/plan.md` | Delivery index: every feature with its stories, tasks, and dependencies. |
| `docs/capacity.md` | What 506 points means in time, with the assumptions stated. |
| `docs/contributing.md` | Day-one setup, how to pick up work, and the pull-request and review policy. |
| `docs/accessibility-conformance.md` | The WCAG 2.2 AA claim, the tests behind it, and where we fall short. |
| `docs/incident-management.md` | Severity, roles, behaviour during an incident, and the postmortem contract. |
| `docs/security-disclosure.md` | How to report a vulnerability, our commitments, safe harbour, and the testing programme. |
| `docs/packaging.md` | What each plan includes: limits and the module-by-plan matrix F064 projects onto F048. |
| `docs/engineering-standards.md` | How code is written and styled: tokens, components, icons, Rust, tests, and what enforces each rule. |
| `docs/threat-model.md` | Assets, trust boundaries, threats and the feature that answers each. Required before implementation. |
| `docs/authorization-model.md` | The permission catalogue, principal kinds and role catalogue every feature authorizes against. |
| `docs/milestones/README.md` | What each milestone M0–M7 contains and its exit criteria, generated from the tickets. |
| `work/epics/`, `work/tickets/`, `work/stories/`, `work/tasks/` | 9 epics, 61 feature tickets, 122 stories, 244 tasks. |
| `work/inprogress/`, `work/archived/` | Lifecycle folders. A work item file moves between folders; it is never copied. |
| `testing/features/F###/` | Per-feature, feature-gated test harness: `feature.toml` plus seven lanes of cases. |
| `automation/xtask/` | The validation gates, runnable as `cargo xtask <command>`. |
| `.githooks/` | `commit-msg`, `pre-commit`, and `pre-push` hooks that run those gates. |

Planned product code lands in `crates/` (domain), `services/` (api, worker, realtime, mcp), and
`apps/web/` (React), with migrations in `services/api/migrations/`. PostgreSQL 18 is the target
database.

## Gates

Run from the repository root:

```sh
export CARGO_TARGET_DIR=/tmp/opshub-xtask-target
M=automation/xtask/Cargo.toml
cargo run --quiet --manifest-path $M -- validate-decisions   # architecture decisions parse and agree
cargo run --quiet --manifest-path $M -- validate-plan        # every plan row has a file, and vice versa
cargo run --quiet --manifest-path $M -- validate-work        # backlog content quality
cargo run --quiet --manifest-path $M -- check-contracts      # tickets match the contract catalog
cargo run --quiet --manifest-path $M -- test-all             # every feature harness is valid
cargo run --quiet --manifest-path $M -- self-test            # the gates' own positive controls
```

All six pass on `main`. Run them rather than trusting this line.

`validate-work` and `validate-plan` check different things and neither subsumes the other:
`validate-work` inspects the content of files that exist, so a plan row whose file was never created
is invisible to it. Always run both.

Enable the hooks once per clone:

```sh
git config core.hooksPath .githooks
```

## Working rules

The full rules live in the repository rules file at the root; the ones that bite most often:

- Every file is 500 lines or fewer, including documentation.
- One feature is one ticket. Stories and tasks are its child specifications.
- Requirement IDs and failing tests come before implementation.
- An agent edits only the `owned_paths` its work item declares, and those globs are module-scoped and
  disjoint across features.
- Test code lives under `testing/`, outside live code, behind a feature flag.
- Never weaken the commit, push, ownership, dependency, or policy gates to make a change land.

## License

MIT. See [LICENSE](LICENSE).
