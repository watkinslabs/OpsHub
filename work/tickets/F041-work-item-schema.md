---
id: F041
type: feature
status: planned
priority: P0
owner: platform
estimate: 5
target_milestone: M0
parent_epic: E000
depends_on: []
blocks: [F042, F043, F044, F001]
conflicts_with: []
parallel_safe: true
owned_paths: [automation/xtask/src/main.rs, automation/xtask/src/backlog.rs, automation/xtask/src/content.rs, automation/xtask/src/support.rs, automation/xtask/Cargo.toml, testing/features/F041/**]
feature_flag: F041_FEATURE
flag_default: off
branch: f041-work-item-schema
started_at: null
finished_at: null
---

# F041 — Work-item schema

## 1. Identity and dates

- Branch: `f041-work-item-schema`
- Capability area: developer workflow control plane (spec section 7 Phase 0 exit criteria, section 8 release gates; plan rules in `work/plan.md`)
- Decision references: `docs/architecture-decisions.md` sections 1, 9, 10; `docs/capability-contracts.md` row F041
- Module slug: `xtask-schema` (Rust module `automation/xtask/src/backlog.rs`, templates in `content.rs`, shared helpers in `support.rs`, dispatch in `main.rs`)

- Design: this feature has no user surface; it ships tooling, runtime or contracts only.

## 2. Requirement specification

### Problem and user outcome

The backlog in `work/` is the only contract between planning and implementation. Today `validate-work` checks a handful of string markers, so a ticket can name a parent that does not exist, depend on itself, claim `services/api/**`, or drift from `work/plan.md` without failing. Every downstream gate (ownership, lanes, release evidence) reads the same front matter, so an unvalidated schema poisons all of them.

As a maintainer, I want `cargo xtask validate-work`, `validate-plan`, and `validate-tickets` to prove that every epic, feature, story, and task file has a complete typed front matter, a resolvable hierarchy, an acyclic dependency graph, correct branch and filename, required sections, no scaffold markers, and no file over 500 lines, so that an agent can claim any planned item and implement it without asking a question.

### Functional requirements

- **FR-F041-01:** `validate-work` parses the YAML front matter (between the first two `---` lines) of every `*.md` file except `README.md` under `work/epics`, `work/tickets`, `work/stories`, `work/tasks`, `work/inprogress`, and `work/archived` into `FrontMatter`, and reports `front.missing_key` or `front.unknown_key` with file path and line for any key outside the per-kind key set (epic: `id,type,status,owner,target_milestone,branch,started_at,finished_at`; feature: those plus `priority,estimate,parent_epic,depends_on,blocks,conflicts_with,parallel_safe,owned_paths,feature_flag,flag_default`; story: `id,type,status,parent_epic,parent_feature,depends_on,owned_paths,feature_flag,branch,started_at,finished_at`; task: story keys plus `parent_story`).
- **FR-F041-02:** Values are validated as enumerations and reported as `front.bad_value`: `type` in `epic|feature|story|task`; `status` in `planned|ready|in-progress|blocked|done|archived`; `priority` in `P0..P3`; `estimate` in `1,2,3,5,8,13`; `target_milestone` in `M0..M7`; `flag_default` exactly `off`; `parallel_safe` a YAML boolean; `feature_flag` exactly `{feature id}_FEATURE`; `started_at`/`finished_at` either `null` or RFC 3339 UTC (`2026-09-03T14:05:00Z`).
- **FR-F041-03:** `id` matches `^[EFST][0-9]{3}$`, is unique across all six directories (`id.duplicate`), matches the first four characters of the filename (`id.filename_mismatch`), and its letter matches the directory kind (`E` in `work/epics`, `F` in `work/tickets`, `S` in `work/stories`, `T` in `work/tasks`; `work/inprogress` and `work/archived` accept `F`, `S`, `T`) or `type.mismatch` is reported.
- **FR-F041-04:** The filename stem equals `{id}-{slug}` where `slug` is the H1 title after `# {id} — ` lower-cased with every run of non-alphanumerics collapsed to `-`, and `branch` equals the stem with the id lower-cased (`f041-work-item-schema`); mismatches are `file.slug_mismatch` and `branch.invalid`.
- **FR-F041-05:** Hierarchy references resolve: `parent_epic` names an existing epic; a story's `parent_feature` is a feature whose `parent_epic` equals the story's; a task's `parent_story` is a story whose `parent_feature` equals the task's `parent_feature`; violations are `parent.unresolved` or `parent.inconsistent` and include both file paths.
- **FR-F041-06:** Every id in `depends_on`, `blocks`, and `conflicts_with` exists (`depends.unresolved`), no item lists itself, the `depends_on` graph over all items is acyclic (`depends.cycle` names the cycle in id order), `blocks` is the inverse of `depends_on` for features (`depends.blocks_mismatch` when `F042` depends on `F041` but `F041` does not list `F042` in `blocks`), and a story, task, or non-E000 feature with `depends_on: []` is `depends.empty`.
- **FR-F041-07:** A feature's `depends_on` set equals the `Depends on` column of its row in `work/plan.md` (an em-dash cell means the empty set); a difference is `plan.depends_mismatch` listing the extra and missing ids.
- **FR-F041-08:** `owned_paths` is a non-empty list of globs; a feature must include `testing/features/{id}/**`; any glob equal to `services/api/**`, `apps/web/**`, `crates/**`, `testing/features/**`, `services/worker/**`, `services/realtime/**`, `services/mcp/**`, `work/**`, or `**` is `paths.catch_all`; the non-module roots `.github/workflows/**`, `.githooks/**`, `infra/**`, `openapi/**`, `.lanes/**`, `.worktrees/**`, `.agent-target/**`, and `testing/evidence/**` are exempt and may be owned directly, matching the `CATCH_ALL_EXEMPT` constant in `automation/xtask/src/content.rs`; every story and task glob must be equal to or lexically narrower than one glob of its parent feature (`paths.not_subset`); two features whose globs can match the same path are `paths.overlap` unless one lists the other in `conflicts_with`.
- **FR-F041-09:** Required sections are present as exact headings: feature files need `## 1. Identity and dates` through `## 10. Release notes` plus `### Problem and user outcome`, `### Functional requirements`, `### Non-functional requirements`, `### Scope`, `### Rust backend`, `### PostgreSQL/SQLx`, `### React/TypeScript`, `### Fast fanout configuration`, and a ```` ```gherkin ```` block with at least three `Scenario:` lines; stories need `## Requirements`, `## Surfaces`, `## TDD harness`, `## Exit criteria`; tasks need `## Objective`, `## Specification`, `## TDD`, `## Exit criteria`; epics need `## Outcome`, `## Scope`, `## Child features`, `## Exit criteria`; a missing heading is `section.missing`.
- **FR-F041-10:** A feature file contains at least eight `FR-{id}-NN` and four `NFR-{id}-NN` identifiers, a story at least five `SR-{id}-NN`, and a task at least three test names under `testing/features/{feature}/`; counts below the minimum are `content.too_thin`. Any generated-template marker listed in the `PLACEHOLDERS` constant of `automation/xtask/src/content.rs` — unresolved/to-be-determined tokens, bracketed field stubs, underscore identifier stubs, empty ownership, and scaffold boilerplate phrases — and any backticked event name ending in .changed rather than .v1 are `marker.unresolved`. The constant is the single source of truth; this ticket does not restate its entries so the ticket cannot trip its own gate.
- **FR-F041-11:** Lifecycle rules: a file in `work/inprogress` has `status: in-progress` and a non-null `started_at`; a file in `work/archived` has `status: done|archived`, non-null `started_at` and `finished_at`, and `finished_at >= started_at`; a file in the three planning directories has both timestamps `null`; violations are `lifecycle.timestamp` or `lifecycle.status`.
- **FR-F041-12:** Every text file in the repository outside `.git`, `target`, `.agent-target`, `.worktrees`, and `node_modules` with more than 500 lines is `line.limit` with the actual count; binary files (a NUL byte in the first 8 KiB) are skipped.
- **FR-F041-13:** `validate-plan` parses every `## E### — Title` heading and every `| F###` row of `work/plan.md`, requires exactly one materialized file per epic, feature, story, and task id (`plan.missing_item`), rejects any materialized item absent from the plan (`plan.orphan_item`), requires each feature row to list exactly two stories and four tasks with tasks 1–2 belonging to story 1 and tasks 3–4 to story 2 (`plan.pairing`), and requires each feature's `parent_epic` to be the epic whose section contains its row (`plan.epic_mismatch`).
- **FR-F041-14:** `validate-tickets` applies FR-F041-01 to FR-F041-12 to `work/tickets`, `work/inprogress`, and `work/archived` only and additionally requires `testing/features/{id}/README.md`, `feature.toml` with `feature = "{id}"` and `flag = "{id}_FEATURE"`, and the seven lane directories `requirements, api, database, frontend, e2e, accessibility, performance` each containing `README.md` and `cases.md` (`harness.missing`), with `requirements/cases.md` referencing every `FR-`/`NFR-` id declared in the ticket (`harness.uncovered`).
- **FR-F041-15:** Each command prints one line per finding to stderr as `BLOCKED: <code> <path>:<line>: <message>` sorted by path then line then code, prints `<command> passed (<n> items)` to stdout on success, and with `--json` (or `XTASK_FORMAT=json`) prints exactly one JSON object `{ "command", "ok", "checked", "findings": [{ "code", "path", "line", "message" }], "duration_ms" }` to stdout; the exit code is 0 with no findings, 1 with findings, and 2 for usage or I/O errors.

### Non-functional requirements

- **NFR-F041-01 Performance:** `validate-work` over 500 work files and a 20,000-file repository completes in under 2 s wall clock on the CI runner (`ubuntu-latest`, 2 vCPU); each file is read exactly once and the line-limit scan streams files without loading more than 1 MiB at a time.
- **NFR-F041-02 Security/privacy:** the commands read only regular files under the repository root, follow no symlinks outside it, execute no content, make no network calls, and never print file contents beyond the offending line (truncated to 200 characters).
- **NFR-F041-03 Accessibility:** CLI output is plain ASCII by default, never conveys status by color alone, honours `NO_COLOR`, wraps no line beyond 200 characters, and the `--json` form gives tools and screen readers a structured equivalent of every finding.
- **NFR-F041-04 Reliability/observability:** output is byte-identical across runs for the same tree (sorted findings, no timestamps except `duration_ms`); when `GITHUB_ACTIONS=true` every finding is also emitted as `::error file=<path>,line=<line>::<code> <message>` so it annotates the PR diff.

### Scope

Included: the `FrontMatter` parser and typed model, the finding model and reporter, hierarchy, dependency, plan parity, branch, filename, section, marker, path-subset, lifecycle, line-limit, and harness-structure checks, `--json` output, GitHub annotations, and the `main.rs` dispatcher with the module split (`policy`, `backlog`, `content`, `lanes`, `release`, `support`) declared so later features add their modules without restructuring.

Excluded: forbidden-token scanning and ownership of staged files (F042), lane state under `work/inprogress` transitions (F043), contract, migration, and flag drift (F044), the CI workflow file (F001), and changes to the scaffold templates' wording in `content.rs` other than keeping `scaffold-plan` output valid under this schema.

## 3. UX specification

No UI. The surface is the command line.

- Entry points: `cargo xtask validate-work [--json]`, `cargo xtask validate-plan [--json]`, `cargo xtask validate-tickets [--json]`; invoked by `.githooks/pre-commit`, `.githooks/pre-push`, and `.github/workflows/gates.yml`.
- Primary flow: a maintainer edits `work/tasks/T023-grid-api.md`, runs `cargo xtask validate-work`, reads `BLOCKED: depends.unresolved work/tasks/T023-grid-api.md:9: depends_on names T099 which does not exist`, fixes the id, re-runs, sees `validate-work passed (241 items)`.
- Success: single stdout line and exit 0. Failure: one `BLOCKED:` line per finding, a final `validate-work failed: 3 findings` line, exit 1. Usage error: `usage: cargo xtask validate-work [--json]` on stderr, exit 2. Empty: a repository with no `work/` files reports `plan.missing_item` for every plan id rather than passing.
- Keyboard/screen reader: no interactive prompts; all output is line-oriented text or JSON.
- Denied: not applicable to a read-only validator; a file the process cannot read is reported as `io.unreadable` with the OS error and the run continues so all other findings are still shown.
- Stale: if `work/plan.md` is newer than the last `scaffold-plan` output the validator still reads both live files; there is no cache.
- Responsive/tokens/icons: not applicable.

## 4. Technical specification

Canonical contract: aggregate `work-item`; module `xtask-schema`; surface `cargo xtask validate-work`, `validate-plan`, `validate-tickets`; events none; persistence `work/**` front matter; role maintainer. Decision link: `docs/architecture-decisions.md` sections 9 and 10.

### Rust backend

- Crate: `automation/xtask` (edition 2024, no workspace membership so it builds with `CARGO_TARGET_DIR=/tmp/opshub-xtask-target`). Dependencies added to `automation/xtask/Cargo.toml`: `serde`, `serde_yaml`, `serde_json`, `globset`, `time` (RFC 3339 parsing only). No async runtime.
- `main.rs`: `mod policy; mod backlog; mod content; mod lanes; mod release; mod support;` and `fn main() -> ExitCode` dispatching on the first argument to `backlog::validate_work`, `backlog::validate_plan`, `backlog::validate_tickets`, `backlog::validate_decisions`, `content::scaffold_plan`, plus the F042–F044 commands; parses the global `--json` flag via `support::OutputFormat::from_args`.
- `backlog.rs` types: `enum ItemKind { Epic, Feature, Story, Task }`, `struct ItemId(String)` with `fn kind(&self) -> ItemKind`, `struct FrontMatter { id: ItemId, kind: ItemKind, status: Status, priority: Option<Priority>, owner: Option<String>, estimate: Option<u8>, target_milestone: Option<Milestone>, parent_epic: Option<ItemId>, parent_feature: Option<ItemId>, parent_story: Option<ItemId>, depends_on: Vec<ItemId>, blocks: Vec<ItemId>, conflicts_with: Vec<ItemId>, parallel_safe: Option<bool>, owned_paths: Vec<String>, feature_flag: Option<String>, flag_default: Option<String>, branch: String, started_at: Option<OffsetDateTime>, finished_at: Option<OffsetDateTime> }`, `struct WorkItem { path: PathBuf, dir: WorkDir, front: FrontMatter, title: String, body: String, front_lines: usize }`, `struct WorkGraph { items: BTreeMap<ItemId, WorkItem> }`, `struct PlanRow { epic: ItemId, feature: ItemId, stories: [ItemId; 2], tasks: [ItemId; 4], depends_on: BTreeSet<ItemId> }`.
- Use-case functions: `backlog::load_graph(root) -> Result<(WorkGraph, Vec<Finding>), XtaskError>`, `backlog::parse_plan(text) -> Result<Vec<PlanRow>, Finding>`, `backlog::check_front_matter(&WorkItem) -> Vec<Finding>`, `check_hierarchy(&WorkGraph)`, `check_dependencies(&WorkGraph)` (Tarjan SCC for cycles), `check_plan_parity(&WorkGraph, &[PlanRow])`, `check_branch_and_file(&WorkItem)`, `check_sections(&WorkItem)`, `check_markers(&WorkItem)`, `check_owned_paths(&WorkGraph)` (globset subset test by literal prefix and segment comparison), `check_lifecycle(&WorkItem)`, `check_harness(&WorkItem)`, `support::check_line_limits(root) -> Vec<Finding>`.
- Finding model in `support.rs`: `struct Finding { code: &'static str, path: PathBuf, line: usize, message: String }`, `struct Report { command: &'static str, ok: bool, checked: usize, findings: Vec<Finding>, duration_ms: u128 }`, `fn Report::emit(self, format: OutputFormat) -> ExitCode` implementing FR-F041-15 and NFR-F041-04 (annotations when `GITHUB_ACTIONS=true`).
- Error mapping: YAML parse failure → `front.parse` at the reported line; missing directory → exit 2 with `io: work/tasks: No such file or directory`; every check returns findings, never panics; `XtaskError::Usage` → exit 2.
- `content.rs` keeps `scaffold_plan`, `generated_epic/feature/story/task`, `write_harness`, and `contract_row`; its templates are updated so freshly scaffolded skeletons carry `owned_paths: [testing/features/{id}/**]` placeholders that fail `content.too_thin` rather than `marker.unresolved`, keeping `scaffold-plan` idempotent and refusing to overwrite (`write_generated` unchanged).
- Data access (decision 2.1): this feature owns no table and adds no repository; `automation/xtask` holds no SQL string, `sqlx` dependency, or database connection, and the `work-item` validators read only the file system, so nothing here bypasses `crates/persistence`.
- Authorization: the commands run as the invoking maintainer with read-only access; they never write to `work/**` (only `scaffold-plan` writes, and only new files). No tenant context exists.
- Validation limits: front matter ≤ 64 lines; `owned_paths` ≤ 32 globs; `depends_on` ≤ 16 ids; H1 title ≤ 120 characters; a file over any limit is `front.too_large` with the limit in the message.
- Telemetry: none beyond the JSON report and `duration_ms`; no events (contracts row lists none).
- Exit code contract shared with every other xtask command: `0` pass, `1` findings, `2` usage or I/O, `3` refused precondition (used by F043 and F044).

### PostgreSQL/SQLx

No database. Persistence is the file system: YAML front matter in `work/**`, the tables in `work/plan.md`, and `testing/features/F###/feature.toml`. Invariants are enforced at validation time rather than by constraints: unique `id` across the six work directories, single owner directory per id, acyclic `depends_on`, and pairwise-disjoint feature `owned_paths`. No migrations; rollback is reverting the `automation/xtask` change.

### React/TypeScript

No UI. The command line contract replaces the React section: three subcommands, a shared `--json` flag, exit codes 0/1/2, stderr `BLOCKED:` lines, stdout summary or JSON, and GitHub annotations. The generated JSON schema is documented in `testing/features/F041/api/cases.md` and is consumed by F043 `collect-artifacts` to attach validator output to lane evidence.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F041-01 through FR-F041-15 in `testing/features/F041/requirements/cases.md`
- [ ] Failure/edge-case tests: front matter without closing `---`, BOM-prefixed file, CRLF line endings, duplicate id across `work/tasks` and `work/archived`, dependency cycle of length 3, plan row with three stories, glob `services/api/src/sheets/**` versus `services/api/**`
- [ ] Permission-negative tests: a story claiming `services/api/src/authz/**` while its feature owns `services/api/src/sheets/**` is `paths.not_subset`; a feature claiming `services/api/**` is `paths.catch_all`
- [ ] Rust unit tests: `backlog.rs` parser, slug, subset, cycle detection; `support.rs` reporter ordering and JSON shape
- [ ] CLI integration tests: run the built binary against fixture trees under `testing/features/F041/fixtures/{valid,cycle,orphan,catch_all,thin}` and assert exit code, stderr, and JSON
- [ ] Database lane: file-system persistence cases (atomic reads, symlink refusal, CRLF)
- [ ] Frontend lane: no UI, covered by CLI output cases
- [ ] E2E: pre-commit hook and CI job invocation on a scratch clone
- [ ] Accessibility: `NO_COLOR`, ASCII-only, line width, JSON parity
- [ ] Performance: 500 work files and 20,000-file tree under 2 s

### Fast fanout configuration

- Test harness path: `testing/features/F041/`
- Feature flag: `F041_FEATURE` (selects the harness suite; the commands themselves are always available because CI depends on them)
- Fixture/seed factory: `testing/features/F041/fixtures/` scratch repositories built by `testing/harness/repo.rs::scratch_repo(name)` which copies a fixture tree into a temp dir and runs `git init`
- Deterministic test data: fixed ids `E900`, `F900`–`F903`, `S900`–`S907`, `T900`–`T915`; fixed clock `2026-09-03T00:00:00Z`
- Mock/stub contracts: none; the binary under test is the real `xtask`
- Parallel isolation: one temp directory per test, `CARGO_TARGET_DIR` shared read-only for the prebuilt binary
- Targeted command: `cargo xtask test-feature F041`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F041/`

## 6. Acceptance criteria

```gherkin
Feature: Work-item schema validation

Scenario: Clean backlog passes
  Given the repository backlog with 241 work files matching work/plan.md
  When a maintainer runs cargo xtask validate-work --json
  Then the exit code is 0
  And stdout is one JSON object with ok true, checked 241, and an empty findings array

Scenario: Dependency cycle is rejected
  Given task T900 depends on T901 and T901 depends on T900
  When a maintainer runs cargo xtask validate-work
  Then stderr contains "BLOCKED: depends.cycle work/tasks/T900-alpha.md:8: cycle T900 -> T901 -> T900"
  And the exit code is 1

Scenario: Story cannot widen its feature's ownership
  Given feature F900 owns services/api/src/sheets/** and story S900 lists services/api/src/authz/**
  When a maintainer runs cargo xtask validate-work
  Then the finding paths.not_subset names work/stories/S900-create-sheet.md and work/tickets/F900-sheets.md
  And the exit code is 1

Scenario: Plan parity
  Given work/plan.md lists T915 but no file under work/tasks defines id T915
  When a maintainer runs cargo xtask validate-plan
  Then stderr contains "plan.missing_item" with T915 and the exit code is 1

Scenario: Line limit
  Given work/tickets/F901-long.md has 501 lines
  When a maintainer runs cargo xtask validate-tickets
  Then stderr contains "BLOCKED: line.limit work/tickets/F901-long.md:501: 501 lines; limit is 500"
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: none (root of the E000 graph); decisions sections 9–10; contracts row F041
- Blocks: F042, F043, F044, F001
- Conflicts with: none. `automation/xtask/**` is exempt from `check-ownership` because it is a policy file, so F042–F044 may add their `mod` line and match arm in `main.rs` without a conflict; the owned path is documentary.
- External dependencies: crates `serde_yaml`, `globset`, `time`, `serde_json` from crates.io (vendored in `Cargo.lock`)
- Risks and mitigations: strict slug and section rules could reject the existing 241 files, so T163 runs the validator against the current tree and the ticket is not accepted until the tree passes; glob subset comparison by lexical prefix rejects some legal but unusual patterns, so the rule is documented and `paths.not_subset` messages show both globs.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] Requirement IDs above mapped to failing tests in `testing/features/F041/`
- [ ] `testing/harness/repo.rs::scratch_repo` available
- [ ] Module split agreed: `backlog.rs`, `content.rs`, `support.rs` created by T161 with the other modules as empty files

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] The current repository tree passes `validate-work`, `validate-plan`, and `validate-tickets` with exit 0
- [ ] `.githooks/pre-commit` and `gates.yml` invocations unchanged and green
- [ ] All changed files ≤ 500 lines; `cargo xtask self-test` passes
- [ ] Rollback verified: reverting the `automation/xtask` commit restores the previous validator behaviour with no data migration
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- `validate-work`, `validate-plan`, and `validate-tickets` now enforce the full front matter schema, hierarchy, dependency graph, plan parity, ownership subset, sections, markers, lifecycle, and the 500-line limit, with `--json` output and GitHub annotations.
- No database or runtime change; rollback is a code revert. `F041_FEATURE` gates only the harness suite.
