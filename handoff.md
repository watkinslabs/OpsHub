# OpsHub handoff

Status: READY FOR IMPLEMENTATION. Specification, architecture and design are complete and
mechanically checked. No product code exists yet — the repository is 1,337 files of specification,
design and gate tooling.

Every number below was measured, not remembered. Verify anything you are about to rely on; an
earlier version of this file claimed all gates passed while two were failing.

## Read these first, in this order

1. The repository rules file at the root — sources of truth, gates, how to write a ticket, change control.
2. `docs/architecture-decisions.md` — frozen. Sections 2 and 2.1 (normalization, one data access class) constrain nearly every ticket.
3. `docs/milestones/README.md` — M0 through M7 and their exit criteria.
4. `order.html` — open it from disk. The build order, the long pole, and every feature's dependencies.
5. The ticket you are about to build.

## Current state

- Root `/home/nd/ent/OpsHub`; remote `github.com/watkinslabs/OpsHub` (public, MIT).
- Rust 2024 / Axum / Tokio / SQLx / PostgreSQL 18; React 19 + TypeScript + Vite; NATS JetStream; MinIO.
- 9 epics, 73 feature tickets, 146 stories, 292 tasks, 73 feature-gated harnesses of seven lanes
  (`api`, `database`, `frontend`, `e2e`, `accessibility`, `performance`, `requirements`).
- 8 milestones, 519 estimate points, 15 dependency waves, 150 dependency edges, acyclic.
- The catalog declares 495 routes, 251 events and 381 tables, each table owned by exactly one feature.
- 62 design artboards in `design/artboards/`, one canvas, indexed by `design/canvas.json`.

## What "complete" means here, and what it does not

**Checked mechanically.** All 70 tickets with a surface define their request and response shapes and
a signature per use case (`check-completeness`). Every route in a ticket has a catalog row and every
catalog row has a route, matched on method and path (`check-contracts`). Every table has exactly one
owning repository (`check-persistence`). Every `FR-`/`NFR-`/`SR-` citation resolves (`check-references`,
7,848 of them). Every role is defined (`check-roles`). Every screen a ticket names exists
(`check-design`). Every filtering feature declares its subset of one operator vocabulary
(`check-filters`).

**Not checked, and worth knowing.** No line of product code has been written or compiled. No
migration has run. The estimates are estimates. The specification is internally consistent, which is
not the same as correct — the first feature you build will find things it got wrong. When it does,
that is an amendment, not a silent edit; see change control below.

## Sources of truth

One subject, one owner. When two disagree the owner wins and the other is corrected — never both
edited to meet in the middle. The full table is in the repository rules file. The ones people trip on:

| Subject | Owner |
|---|---|
| Routes, events, tables, aggregates, roles per feature | `docs/capability-contracts.md` |
| Permission catalogue, principal kinds, role definitions | `docs/authorization-model.md` |
| Filter operators, the value each takes, relative dates | `docs/filter-vocabulary.md` |
| Who consumes which event | `docs/event-map.md` |
| How code is written and styled | `docs/engineering-standards.md` |
| `Page<T>`, the error body, the status codes | ticket F028 |
| `CellValue`, `ColumnType`, `ColumnSettings` | ticket F007 |
| `FilterNode` | ticket F013 |
| `ActorContext` | ticket F038 |
| The `Repository` trait, `UnitOfWork`, cursor encoding | ticket F068 |
| Design tokens and component contracts | ticket F062 |
| Screens | `design/artboards/*.dc.html` |

## Change control

No implementation without a ticket. A discovery is an amendment or a new ticket, never a silent
edit, and it lands in the same pull request as the code. Amendments are recorded in the ticket's
`## 7.1 Amendments` table, and linkage runs both ways: a change crossing a contract boundary amends
both sides. The catalog moves first. Nothing is "temporary".

This is not bureaucracy for its own sake. The backlog is currently the only description of the
product that exists; the moment code and tickets diverge, neither is trustworthy.

## Gates

Eleven run on every commit and push — `audit-staged`, `validate-plan`, `validate-work`,
`check-contracts`, `check-persistence`, `check-roles`, `check-design`, `check-references`,
`check-order`, `check-filters`, `check-completeness` — wired into `.githooks/pre-commit`,
`.githooks/pre-push`, `.github/workflows/gates.yml` and FR-F001-07. Install them with
`cargo xtask install-hooks`. Four more are run on demand: `validate-decisions`, `validate-tickets`,
`check-migrations`, `check-ownership`, plus `self-test`, which tests the gates themselves.

All fifteen pass on this commit. Run them yourself:

```text
export CARGO_TARGET_DIR=/tmp/opshub-xtask-target
X="cargo run --quiet --manifest-path automation/xtask/Cargo.toml --"
for c in validate-decisions validate-plan validate-tickets validate-work \
         check-contracts check-migrations check-persistence check-roles \
         check-design check-references check-order check-filters \
         check-completeness check-ownership self-test; do echo "== $c"; $X $c; done
```

Never weaken a gate to make a change land. `--no-verify` is not an option. Every gate here exists
because something got through: `check-contracts` became bidirectional after a ticket promised a
public route no catalog row declared, and method-aware after a `POST` passed against a declared
`GET`; `check-filters` exists because ten features had each invented their own spelling of the same
operators.

### Gate notes

- `check-persistence` reads DDL lines only. Prose of the form "`x` replaces `y text[]`" records a
  conversion and is not a finding.
- `validate-work` inspects files that exist; a plan row whose file was never created is caught only
  by `validate-plan`. Run both.
- Section 1 of every ticket must carry an `Aggregate` line naming the aggregate its catalog row declares.
- `CATCH_ALL_EXEMPT` in `automation/xtask/src/content.rs` lists the non-module roots that may be
  owned directly; the content self-test pins it.
- The forbidden-token scanner rejects assistant-attribution tokens anywhere in a commit message, PR
  body or tracked file. It also rejects the design canvas URL, so that lives in the one exempt file,
  `docs/design-canvas.md`. Commit messages carry no assistant attribution.
- `check-order` holds both `docs/build-order.md` and `order.html` to the order derived from the
  tickets. Regenerate with `cargo xtask build-order` and `cargo xtask build-order --html > order.html`.

## Stack decisions worth knowing

- MUI v7 under a custom theme is the only source of rendered UI, with MIT MUI X Charts and Date
  Pickers. TanStack Table and Virtual supply headless grid state and emit no markup. **No paid grid
  package, no licence key, no second UI library** — this was decided after three reversals; do not
  reopen it without a reason the earlier rounds did not cover.
- Plus Jakarta Sans with JetBrains Mono for numerics. Brand hue derives through `color-mix(in oklch)`
  from `--brand`; light and dark are at parity.
- Navigation is a 56px masthead, a fixed 72px icon rail, and one 236px section nav. Never two wide
  sidebars (FR-F062-12).
- One data access class per object type in `crates/persistence/src/<module>/`. All SQL lives in that
  crate. The base contract applies the tenant predicate, soft-delete filter, version check, audit row
  and outbox enqueue, so a repository cannot forget them.
- Transactional outbox, idempotency keys, optimistic concurrency by `If-Match`, signed cursors,
  expand-migrate-contract schema staging.

## Where to start

`order.html` answers this precisely, but in short: **F041 → F042 → F001**, then wave 3 opens up.

The long pole is 15 features and 112 of 519 points:

```text
F041 → F042 → F001 → F002 → F038 → F003 → F005 → F006 → F007 → F009 → F035 → F018 → F019 → F020 → F032
```

Nothing off that chain shortens the build. Anything in the same wave can be built in parallel.

For each feature: take the lowest-order ticket whose dependencies are archived, claim its branch and
`owned_paths`, write the failing tests in `testing/features/F###/` first, then implement the vertical
slice, then archive with harness evidence under `testing/evidence/F###/`.

## Known open items

Carried deliberately, not forgotten:

- **F027 `RecordKind` does not cover four of F070's trash kinds.** `view`, `folder`, `report` and
  `dashboard` have no retention policy row, so they currently keep forever. Needs a joint amendment
  to F027 and F070 if they should expire — a product decision, not a technical one.
- **F024 has no route to create a chart outside a dashboard.** Consistent with FR-F024-04 and
  documented as deliberate, but an ad-hoc saved chart has no path today.
- **Four values chosen rather than derived**, each flagged in its ticket: F015's manifest key
  grammar, F055's `row_version` projection, F064's credit-balance derivations, F046's WebSocket
  `1000` close code.
- **Legal and commercial documents are deliberately unwritten** — SLA numbers, ToS, DPA,
  subprocessor list, SOC 2 scope. These need the owner and counsel, not an engineer.

## Rules to preserve

- Every file is 500 lines or fewer, including the gate tooling itself.
- One feature per ticket. Test code lives under `testing/`, feature gated, outside live code.
- Never weaken the commit, push, ownership, dependency or policy gates to make a change land.
- Do not claim implementation from a green harness manifest. A passing harness with no product code
  is a passing harness with no product code.

## Next session

```text
cd /home/nd/ent/OpsHub && git status --short && cargo xtask validate-work && sed -n '1,80p' docs/milestones/README.md
```

Then open `order.html`, pick the first unarchived feature, and read its ticket end to end before
writing anything.
