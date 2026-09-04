---
id: F044
type: feature
status: planned
priority: P0
owner: platform
estimate: 8
target_milestone: M0
parent_epic: E000
depends_on: [F041, F042]
blocks: []
conflicts_with: []
parallel_safe: true
owned_paths: [automation/xtask/src/release.rs, testing/evidence/**, testing/features/F044/**]
feature_flag: F044_FEATURE
flag_default: off
branch: f044-contract-release-control
started_at: null
finished_at: null
---

# F044 — Contract/release control

## 1. Identity and dates

- Branch: `f044-contract-release-control`
- Capability area: developer workflow control plane (spec section 8 release gates: API contract and migration tests, feature-flag/rollback plan; spec 5.9 INT-01 versioned REST API and OpenAPI; spec section 10 flags default off; decisions section 3 OpenAPI from typed contracts, section 8 MCP schema drift fails CI, section 9 one flag per suite)
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 8, 9, 10; `docs/capability-contracts.md` row F044
- Aggregate: `release-control`
- Module slug: `xtask-release` (Rust module `automation/xtask/src/release.rs`; evidence under `testing/evidence/<ID>/**`; inputs `docs/capability-contracts.md`, `openapi/v1.json`)

- Design: this feature has no user surface; it ships tooling, runtime or contracts only.

## 2. Requirement specification

### Problem and user outcome

A feature ticket, the frozen contracts catalog, the generated OpenAPI document, the event registry, the migrations, and the feature-flag registry all describe the same feature and drift independently. Today `check-contracts` only checks that a row exists and `check-migrations` only checks that filenames contain an underscore, and nothing verifies that a feature marked done actually has passing evidence in every lane, a registered flag, and a tested rollback.

As a release manager, I want `check-contracts`, `check-migrations`, and `check-flags` to fail on any drift between tickets, catalog, OpenAPI, events, generated clients, MCP schemas, migrations, and flags, and `verify-release <ID>` to assemble and sign the evidence that a feature is releasable and reversible, so that a release decision rests on machine-checked facts rather than a checklist.

### Functional requirements

- **FR-F044-01:** `check-contracts` parses every row of the two tables in `docs/capability-contracts.md` into `ContractRow { id, aggregate, module, routes|surface, events, tables|persistence, roles }`, rejects the catalog when any row has an empty cell, a duplicate id, an event not matching `^[a-z0-9-]+\.[a-z0-9-]+\.v1$`, or a route not starting with `/api/v1`, `/auth`, `/public`, `/scim/v2`, `/mcp/v1`, `/ws/v1`, `/embed`, `/m/`, `/apps/`, `/manifest.webmanifest`, `/healthz`, `/readyz`, or `/metrics` (`contract.catalog`), and requires exactly one row per feature ticket id (`contract.row_missing`, `contract.row_orphan`).
- **FR-F044-02:** For every feature ticket, every route and every event in its catalog row must appear verbatim (backticked) inside `## 4. Technical specification` (`contract.route_missing_in_ticket`, `contract.event_missing_in_ticket`), and every backticked string in that section that looks like a route (`^(GET|POST|PUT|PATCH|DELETE) /` or starts with `/api/v1`) or an event (matches the event pattern) must be in the row (`contract.route_not_in_row`, `contract.event_not_in_row`); tooling rows compare the `Surface` commands instead of routes. The check is bidirectional: a route a ticket names that no catalog row declares is `contract.route_undeclared`, because nothing generates a handler or an OpenAPI path for it — F013 promised a public view-share link for weeks with no row behind it, which is the case this rule exists for. The example path is deliberately not reproduced here, since this ticket is itself scanned. A ticket may name a base path or a deeper path under a declared route; only an unrelated path is a finding.
- **FR-F044-03:** A feature's `owned_paths` must contain the module-slug globs implied by its row (`crates/domain/src/<m>/**`, `services/api/src/<m>/**`, `apps/web/src/features/<m>/**`, `services/api/migrations/*_<m>_*.sql` for product rows; the listed real paths for tooling rows) and `testing/features/<id>/**` (`contract.paths_mismatch`), and the ticket must link `docs/architecture-decisions.md` and cite its row (`contract.decision_link`).
- **FR-F044-04:** When `openapi/v1.json` exists, every route in a product row must exist as `paths[<path>][<method>]` with an `operationId` of the form `<module>_<verb>` and the `x-opshub-feature: <id>` extension, and every operation in the document must map back to a catalog row or carry `x-opshub-internal: true` (`openapi.route_missing`, `openapi.orphan_operation`, `openapi.feature_mismatch`); path templates are compared after normalising `{id}` parameter names.
- **FR-F044-05:** When `crates/events/src/registry.rs` exists, the set of `EventName` constants must equal the union of catalog events (`events.registry_missing`, `events.registry_orphan`), and each event's payload struct must contain the fields `tenant_id, actor_id, aggregate_id, version, changed_fields, correlation_id, occurred_at` (`events.payload_shape`).
- **FR-F044-06:** When `apps/web/src/api/generated/manifest.json` exists, its `openapi_sha256` must equal the SHA-256 of `openapi/v1.json` (`client.stale`); when `services/mcp/schemas/manifest.json` exists, its `contracts_sha256` must equal the SHA-256 of `docs/capability-contracts.md` and its tool list must cover every product row's aggregate (`mcp.schema_stale`, `mcp.tool_missing`).
- **FR-F044-07:** `check-migrations` requires every file in `services/api/migrations/` to match `^(\d{14})_([a-z0-9-]+)_([a-z0-9_]+)\.(up|down)\.sql$`, every `up` to have a `down` with the same stem, the module segment to belong to a catalog row whose feature owns `services/api/migrations/*_<module>_*.sql`, and a header comment on line 1 `-- opshub: feature=<id> module=<m> reversible=true|false destructive=none|<statement list>` (`migration.name`, `migration.down_missing`, `migration.module_not_owned`, `migration.header`).
- **FR-F044-08:** Migration ordering: timestamps are strictly increasing and unique; on a branch, no new migration may carry a timestamp older than the newest migration reachable from `origin/main` (`migration.order`); a migration file present on `origin/main` must be byte-identical on the branch (`migration.mutated`).
- **FR-F044-09:** Migration safety: an `up` file containing `DROP TABLE`, `DROP COLUMN`, `ALTER COLUMN .* TYPE`, `TRUNCATE`, `ADD COLUMN .* NOT NULL` without `DEFAULT`, or `CREATE (UNIQUE )?INDEX` without `CONCURRENTLY` on a table that exists in an earlier migration is `migration.destructive` unless the header's `destructive=` list names that exact statement kind and the ticket's section 4 contains an `Expand/contract:` bullet; `down` files must not be empty and must reference every object the `up` creates (`migration.down_incomplete`).
- **FR-F044-10:** `check-flags` reads the flag registry `crates/contracts/src/feature_flags.rs` (`pub const FLAGS: &[FlagDef { key, feature, default: FlagDefault::Off, state: FlagState::{Planned, Active, Graduated, Removed}, introduced: &str }]`) when it exists, and requires: every feature ticket's `feature_flag` equals `<id>_FEATURE` with `flag_default: off`; every feature in `work/inprogress` or `work/archived` has a registry entry; every registry entry has a ticket; `testing/features/<id>/feature.toml` `flag` matches; every `cfg(feature = "…_FEATURE")`, `flags.enabled("…")`, and `useFlag('…')` reference in `crates/`, `services/`, and `apps/` names a registered flag (`flag.unregistered`, `flag.missing_ticket`, `flag.harness_mismatch`, `flag.unknown_reference`).
- **FR-F044-11:** Flag lifecycle: a flag is `Planned` while its ticket is planned, `Active` while in progress or archived within the current milestone, `Graduated` when the feature's epic milestone is complete (default may become on only then), and `Removed` after the next milestone; `check-flags` reports `flag.stale` for an archived feature still `Active` two milestones later, `flag.premature_default` for any `Graduated` flag whose feature is not archived, and `flag.removed_reference` for any code reference to a `Removed` flag.
- **FR-F044-12:** `verify-release <ID>` for a feature id requires: the ticket in `work/archived` with `status: done` and `finished_at`; both stories and all four tasks archived; `testing/evidence/<ID>/manifest.json` (F043) present with lanes `requirements, api, database, frontend, e2e, accessibility, performance` each `pass`, or `missing` only when listed in `feature.toml` `lanes_not_applicable` with a reason; `check-contracts`, `check-migrations`, and `check-flags` passing; `testing/evidence/<ID>/rollback.json` with `{ flag_off_verified: true, migration_down_verified: true|"not_applicable", commands: [...], commit }`; and a non-empty `## 10. Release notes` section (`release.not_archived`, `release.child_open`, `release.lane_missing`, `release.lane_failed`, `release.gate_failed`, `release.rollback_missing`, `release.notes_missing`).
- **FR-F044-13:** On success `verify-release` writes `testing/evidence/<ID>/release.json` `{ id, verified_at, verifier, head_commit, inputs: [{ path, sha256 }], gates: { contracts, migrations, flags }, lanes: {...}, rollback: {...}, signature }` where `signature` is the SHA-256 over the sorted input hashes, and prints `release verified <ID> <signature>`; a second run on unchanged inputs produces the same `signature`.
- **FR-F044-14:** `verify-release` writes `release.json` only when `XTASK_ROLE=release-manager` is set (recorded as `verifier` with `XTASK_OWNER`) or when running in CI on `main` (`GITHUB_ACTIONS=true` and `GITHUB_REF=refs/heads/main`); otherwise it runs every check, prints `dry run: release-manager role required to record`, and exits 3 `release.role_required` without writing.
- **FR-F044-15:** `verify-release --milestone M1` verifies every feature whose `target_milestone` is `M1` and writes `testing/evidence/milestones/M1.json` listing each feature's signature; any failing feature fails the milestone with all findings listed.
- **FR-F044-16:** All four commands support `--json`, the shared exit codes (0/1/2/3), and run in `.githooks/pre-commit`, `pre-push`, and `gates.yml` (`check-contracts`, `check-migrations`; `check-flags` is added to `gates.yml` by F001 once the registry exists).

### Non-functional requirements

- **NFR-F044-01 Performance:** `check-contracts` over 61 tickets, a 2 MiB OpenAPI document, and 500 migrations completes in under 3 s; `verify-release` for one feature under 5 s; `--milestone` for 10 features under 30 s on `ubuntu-latest`.
- **NFR-F044-02 Security/privacy:** the commands read only repository files and `git` metadata, never execute SQL or migrations (safety is static analysis), never write outside `testing/evidence/`, and the release signature is a content hash, not a secret; `verifier` records only an email.
- **NFR-F044-03 Accessibility:** output follows the F041 text and JSON rules; drift findings show the expected and actual values side by side in plain text (`expected: sheet.created.v1, found: sheet.create.v1`).
- **NFR-F044-04 Reliability/observability:** every finding names the exact file, line, and the two artifacts that disagree; `release.json` and `M#.json` are deterministic apart from `verified_at` and `head_commit`; a partial write is impossible (temp file plus rename).

### Scope

Included: catalog parsing and validation, ticket-to-catalog route and event drift, owned-path and decision-link checks, OpenAPI, event registry, generated client, and MCP schema drift, migration naming, pairing, ownership, header, ordering, immutability, destructive-statement and down-completeness checks, flag registry and lifecycle checks, per-feature and per-milestone release verification with rollback evidence and signatures.

Excluded: generating OpenAPI, clients, or MCP schemas (F028, F047), running migrations against a database (feature harnesses and F004), the flag runtime and admin API (F048), collecting the lane evidence itself (F043), and the CI workflow file (F001).

## 3. UX specification

No UI. The surface is the command line.

- Entry points: `cargo xtask check-contracts [--json]`, `check-migrations [--json] [--base REF]`, `check-flags [--json]`, `verify-release <ID> [--json]`, `verify-release --milestone M# [--json]`; hooks `pre-commit` and `pre-push`; CI `gates.yml`.
- Primary flow: a release manager runs `XTASK_ROLE=release-manager cargo xtask verify-release F006`, sees each gate line (`contracts: pass`, `migrations: pass (4 files)`, `flags: pass`, `lanes: 7/7 pass`, `rollback: verified at 3f9c2e1`), then `release verified F006 9b1c…`, and finds `testing/evidence/F006/release.json`.
- Success: gate lines plus the verified line, exit 0. Findings: `BLOCKED:` lines with expected/found pairs, exit 1. Refused: `REFUSED: release.role_required` after a full dry run, exit 3. Error: I/O or git failure text, exit 2. Empty: no OpenAPI, registry, client, or MCP manifest present → those checks print `skipped: <path> absent` and pass, so E000 can run before any product code exists.
- Denied: `verify-release` without the role never writes; a milestone run lists every failing feature before exiting.
- Keyboard/screen reader: line-oriented, no prompts. Responsive/tokens/icons: not applicable.

## 4. Technical specification

Canonical contract: aggregate `release-control`; module `xtask-release`; surface `cargo xtask check-contracts`, `check-migrations`, `check-flags`, `verify-release <ID>`; events none; persistence `testing/evidence/<ID>/**`, `docs/capability-contracts.md`, `openapi/v1.json`; role release-manager. Decision link: `docs/architecture-decisions.md` sections 3, 8, 9, and 10.

### Rust backend

- `release.rs` types: `struct ContractRow { id: ItemId, aggregate: String, module: String, routes: Vec<Route>, surface: Vec<String>, events: Vec<EventName>, persistence: Vec<String>, roles: Vec<String>, tooling: bool }`, `struct Route { method: Option<Method>, path: String }`, `struct EventName(String)`, `struct Catalog { rows: BTreeMap<ItemId, ContractRow> }`, `struct OpenApiDoc { operations: Vec<Operation { method, path, operation_id, feature: Option<ItemId>, internal: bool }> }`, `struct Migration { path, timestamp: u64, module, name, direction: Up|Down, header: MigrationHeader, statements: Vec<StatementKind> }`, `struct MigrationHeader { feature, module, reversible: bool, destructive: Vec<StatementKind> }`, `struct FlagDef { key, feature, default: FlagDefault, state: FlagState, introduced }`, `struct ReleaseRecord { id, verified_at, verifier, head_commit, inputs: Vec<InputHash>, gates: Gates, lanes: BTreeMap<String, EvidenceStatus>, rollback: RollbackEvidence, signature }`, `struct RollbackEvidence { flag_off_verified: bool, migration_down_verified: MigrationDown, commands: Vec<String>, commit: String }`.
- Use-case functions: `release::parse_catalog(text) -> Result<Catalog, Vec<Finding>>`, `release::check_ticket_against_row(&WorkItem, &ContractRow) -> Vec<Finding>`, `release::check_openapi(&Catalog, &OpenApiDoc)`, `check_event_registry(&Catalog, &str)`, `check_generated_client(&Path, &Path)`, `check_mcp_schemas(&Path, &Path)`, `release::check_contracts()`, `release::load_migrations(dir) -> Vec<Migration>`, `check_migration_names`, `check_migration_order(&[Migration], base: &str)`, `check_migration_safety(&[Migration], &WorkGraph)`, `release::check_migrations(base)`, `release::load_flags(path)`, `check_flag_registry(&WorkGraph, &[FlagDef])`, `check_flag_references(root, &[FlagDef])`, `check_flag_lifecycle(&WorkGraph, &[FlagDef])`, `release::check_flags()`, `release::verify_release(id, role) -> Result<ReleaseRecord, Vec<Finding>>`, `verify_milestone(m, role)`, `release::test_feature(id)` and `test_all()` (moved here from `main.rs`, calling `lanes::current_lane` for environment injection).
- SQL statement classification: a small tokenizer over the `up` text (comments stripped, strings skipped) recognising `CREATE TABLE`, `ALTER TABLE … ADD COLUMN`, `DROP TABLE`, `DROP COLUMN`, `ALTER COLUMN … TYPE`, `TRUNCATE`, `CREATE INDEX`, `CREATE UNIQUE INDEX`, `CONCURRENTLY`; table existence is tracked across migrations in timestamp order.
- Error mapping: catalog parse failure → `contract.catalog` findings, exit 1; missing optional inputs → `skipped` lines, pass; git failure resolving `origin/main` → fall back to `main`, then exit 2 if neither exists; role missing → exit 3.
- Data access (decision 2.1): this feature owns no table and adds no repository; `release-control` analyses `services/api/migrations/*.sql` as text and never executes a statement or opens a database connection, so the migration gate runs with no SQLx dependency at all.
- Authorization: `release-manager` via `XTASK_ROLE` or CI on `main` (FR-F044-14); every other command is maintainer read-only.
- Finding codes: `contract.*`, `openapi.*`, `events.*`, `client.stale`, `mcp.*`, `migration.*`, `flag.*`, `release.*`.
- Telemetry: gate lines and JSON `gates` object; no events (contracts row lists none).
- Limits: catalog ≤ 200 rows; OpenAPI ≤ 16 MiB; ≤ 2,000 migrations; flag registry ≤ 500 entries; a limit breach is `io.too_large` with the limit.
- Optional inputs and their absence behaviour: `openapi/v1.json`, `crates/events/src/registry.rs`, `apps/web/src/api/generated/manifest.json`, `services/mcp/schemas/manifest.json`, `crates/contracts/src/feature_flags.rs`, `services/api/migrations/` each print `skipped: <path> absent` and pass until the owning feature creates them.
- Exit codes: 0 pass, 1 findings, 2 usage or I/O, 3 refused (`release.role_required`).

### Interface

This feature has no HTTP surface, so its interface is the command line: the arguments each command
accepts, the exit code each outcome produces, the exact text of every finding, and the JSON records
`verify-release` writes. Those four are what two implementers would otherwise build differently, and
they are fixed here. Nothing below quotes a route or an event literal, because this ticket is itself
scanned by the gate it describes.

**Command arguments.** Every command is `cargo xtask <command> [args]`. An unknown flag, a missing
required value, or a positional argument the command does not take is exit `2` with usage on stderr.

| Command | Argument | Type | Required | Constraint |
|---|---|---|---|---|
| `check-contracts` | `--json` | flag | no | switches stdout to the single JSON object below |
| `check-migrations` | `--base <REF>` | string | no | git ref the branch is compared against; defaults to `origin/main`, then `main`; neither resolvable → exit `2` |
| | `--json` | flag | no | |
| `check-flags` | `--json` | flag | no | |
| `verify-release` | `<ID>` | item id | yes, unless `--milestone` | `^F[0-9]{3}$`; a well-formed id with no ticket → exit `2`; mutually exclusive with `--milestone` |
| | `--milestone <M#>` | string | no | `^M[0-9]+$`; verifies every feature whose `target_milestone` matches |
| | `--json` | flag | no | |

**Environment.** These are inputs, not flags, and they decide whether a run may record.

| Variable | Type | Effect |
|---|---|---|
| `XTASK_ROLE` | string? | `release-manager` permits `verify-release` to write; any other value or absence makes the run a dry run |
| `XTASK_OWNER` | string? | recorded as `verifier`; required alongside the role, absent → exit `3` |
| `GITHUB_ACTIONS` / `GITHUB_REF` | string? | `true` with `refs/heads/main` grants the same permission as the role; `GITHUB_ACTOR` and the run URL are then recorded in `release.json` |
| `NO_COLOR` | any | suppresses colour; state is words in every mode regardless |

**Optional inputs and their absence.** Each prints `skipped: <path> absent` on stdout and does not
fail, so E000 runs before any product code exists: `openapi/v1.json`,
`crates/events/src/registry.rs`, `apps/web/src/api/generated/manifest.json`,
`services/mcp/schemas/manifest.json`, `crates/contracts/src/feature_flags.rs`, and the migrations
directory. Limits are catalog ≤ 200 rows, OpenAPI ≤ 16 MiB, ≤ 2,000 migrations, flag registry ≤ 500
entries; a breach is `io.too_large` naming the limit.

**Finding text.** Every finding is one line on stderr, sorted by path, then line, then code:

```
BLOCKED: <code> <path>[:<line>]: <message>
```

and a drift message always renders both sides in the same order, `expected: <a>, found: <b>`, so a
diff is readable without opening either artifact. No line exceeds 200 characters and output is ASCII.

| Code | Produced when |
|---|---|
| `contract.catalog` | a catalog row has an empty cell, a duplicate id, an event outside the event pattern, or a route outside the allowed path prefixes |
| `contract.row_missing` / `contract.row_orphan` | a feature ticket with no catalog row / a catalog row with no feature ticket |
| `contract.route_missing_in_ticket` / `contract.event_missing_in_ticket` | a route or event the row declares that section 4 of its ticket does not reproduce verbatim |
| `contract.route_not_in_row` / `contract.event_not_in_row` | the reverse: section 4 names one the row does not declare |
| `contract.route_undeclared` | a ticket names a path no row declares and that is neither a prefix nor an extension of one — the case a promised link with no row behind it produced |
| `contract.paths_mismatch` | `owned_paths` lacks a glob the row's module slug implies, or the harness path for its id |
| `contract.decision_link` | the ticket links neither the decision record nor its catalog row |
| `openapi.route_missing` / `openapi.orphan_operation` / `openapi.feature_mismatch` | a declared route with no operation / an operation mapping to no row and not marked internal / an operation whose feature extension names another id |
| `events.registry_missing` / `events.registry_orphan` / `events.payload_shape` | a catalog event absent from the registry / a registry constant absent from the catalog / a payload struct missing one of the seven envelope fields |
| `client.stale` | the generated client manifest's OpenAPI hash differs from the document's |
| `mcp.schema_stale` / `mcp.tool_missing` | the MCP manifest's catalog hash differs / a product row's aggregate has no tool |
| `migration.name` / `migration.down_missing` / `migration.module_not_owned` / `migration.header` | filename outside the pattern / an `up` with no matching `down` / a module segment no feature owns / a missing or malformed header comment |
| `migration.order` / `migration.mutated` | a new timestamp older than the newest on the base ref / a file on the base ref changed on the branch |
| `migration.destructive` / `migration.down_incomplete` / `migration.unclassified` | an undeclared destructive statement / a `down` that is empty or does not reference every object its `up` creates / a statement the classifier does not recognise, reported at warning level in JSON and declarable in the header |
| `flag.unregistered` / `flag.missing_ticket` / `flag.harness_mismatch` / `flag.unknown_reference` | an in-progress or archived feature with no registry entry / a registry entry with no ticket / a harness `flag` that differs from the ticket's / a code reference to an unregistered key |
| `flag.stale` / `flag.premature_default` / `flag.removed_reference` | an archived feature still active two milestones later / a graduated flag whose feature is not archived / a reference to a removed flag |
| `release.not_archived` / `release.child_open` | the ticket is not archived with `status: done` and `finished_at` / a story or task of it is not archived |
| `release.lane_missing` / `release.lane_failed` | a lane absent from the evidence manifest and not listed as not applicable with a reason / a lane recorded as failed |
| `release.gate_failed` | one of the three gates did not pass |
| `release.rollback_missing` / `release.notes_missing` | no rollback evidence / an empty release-notes section |
| `release.role_required` | a write was requested without the role and outside CI on `main` |
| `io.too_large` | an input past one of the limits above, naming the limit |

`release.scale_missing`, `release.scale_stale` and `release.scale_failed` are F067's additions to this
command's milestone check; that ticket defines them and this one consumes them.

**Exit codes.** One meaning each, so a caller branches on the code and never on the text.

| Code | Meaning |
|---|---|
| `0` | no findings; every optional input either checked or `skipped` |
| `1` | one or more findings; the summary line is `<command> failed: <n> findings` |
| `2` | usage, I/O, or a git failure that leaves the check unable to run at all |
| `3` | refused: `verify-release` ran every check and would have written, but the role was absent |

**`--json` output.** Exactly one object on stdout and nothing else, so the text and JSON forms are
structural equivalents.

| Field | Type | Notes |
|---|---|---|
| `command` | string | the subcommand name |
| `ok` | bool | `true` only on exit `0` |
| `checked` | integer | rows, files, or features examined |
| `findings` | `{ code, path, line?, message }[]` | in the same order as the text lines |
| `gates` | `{ contracts, migrations, flags }` of `"pass" \| "fail" \| "skipped"` | present on `verify-release` only |
| `duration_ms` | integer | |

**`release.json`** — written to `testing/evidence/<ID>/` by temp file plus rename, so a partial write
is impossible

| Field | Type | Notes |
|---|---|---|
| `id` | item id | |
| `verified_at` | timestamp | RFC 3339 UTC; with `head_commit`, the only non-deterministic field |
| `verifier` | string | `XTASK_OWNER`, or the CI actor and run URL |
| `head_commit` | string | full commit sha |
| `inputs` | `{ path, sha256 }[]` | sorted by path; the set the signature is taken over |
| `gates` | `{ contracts, migrations, flags }` | as above |
| `lanes` | map<string, `"pass" \| "missing" \| "failed"`> | the seven lanes; `missing` only when the harness lists it as not applicable with a reason |
| `rollback` | RollbackEvidence | see below |
| `signature` | string | SHA-256 hex over the sorted input hashes; unchanged inputs produce the same signature, which is what makes a second run verifiable rather than merely repeatable |

**`RollbackEvidence`** — read from `testing/evidence/<ID>/rollback.json`, not composed here

| Field | Type | Notes |
|---|---|---|
| `flag_off_verified` | bool | must be `true`, else `release.rollback_missing` |
| `migration_down_verified` | `bool \| "not_applicable"` | the string only for a feature that owns no migration |
| `commands` | string[] | what was run to prove it |
| `commit` | string | where it was proven |

**`M#.json`** — `{ milestone, verified_at, features: [{ id, signature }], ok }`, written to
`testing/evidence/milestones/`. Any failing feature fails the milestone and every finding is listed
before the exit.

### Use case signatures

In `automation/xtask/src/release.rs`. There is no `Ctx` and no `UnitOfWork` here: this feature owns no
table, opens no connection, and executes no statement — the migration gate is static analysis over
text, which is why it carries no SQLx dependency at all. `Finding` is F042's finding type and
`Reporter` is F041's; both are reused rather than redefined.

```rust
fn parse_catalog(text: &str) -> Result<Catalog, Vec<Finding>>;
fn check_ticket_against_row(item: &WorkItem, row: &ContractRow) -> Vec<Finding>;
fn check_openapi(catalog: &Catalog, doc: &OpenApiDoc) -> Vec<Finding>;
fn check_event_registry(catalog: &Catalog, registry_src: &str) -> Vec<Finding>;
fn check_generated_client(manifest: &Path, openapi: &Path) -> Vec<Finding>;
fn check_mcp_schemas(manifest: &Path, catalog_path: &Path) -> Vec<Finding>;
fn check_contracts(args: &Args) -> Result<(), String>;
fn load_migrations(dir: &Path) -> Result<Vec<Migration>, Vec<Finding>>;
fn check_migration_names(migrations: &[Migration], graph: &WorkGraph) -> Vec<Finding>;
fn check_migration_order(migrations: &[Migration], base: &str) -> Vec<Finding>;
fn check_migration_safety(migrations: &[Migration], graph: &WorkGraph) -> Vec<Finding>;
fn check_migrations(args: &Args) -> Result<(), String>;
fn load_flags(path: &Path) -> Result<Vec<FlagDef>, Vec<Finding>>;
fn check_flag_registry(graph: &WorkGraph, flags: &[FlagDef]) -> Vec<Finding>;
fn check_flag_references(root: &Path, flags: &[FlagDef]) -> Vec<Finding>;
fn check_flag_lifecycle(graph: &WorkGraph, flags: &[FlagDef]) -> Vec<Finding>;
fn check_flags(args: &Args) -> Result<(), String>;
fn verify_release(id: &ItemId, role: Role) -> Result<ReleaseRecord, Vec<Finding>>;
fn verify_milestone(milestone: &str, role: Role) -> Result<MilestoneRecord, Vec<Finding>>;
fn signature(inputs: &[InputHash]) -> String;
```

Every `check_*` returning `Vec<Finding>` is pure over already-loaded inputs and touches no filesystem,
so each rule is tested against a fixture value rather than a fixture tree; the four `check_*(args)`
entry points are the only ones that read the repository and the only ones that map findings onto an
exit code. `verify_release` returns the record it *would* write; the caller decides whether the role
permits writing it, which is why a dry run is the same computation as a recorded one and cannot
diverge from it.

Write boundaries, in place of a transaction boundary this feature has no database to open:

- `verify_release` writes `release.json` only after every gate and lane has passed, as one temp file
  plus rename, so no reader ever sees a half-written record and a failed run leaves the previous
  record intact.
- `verify_milestone` writes `M#.json` only when every feature in the milestone verified; a single
  failure writes nothing and lists every finding.
- Nothing else in this feature writes. It reads repository files and `git` metadata and never
  executes a migration, a statement, or a network call.

### PostgreSQL/SQLx

No database owned by this feature. Migrations are analysed statically from `services/api/migrations/*.sql` (never executed). Invariants enforced: unique increasing timestamps, one `down` per `up`, module segment owned by exactly one feature, header present, destructive statements declared and justified, `down` references every created object. Persistence written by this feature: `testing/evidence/<ID>/release.json`, `testing/evidence/milestones/M#.json`, both via temp file plus rename. Rollback of the feature itself is a code revert; evidence files are inert.

### React/TypeScript

No UI. The command line contract replaces the React section: four subcommands, `--json`, exit codes 0/1/2/3, expected/found drift lines, `skipped` lines for absent optional inputs, and the `release.json` and `M#.json` schemas documented in `testing/features/F044/api/cases.md`. The generated web client is only hashed (`client.stale`), never modified.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F044-01 through FR-F044-16 in `testing/features/F044/requirements/cases.md`
- [ ] Failure/edge-case tests: catalog row with an empty cell, event without `.v1`, route in ticket but not row, OpenAPI path with a renamed parameter, stale client hash, migration with older timestamp on a branch, mutated migration, `DROP COLUMN` without declaration, flag referenced in code but unregistered, archived feature with stale flag, manifest with one failed lane, rollback file missing, unchanged inputs producing the same signature
- [ ] Permission-negative tests: `verify-release` without `XTASK_ROLE` runs dry and writes nothing; CI on a non-main ref is also a dry run
- [ ] Rust unit tests: `release.rs` catalog parser, route normaliser, SQL classifier, flag reference scanner, signature
- [ ] CLI integration tests: fixture repositories under `testing/features/F044/fixtures/` with catalogs, tickets, OpenAPI documents, migrations, registries, and evidence
- [ ] Database lane: static migration analysis and evidence persistence cases
- [ ] Frontend lane: no UI, covered by CLI output cases
- [ ] E2E: hooks and CI gate scripts on a fixture branch; a full `verify-release` on a fixture feature
- [ ] Accessibility: expected/found lines, `NO_COLOR`, JSON parity
- [ ] Performance: contracts under 3 s, release under 5 s, milestone under 30 s

### Fast fanout configuration

- Test harness path: `testing/features/F044/`
- Feature flag: `F044_FEATURE`
- Fixture/seed factory: `testing/harness/repo.rs::scratch_repo` plus `testing/features/F044/fixtures/{catalog,openapi,migrations,flags,release}`
- Deterministic test data: fixed feature `F900` with module `widgets`, routes `GET /api/v1/widgets`, `POST /api/v1/widgets`, events `widget.created.v1`, migrations `20260903000000_widgets_create.up.sql`/`.down.sql`; `XTASK_NOW=2026-09-03T00:00:00Z`
- Mock/stub contracts: none; the OpenAPI, registry, client manifest, and MCP manifest are fixture files
- Parallel isolation: one scratch repository per test
- Targeted command: `cargo xtask test-feature F044`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F044/`

## 6. Acceptance criteria

```gherkin
Feature: Contract, migration, flag, and release control

Scenario: Event drift between ticket and catalog
  Given the F900 catalog row lists widget.created.v1 and the ticket section 4 lists widget.create.v1
  When a maintainer runs cargo xtask check-contracts
  Then stderr contains "BLOCKED: contract.event_missing_in_ticket work/tickets/F900-widgets.md" with "expected: widget.created.v1"
  And "contract.event_not_in_row" with "found: widget.create.v1", and the exit code is 1

Scenario: Destructive migration without declaration
  Given 20260903000001_widgets_drop.up.sql contains DROP COLUMN and its header says destructive=none
  When a maintainer runs cargo xtask check-migrations
  Then stderr contains "migration.destructive" naming the file and "DROP COLUMN"
  And the exit code is 1

Scenario: Unregistered flag reference
  Given services/api/src/widgets/routes.rs contains flags.enabled("F901_FEATURE") and the registry has no F901 entry
  When a maintainer runs cargo xtask check-flags
  Then stderr contains "flag.unknown_reference services/api/src/widgets/routes.rs:12"

Scenario: Release verification requires the role
  Given F900 is archived with passing evidence and rollback.json
  When a maintainer runs cargo xtask verify-release F900 without XTASK_ROLE
  Then every gate prints pass, stderr ends with "REFUSED: release.role_required", exit code 3, and no release.json exists

Scenario: Release recorded with a stable signature
  Given the same state as above
  When XTASK_ROLE=release-manager runs verify-release F900 twice
  Then testing/evidence/F900/release.json exists and both runs print the same signature
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F041 (`WorkGraph`, reporter, harness structure), F042 (ownership module for path-implication checks); decisions sections 3, 8, 9, 10; contracts rows F044 and every product row
- Blocks: none directly; F028 (OpenAPI), F047 (MCP schemas), and F048 (flag runtime) plug their generated artifacts into these checks
- Conflicts with: none; `testing/evidence/**` is written only by `collect-artifacts` (F043) and `verify-release`
- External dependencies: crates `serde_json`, `sha2`, `regex`, `toml`; `git` for `origin/main` comparisons
- Risks and mitigations: static SQL classification can miss vendor syntax, so unrecognised statements are reported as `migration.unclassified` at warning level in JSON and the header may declare them; route normalisation across `{id}` names could hide a real change, so the raw path is included in every finding; the role check is environment based, so CI records `GITHUB_ACTOR` and the run URL in `release.json` for traceability.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F041 and F042 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F044/`
- [ ] Fixture OpenAPI, registry, client manifest, MCP manifest, and migration samples checked into `testing/features/F044/fixtures/`
- [ ] Flag registry file path `crates/contracts/src/feature_flags.rs` and header comment format agreed with F001 and F048

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] The live repository passes `check-contracts`, `check-migrations`, and `check-flags` with exit 0 (optional inputs skipped)
- [ ] `verify-release F041` succeeds as the first real release record after F041's evidence is collected
- [ ] All changed files ≤ 500 lines; `validate-work` and `validate-tickets` pass
- [ ] Rollback verified: reverting the commit restores the previous `check-contracts` and `check-migrations`; evidence files remain valid JSON
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- `check-contracts` now detects route, event, path, OpenAPI, event-registry, client, and MCP schema drift; `check-migrations` enforces naming, pairing, ownership, headers, ordering, immutability, and destructive-change declarations; new `check-flags` enforces the flag registry and lifecycle; new `verify-release` records signed release evidence per feature and per milestone.
- No database or runtime change; rollback is a code revert. `F044_FEATURE` gates only the harness suite.
