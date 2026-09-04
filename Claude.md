# OpsHub repository rules

Canonical repository: `github.com/watkinslabs/OpsHub`.

Current backlog status: READY FOR IMPLEMENTATION. `docs/architecture-decisions.md` is the decision gate; `docs/capability-contracts.md` is the hand-maintained contract catalog (routes, events, tables, roles, module slug per feature). Do not implement or claim build-ready tickets while a ticket contains synthetic routes, aggregates, events, placeholders, or unresolved decisions; `cargo xtask validate-work` rejects them.

Read this file first. These rules apply to all work in this repository. Read `MANIFEST.md` only when a task needs deeper reference material.

## Code discipline

- Hard limit: every file is 500 lines or fewer, including code, comments, and documentation.
- Split files by function/responsibility. If a file approaches 400 lines, split it before it reaches the limit.
- Prefer small focused modules, components, services, and tests over large multipurpose files.
- Comments are limited to implementation-specific gotchas, invariants, security constraints, or non-obvious decisions required by the feature being implemented.
- Do not add verbose comments, restate code, write tutorials in source files, or add speculative documentation.
- Keep ticket and code language direct and concise. We are coding; avoid filler.
- CI must fail when the 500-line limit is exceeded.

## Work-item model

- One product feature is one complete feature ticket. Stories and tasks are child implementation specifications linked to that feature.
- Bugs and spikes are single work-item tickets with their own specifications.
- Every ticket must include requirements, scope, UX behavior, Rust/API/data design, React design, TDD plan, test harness plan, acceptance criteria, entry criteria, exit criteria, and release notes.
- Use the templates in `work/templates/`.
- Every ticket starts with valid YAML front matter. Treat it as machine-readable control data, not prose.
- The ticket is the source of truth for requirements, scope, tests, ownership, dependencies, and handoff.
- Before editing, inspect current code, ticket, dependencies, and contracts. Plans and prior handoffs are not proof.
- Do not create duplicate registries, shadow state, fallback paths, or parallel sources of truth.

## Ticket locations and movement

- New and planned tickets live in `work/tickets/`.
- Active tickets live in `work/inprogress/`.
- Released or permanently closed tickets live in `work/archived/`.
- Move the same file; never copy or rename it during lifecycle movement.
- Record `started_at` when moving a ticket into `inprogress/`.
- Record `finished_at` only after exit criteria pass and immediately before moving it into `archived/`.
- Do not delete archived tickets.

## Metadata and ownership

- Required metadata: `id`, `type`, `status`, `priority`, `owner`, `estimate`, `target_milestone`, `parent_epic`, `depends_on`, `blocks`, `conflicts_with`, `parallel_safe`, `owned_paths`, `feature_flag`, `flag_default`, `started_at`, and `finished_at`.
- Agents may edit only `owned_paths` declared by their ticket. Owned paths are module-scoped globs (`services/api/src/<module>/**`, `services/api/migrations/*_<module>_*.sql`); catch-alls such as `services/api/**` are invalid.
- One active agent owns one ticket. Never modify another active ticket's files.
- Unresolved dependencies, conflicts, or ambiguous requirements block implementation.
- Use `cargo xtask validate-tickets` before review and in CI.
- Use `cargo xtask validate-work` after scaffolding and before fanout.
- Use `cargo xtask validate-decisions` before scaffolding or implementation.
- Use `cargo xtask scaffold-plan` only to create missing skeleton files for new plan rows; it never overwrites. Every backlog file is hand-written against the spec, decisions, and contract catalog, and `validate-work` enforces content rules: no placeholders, 8+ FR and 4+ NFR per feature, 5+ SR per story, named failing tests, gherkin scenarios, catalog routes/events/tables reproduced, `depends_on` equal to the plan column, disjoint module-scoped `owned_paths`, and feature-specific harness cases.
- Claim the ticket before editing. One ticket, one owner, one branch, one worktree.
- Agents may not modify another active ticket's files.

## IDs and branch names

IDs use one uppercase type letter and three digits, with no dash: `E001`, `F001`, `S001`, `T001`, `B001`, `P001`, `D001`, `M001`.

Branches use the lowercase type letter, the same three digits, one dash, and a short kebab-case description:

| Work item | ID | Branch |
|---|---|---|
| Feature | `F001` | `f001-create-workspace` |
| Story | `S001` | `s001-workspace-api` |
| Task | `T001` | `t001-workspace-migration` |
| Bug | `B001` | `b001-fix-row-permission` |
| Spike | `P001` | `p001-evaluate-formula-engine` |
| Epic | `E001` | `e001-work-management` |
| Decision | `D001` | `d001-api-versioning` |
| Milestone | `M001` | `m001-foundation` |

Rules:

- The branch prefix must match the work-item type.
- There is no dash after the letter: use `f001`, never `f-001`.
- Use lowercase ASCII and kebab case after the numeric ID.
- Do not include status, date, username, issue-provider prefix, or random abbreviations.
- Branch descriptions are short, imperative, and stable.

## TDD and testing

- Write requirement IDs and executable acceptance tests before production implementation.
- All test code, harnesses, fixtures, deterministic seed data, mocks, E2E suites, accessibility checks, and performance suites belong under root `testing/`—not in live application feature code.
- Each feature suite must be independently feature-gated for fast fanout testing and must also support a full-suite mode.
- Every ticket must document targeted and full commands, the feature flag, fixture isolation, and CI evidence.
- Do not mark a ticket accepted until unit, API, database, frontend, E2E, permission-negative, accessibility, and applicable performance gates pass.
- Test files follow the same 500-line limit and must be split by feature behavior or harness responsibility.
- Tests must be deterministic, order-independent, timezone-controlled, and safe to run in parallel.
- Use isolated tenant/database/worker fixtures and mocks for external services.
- Each feature suite must run independently and all suites must have a full-suite mode.
- Every new gate or test needs a positive control: known defect → RED → restore → GREEN.

## Rust backend rules

`docs/engineering-standards.md` is the full standard and is binding. In particular:

- **No SQL, pool or connection outside `crates/persistence`.** The domain depends on repository
  traits; the base contract owns the tenant predicate, soft-delete filter, version check, audit row
  and outbox enqueue, so a repository never re-implements them.
- **No `unwrap`, `expect` or `panic!` on a request or job path.**
- **Typed domain errors** with exactly one mapping per module onto `invalid`, `denied`, `not_found`,
  `conflict`, `rate_limited`, `unavailable`. No handler invents a status code.
- Every request and job runs in a tracing span carrying `tenant_id`, `actor_id`, `correlation_id` and
  the entity id.
- Use Rust 2024 stable, Axum/Tokio, SQLx, PostgreSQL, typed domain errors, migrations, tracing, and versioned OpenAPI contracts.
- Enforce tenant isolation and authorization at service/API boundaries.
- Use idempotency and optimistic concurrency for mutating operations.
- Add unit and integration tests with every behavior change.
- Define OpenAPI, event, and database contracts before fanout implementation.
- Every migration needs forward compatibility, rollback/backfill strategy, indexes, constraints, and large-table impact notes.

## Diagnosis and evidence

- Do not ship workarounds. State the cause before changing behavior.
- Report direct evidence: file, call path, command, and result.
- A feature is incomplete until production code consumes it and an integration test proves that path.
- Gate skips require a named gate, reason, linked ticket, approver, and removal plan. Never blanket-skip.

## Fanout

- Fan out only when dependencies, conflicts, and owned paths permit it.
- Each lane gets its own worktree, build/cache directory, test database or tenant, and artifact path.
- Delegated agents have no merge authority unless explicitly assigned as integration owner.

## React frontend rules

`docs/engineering-standards.md` is the full standard and is binding. The rules that get broken most:

- **Tokens are the only source of visual values.** No hex, `rgb()`, raw `px` for spacing or type, or
  raw `ms` anywhere under `apps/web/src/**`. No stylesheet outside `apps/web/src/design/`.
- **One import surface.** Features import from `apps/web/src/ui`, never `@mui/material`, `@mui/x-*`,
  `@tanstack/*` or an icon package directly, and never redefine a component the library exports.
- **Variants are enumerated, not composed.** A button is one of the declared variants and sizes; a
  feature that wants a new one opens a ticket against F062 rather than passing `sx` to invent it.
  `className` is for layout only — never colour, typography, border or shadow.
- **Icons come from `apps/web/src/ui/icons.ts`**, the only module allowed to import the icon package,
  at 14, 16, 20 or 24px. Decorative icons are `aria-hidden`; meaningful ones require `title`. Never
  emoji as functional UI.
- **Every surface ships loading, empty, error with `correlation_id`, denied, stale, offline and
  success states**, composed from the F062 patterns rather than hand-rolled.
- Keyboard operability, visible `:focus-visible`, screen-reader semantics, responsive behaviour and
  WCAG 2.2 AA are gates, and colour is never the only signal.

## Feature flags

- Unreleased functionality must be behind the ticket's feature flag and default off.
- Targeted and full test commands must explicitly enable the relevant flags.
- Every flag needs an owner, rollout state, disable procedure, and cleanup ticket.

## Agent handoff

Every handoff records: implemented summary, files changed, commands/results, known issues, follow-up tickets, migration status, and rollback procedure.

## Protected changes

Human approval is mandatory for authorization, tenant isolation, migrations, deletion, production configuration, security, billing, external integrations, generated contracts, and AI actions that write or send data.

## Architecture decisions

Create a decision record before adding a service/library or changing auth, data, events, integrations, or shared UI patterns. Link the decision from affected tickets.

## Completion rule

Before implementation starts, a ticket must meet entry criteria. Before release, it must meet every exit criterion, have test evidence and a rollback plan, record `finished_at`, and move to `work/archived/`.

## Sources of truth

Each of these owns exactly one thing. When two disagree, the one listed here wins for its own subject
and the other is corrected — never both edited to meet in the middle.

| Subject | Source of truth |
|---|---|
| Architecture and data-model rules | `docs/architecture-decisions.md` |
| Product requirements | `docs/product-capability-spec.md` |
| Routes, events, tables, aggregates, module slugs, roles per feature | `docs/capability-contracts.md` |
| Permission catalogue, principal kinds, role definitions | `docs/authorization-model.md` |
| What a milestone contains and when it is done | `docs/milestones/README.md` |
| Threats, trust boundaries and their mitigations | `docs/threat-model.md` |
| How code is written and styled | `docs/engineering-standards.md` |
| What each plan includes | `docs/packaging.md` |
| Screens | `design/artboards/*.dc.html`, indexed by `design/canvas.json` |
| Feature contract, scope, tests, ownership | its ticket in `work/` |
| Which items exist and their dependencies | `work/plan.md` |

The ticket is the contract and the artboard is the picture: when they disagree the ticket wins and
the artboard is corrected.

## Gates

Run before review and in CI. Each exists because something was wrong that a human review missed.

| Command | Enforces |
|---|---|
| `validate-decisions` | The decision record parses and carries no unresolved language |
| `validate-plan` | Every plan row has a file and every file has a plan row. `validate-work` cannot see a row whose file was never created, so both must run |
| `validate-work` | Content quality: no placeholders, minimum requirement counts, gherkin scenarios, named failing tests, disjoint module-scoped owned paths, harness lanes |
| `check-contracts` | Catalog and tickets agree **in both directions**: a catalog route missing from its ticket fails, and so does a route a ticket names that no row declares |
| `check-persistence` | Third normal form, no array columns, justified `jsonb`, one repository class per table-owning feature |
| `check-roles` | Every role a ticket or catalog row authorizes against is defined in the authorization model |
| `check-design` | Every ticket names an artboard that exists in `design/artboards/`, or states plainly that it has no user surface |
| `check-migrations` | Migration naming, ordering, reversibility and safety |
| `test-all`, `test-feature` | Every feature harness is present and valid |
| `self-test` | The gates' own positive controls, including that a source-tree root cannot be added to the catch-all exemption |

## Writing a ticket

Beyond the template, these are the rules that have actually been violated:

- **Name the aggregate.** Section 1 carries an `- Aggregate: \`<name>\`` line matching the catalog row.
  Rewriting a ticket without it fails `check-contracts`.
- **Reproduce every catalog route, event and table** verbatim in section 4, and invent none. A route
  you need that the catalog lacks is a catalog change first, in the same commit.
- **Normalize.** No array column. An enumerable set is a child table with a foreign key and its own
  indexes. `jsonb` only for genuinely schema-less payloads — cell values, event payloads, authored
  ASTs, provider snapshots, diffs — never for something the product filters, joins, sorts or
  constrains on, and say in the ticket why a kept one is a payload.
- **Name the data access class.** One `<Aggregate>Repository` per object type in
  `crates/persistence/src/<module>/`, and state that the use cases contain no SQL. No handler, job or
  test opens a connection.
- **Authorize against the model.** Use a role that `docs/authorization-model.md` defines. Needing a
  new one means adding it there first, with what it inherits and what it adds.
- **Own your paths.** `owned_paths` are module-scoped globs including
  `crates/persistence/src/<module>/**` when the feature owns tables, disjoint from every other
  feature, and every story and task path is a subset of its parent's.
- **Reference the design.** Section 3 names the artboard in `design/artboards/`, or says plainly that
  the feature has no user surface.
- **Do not restate a gate's own denylist.** A ticket that enumerates the forbidden markers, or quotes
  an undeclared example route, fails the gate it is describing. Reference the constant or the rule
  instead. This has now happened four times.
- **Two features never write the same table.** Child tables belong to their parent's repository.

## Milestones

Every ticket declares a `target_milestone`. A feature may not depend on one in a later milestone —
the dependency graph must be acyclic and forward-only. `docs/milestones/README.md` defines each
milestone's contents and exit criteria and is generated from the tickets, so scope cannot drift.

## Navigation

Required files are `Claude.md`, `MANIFEST.md`, `docs/product-capability-spec.md`, `work/plan.md`, the matching template, and the current item. Do not open unrelated documentation.

## Mandatory attribution policy gate

- Install hooks with `cargo run --manifest-path automation/xtask/Cargo.toml -- install-hooks`.
- `.githooks/pre-commit` audits staged content.
- `.githooks/commit-msg` audits the commit subject/body.
- `.githooks/pre-push` audits pushed commit history.
- CI/PR automation must run `audit-pr TITLE_FILE BODY_FILE` before merge.
- The gate rejects the configured provider/assistant attribution tokens case-insensitively and returns nonzero. No commit, push, or merge may bypass it.
- Only the policy files and enforcement implementation are excluded from content scanning. Commit and PR text have no exemption.
