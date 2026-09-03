# OpsHub feature-ticket system

One product feature equals one complete feature ticket specification. Stories and tasks are child implementation specifications. Bugs and spikes are independent work items.

## Folders

```text
work/tickets/       # planned feature/bug/spike tickets
work/epics/         # epic context
work/stories/       # vertical slices
work/tasks/         # implementation units
work/inprogress/    # active items
work/archived/      # released or permanently closed
```

Move the same file between folders; never duplicate it.

## IDs, files, and branches

IDs are immutable, use a letter plus three digits, and are never reused. The letter identifies the work-item type:

| Type | ID format | Branch format | Example file |
|---|---|---|---|
| Feature | `F###` | `f###-description` | `F001-create-workspace.md` |
| Bug | `B###` | `b###-description` | `B001-fix-row-permission.md` |
| Spike | `P###` | `p###-description` | `P001-evaluate-formula-engine.md` |
| Epic context | `E###` | `e###-description` | `E001-work-management.md` |
| Decision | `D###` | `d###-description` | `D001-api-versioning.md` |
| Milestone | `M###` | `m###-description` | `M001-foundation.md` |

```text
File:   F001-create-workspace.md
Branch: f001-create-workspace
```

Convention: `<lowercase type letter><three-digit number>-<kebab-case-description>`. There is no dash between the type letter and number. Use lowercase ASCII, no spaces, dates, usernames, or status words. A branch must use the same numeric ID as its ticket.

Hierarchy is `Epic → Feature ticket → Story → Task`. Planned and active items use their corresponding `work/` folder; completed items move to `work/archived/`.

## Lifecycle

```text
tickets/ → inprogress/ → archived/
planned    in_progress   released
ready      in_review     cancelled
```

Set `started_at` when moving to `inprogress/`. Set `finished_at` only when accepted and moving to `archived/`.

## TDD and fast fanout

Every ticket is test-first: write requirements and executable acceptance scenarios, add failing tests to the appropriate harness, implement, refactor, and run the required matrix. Harnesses, fixtures, seed data, mocks, and parallel isolation live in the separate `testing/` area—not in live application code—and are feature-gated so teams can run targeted suites or the complete suite on demand.

Every ticket must identify Rust unit, API contract/integration, database, React component, browser E2E, permission-negative, accessibility, and performance coverage as applicable.

## Required metadata

Every ticket includes ID, type, status, priority, owner, estimate, milestone, `started_at`, `finished_at`, parent epic where applicable, capability area, dependencies, branch, requirements, acceptance criteria, test evidence, and exit criteria.

Machine-readable front matter is mandatory. It must include `depends_on`, `blocks`, `conflicts_with`, `parallel_safe`, `owned_paths`, `feature_flag`, and `flag_default`.

Agents may modify only declared `owned_paths`. A ticket with unresolved dependencies or path conflicts cannot enter `inprogress/`.

## File limits

- Every file must stay at or below 500 lines.
- Split files by function or responsibility before reaching the limit.
- Comments are only for feature-specific gotchas, invariants, security constraints, or non-obvious decisions.
- Keep ticket text concise; do not write verbose explanations.

## Engineering standards

- Rust 2024 stable, Axum/Tokio, SQLx, PostgreSQL, typed errors, migrations, tracing, OpenAPI.
- React 19 + TypeScript, Vite, semantic HTML, typed API client, responsive layouts, shared component tokens, accessible SVG icons.
- One documented font stack, tokenized color/spacing/radius/typography, no emoji as UI icons, visible focus states, WCAG 2.2 AA.
- CI gates are feature-selectable: format, lint, typecheck, unit, integration, E2E, accessibility, performance, build, and migration validation.
- Run `cargo xtask validate-tickets` in CI to validate metadata, filenames, branches, folders, dependencies, flags, timestamps, required sections, and 500-line limits.
- API and database contracts must be defined before parallel backend/frontend implementation.
- Generated files must identify their source and may only be changed by regeneration.
- Human approval is required for auth, permissions, migrations, deletion, production config, security, billing, external integrations, and AI writes.
