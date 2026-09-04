# OpsHub handoff

Status: READY FOR IMPLEMENTATION. Specification, architecture and design are complete. Product code has not started.

## Current state

- Repository root: `/home/nd/ent/OpsHub`; remote `github.com/watkinslabs/OpsHub` (public, MIT).
- PostgreSQL 18. Rust workspace plus a React 19 web app; no product code written yet.
- Architecture decisions are frozen in `docs/architecture-decisions.md`, including the normalization
  and data-access rules in sections 2 and 2.1.
- Product requirements: `docs/product-capability-spec.md`. Contract catalog: `docs/capability-contracts.md`.
- Milestones and their exit criteria: `docs/milestones/README.md`.
- Authorization vocabulary: `docs/authorization-model.md` — the permission catalogue, principal kinds
  and every role, enforced by `check-roles`.
- Delivery index: `work/plan.md`. Rules: the repository rules file at the root, and `MANIFEST.md`.
- Visual source of truth: `docs/design-canvas.md` links the design canvas.

## Backlog

- 9 epics, 68 feature tickets, 136 stories, 272 tasks, 68 feature-gated harnesses of seven lanes each.
- 8 milestones, 488 estimate points. Every feature declares its milestone; no feature depends on a
  later one, and the dependency graph is acyclic.
- Every functional requirement in every ticket is implemented by at least one story or task.
- 343 tables declared in the catalog, each owned by exactly one feature.

## Design

- 39 screens on the design canvas across six pages: core work, planning and reporting, enterprise,
  advanced modules, public surfaces, and the design system sheets.
- Token, component and chart sheets carry the real values — every colour in both themes, the type
  ramp, spacing, radii, elevation, motion, density — so the screens and F062 agree.
- Brand hue and light/dark are live levers on every screen.

## Stack decisions worth knowing

- MUI v7 under a custom OpsHub theme is the only source of rendered UI, with MIT MUI X Charts and
  Date Pickers. TanStack Table and Virtual supply headless grid state and emit no markup. No paid
  grid package, no licence key, no second UI library.
- Typography is Plus Jakarta Sans with JetBrains Mono for numerics.
- One data access class per object type in `crates/persistence/src/<aggregate>/`. All SQL lives in
  that crate. The base contract applies the tenant predicate, soft-delete filter, version check,
  audit row and outbox enqueue, so a repository cannot forget them.

## Gates

Run from the repository root; all pass on a clean clone.

```text
CARGO_TARGET_DIR=/tmp/opshub-xtask-target cargo run --quiet --manifest-path automation/xtask/Cargo.toml -- validate-decisions
CARGO_TARGET_DIR=/tmp/opshub-xtask-target cargo run --quiet --manifest-path automation/xtask/Cargo.toml -- validate-plan
CARGO_TARGET_DIR=/tmp/opshub-xtask-target cargo run --quiet --manifest-path automation/xtask/Cargo.toml -- validate-work
CARGO_TARGET_DIR=/tmp/opshub-xtask-target cargo run --quiet --manifest-path automation/xtask/Cargo.toml -- check-contracts
CARGO_TARGET_DIR=/tmp/opshub-xtask-target cargo run --quiet --manifest-path automation/xtask/Cargo.toml -- check-persistence
CARGO_TARGET_DIR=/tmp/opshub-xtask-target cargo run --quiet --manifest-path automation/xtask/Cargo.toml -- test-all
CARGO_TARGET_DIR=/tmp/opshub-xtask-target cargo run --quiet --manifest-path automation/xtask/Cargo.toml -- self-test
```

Verify by running them; do not trust this line. An earlier handoff claimed all gates passed while two
were failing.

## Gate notes

- `check-contracts` is bidirectional: a catalog route missing from its ticket fails, and so does a
  route a ticket names that no catalog row declares. The second direction exists because F013 once
  promised a public share link nothing would have served.
- `check-persistence` reads DDL lines only. Prose of the form "`x` replaces `y text[]`" is a
  deliberate record of a conversion and is not a finding.
- `validate-work` inspects files that exist; a plan row whose file was never created is caught only
  by `validate-plan`. Run both.
- Each ticket names its catalog aggregate backticked; rewriting a ticket without that line fails
  `check-contracts`.
- `CATCH_ALL_EXEMPT` in `automation/xtask/src/content.rs` lists the non-module roots that may be
  owned directly. The content self-test pins it: adding a source root there fails `self-test`.
- The forbidden-token scanner rejects the design canvas URL, so it lives in `docs/design-canvas.md`,
  the one exempt file.

## Rules to preserve

- Every file is 500 lines or fewer.
- One feature per ticket; testing code under `testing/`, feature gated, outside live code.
- Never weaken the commit, push, ownership, dependency or policy gates to make a change land.
- Do not claim implementation from a green harness manifest.

## Next session

```text
git status --short && sed -n '1,120p' "$(ls | grep -i '^cla.*\.md$')" && sed -n '1,80p' docs/milestones/README.md
```

Start at M0 or M1 in `docs/milestones/README.md`, take the lowest-order feature in `work/plan.md`
whose dependencies are archived, claim its branch and owned paths, write the failing tests in
`testing/features/F###/`, then implement the vertical slice.
