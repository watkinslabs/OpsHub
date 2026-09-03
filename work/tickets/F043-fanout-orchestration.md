---
id: F043
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
owned_paths: [automation/xtask/src/lanes.rs, .lanes/**, .worktrees/**, .agent-target/**, testing/features/F043/**]
feature_flag: F043_FEATURE
flag_default: off
branch: f043-fanout-orchestration
started_at: null
finished_at: null
---

# F043 — Fanout orchestration

## 1. Identity and dates

- Branch: `f043-fanout-orchestration`
- Capability area: developer workflow control plane (spec section 8 release gates; decisions section 9 fixture isolation: isolated tenant IDs, deterministic seeds, UTC, fixed clocks, unique worker IDs; plan build order rule: never start an item with unresolved dependencies or overlapping `owned_paths`)
- Decision references: `docs/architecture-decisions.md` sections 7, 9, 10; `docs/capability-contracts.md` row F043
- Module slug: `xtask-lanes` (Rust module `automation/xtask/src/lanes.rs`; lane state `.lanes/<ID>.toml`; worktrees `.worktrees/<branch>`; build targets `.agent-target/<branch>`)

## 2. Requirement specification

### Problem and user outcome

Several agents and people will implement tasks in parallel. Without a lane protocol they would share one working tree, one `target/` directory, one PostgreSQL schema, one NATS subject space, and one set of ports, and their test runs would corrupt each other. Moving a ticket into `work/inprogress/` by hand also skips the dependency, overlap, and timestamp rules that F041 and F042 enforce.

As a maintainer or an agent, I want `claim-lane <ID>` to atomically move a planned item into `work/inprogress/`, create its branch and worktree, allocate a private build target and fixture tenant, and record all of it in `.lanes/<ID>.toml`; `collect-artifacts <ID>` to gather test evidence into `testing/evidence/<ID>/`; and `release-lane <ID>` to archive or abandon the item and free every allocation, so that fanout is deterministic and every lane's evidence is auditable.

### Functional requirements

- **FR-F043-01:** `claim-lane <ID>` accepts a feature, story, or task id, runs `validate-work`, and refuses with exit 3 and `lane.precondition` when the item is not in a planning directory with `status: planned|ready`, when any `depends_on` id is not archived with `status: done|archived`, when any `conflicts_with` id is active, or when the item's `owned_paths` overlap an active item of another feature (F042 `ownership::check_overlap`).
- **FR-F043-02:** A successful claim moves the file to `work/inprogress/<same filename>`, rewrites `status: in-progress` and `started_at: <now UTC RFC 3339 seconds>`, and commits nothing; `now` comes from `XTASK_NOW` when set (fixed-clock tests) else the system clock.
- **FR-F043-03:** The claim creates branch `<branch from front matter>` from `origin/main` if it exists else local `main` (`--base <ref>` overrides), adds a worktree at `.worktrees/<branch>` with `git worktree add`, and refuses with `lane.branch_exists` if the branch already exists and is not checked out in that worktree path.
- **FR-F043-04:** Lane state is written atomically (`O_EXCL` create of `.lanes/<ID>.toml.tmp` then rename) with fields `id`, `kind`, `branch`, `worktree`, `owner` (`XTASK_OWNER` else `git config user.email`), `claimed_at`, `base_commit`, `slot`, `target_dir`, `fixture { tenant_id, schema, nats_prefix, port_base, clock, worker_id, seed }`, `artifacts_dir`; a second claim of the same id fails with `lane.exists` and changes nothing.
- **FR-F043-05:** `slot` is the lowest free integer in `0..=99` recorded in `.lanes/slots.toml` (created on first use, updated under an exclusive `flock`); when all 100 slots are taken the claim fails with `lane.slots_exhausted`.
- **FR-F043-06:** `allocate-target <ID>` returns `target_dir = .agent-target/<branch>` (created if missing), `vite_cache_dir = .agent-target/<branch>/vite`, and `playwright_browsers_path = ${HOME}/.cache/ms-playwright` (shared, read-only), printed as `export KEY=value` lines by default or as JSON with `--json`; the values are deterministic for the id and the command is idempotent.
- **FR-F043-07:** `allocate-fixture <ID>` returns `tenant_id = UUIDv5(namespace 6ba7b810-9dad-11d1-80b4-00c04fd430c8, "opshub-lane:" + ID)`, `schema = lane_<lower id>`, `nats_prefix = lane.<lower id>.`, `port_base = 20000 + slot * 10` (ten ports per lane: api, realtime, worker metrics, mcp, web, mailpit, minio, postgres proxy, nats, spare), `clock = 2026-09-03T00:00:00Z`, `worker_id = lane-<lower id>`, `seed = crc32(ID)`, printed as `export OPSHUB_TEST_TENANT_ID=…`, `OPSHUB_TEST_SCHEMA`, `OPSHUB_TEST_NATS_PREFIX`, `OPSHUB_TEST_PORT_BASE`, `OPSHUB_TEST_CLOCK`, `OPSHUB_TEST_WORKER_ID`, `OPSHUB_TEST_SEED`, `CARGO_TARGET_DIR`; values are identical on every call for the same lane and stored in the lane file.
- **FR-F043-08:** `test-feature <F>` and `test-all`, when run inside a claimed worktree (detected by `.lanes/<ID>.toml` whose `worktree` equals the current root), export the lane's target and fixture environment before running the harness so tests are isolated without manual setup.
- **FR-F043-09:** `collect-artifacts <ID>` copies, from the lane worktree, `<target_dir>/junit/**/*.xml`, `<target_dir>/playwright/**` (traces, videos), `<target_dir>/axe/*.json`, `<target_dir>/criterion/**/estimates.json`, `<target_dir>/xtask/*.json` (validator JSON reports), and `<target_dir>/commands.log` into `testing/evidence/<ID>/<lane>/` grouped by lane name (`requirements, api, database, frontend, e2e, accessibility, performance, xtask`), and writes `testing/evidence/<ID>/manifest.json` with `{ id, branch, base_commit, head_commit, collected_at, owner, lanes: { <lane>: { status: pass|fail|missing, files: [{ path, sha256, bytes }] } }, commands: [{ cmd, exit, duration_ms, started_at }] }`.
- **FR-F043-10:** The manifest is deterministic apart from `collected_at` and `head_commit`: files are sorted by path, hashes are SHA-256 of contents, and running the command twice on an unchanged worktree yields identical file lists; total copied size is capped at 512 MiB, and exceeding it fails with `artifacts.too_large` naming the largest files.
- **FR-F043-11:** `release-lane <ID> --outcome done` requires `testing/evidence/<ID>/manifest.json` with every applicable lane `pass` (lanes listed as not applicable in the item's harness `feature.toml` may be `missing`), rewrites `status: done` and `finished_at: <now>`, moves the file to `work/archived/`, removes the worktree with `git worktree remove` (refusing with `lane.dirty` if the worktree has uncommitted changes), deletes `.lanes/<ID>.toml`, frees the slot, and leaves the branch in place for merge.
- **FR-F043-12:** `release-lane <ID> --outcome abandoned` moves the file back to its planning directory with `status: planned` and `started_at: null`, removes the worktree (`--force` required if dirty), deletes the lane file, frees the slot, and deletes `testing/evidence/<ID>/` only when `--purge-evidence` is given.
- **FR-F043-13:** Only the lane `owner` (or `--owner-override` with a reason recorded in the lane file history) may `release-lane`, `collect-artifacts`, or `allocate-*` for a lane; another actor receives exit 3 `lane.not_owner`.
- **FR-F043-14:** `claim-lane --list` prints every active lane as `<ID> <branch> <owner> <slot> <claimed_at>` sorted by id, and `--json` returns the lane files verbatim; the command is read-only.
- **FR-F043-15:** Every lane command supports `--json` and the shared exit codes (0 pass, 1 findings, 2 usage or git/I-O error, 3 refused precondition) and writes a line to `.lanes/history.log` (`<timestamp> <actor> <command> <ID> <result>`) so lane activity is auditable even after the lane file is deleted.

### Non-functional requirements

- **NFR-F043-01 Performance:** `claim-lane` completes in under 5 s on a repository with 100 lanes and a 50 MiB checkout (worktree add dominates); `allocate-target` and `allocate-fixture` under 100 ms; `collect-artifacts` streams files at disk speed with under 64 MiB resident memory.
- **NFR-F043-02 Security/privacy:** lane commands never execute code from the worktree, never follow symlinks out of the worktree when collecting artifacts (`artifacts.symlink_escape`), record only the owner's email, and `.lanes/`, `.worktrees/`, and `.agent-target/` are git-ignored so no lane state or build output is committed.
- **NFR-F043-03 Accessibility:** output follows the F041 text and JSON rules; `export` lines are valid POSIX shell so `eval "$(cargo xtask allocate-fixture T021)"` works in any shell without color or Unicode.
- **NFR-F043-04 Reliability/observability:** lane state changes are atomic (temp file plus rename, `flock` on `slots.toml`); a crash between file move and lane-file creation is recoverable with `claim-lane --repair <ID>` which reconciles `work/inprogress/`, `.lanes/`, and `git worktree list`; `history.log` is append-only.

### Scope

Included: claim and release protocol with preconditions, branch and worktree lifecycle, slot registry, deterministic target and fixture allocation, environment injection for `test-feature`/`test-all`, artifact collection with manifest and hashes, owner enforcement, lane listing, repair, and history log.

Excluded: running the harness itself (F001 CI and the feature harnesses), creating PostgreSQL schemas or NATS streams (the runtime in F004 consumes the allocated names), merging branches, remote CI lane scheduling, and release verification over the collected evidence (F044).

## 3. UX specification

No UI. The surface is the command line, used by agents and maintainers.

- Entry points: `cargo xtask claim-lane <ID> [--base REF] [--list] [--repair <ID>]`, `release-lane <ID> --outcome done|abandoned [--force] [--purge-evidence] [--owner-override REASON]`, `allocate-target <ID>`, `allocate-fixture <ID>`, `collect-artifacts <ID>`.
- Primary flow: an agent runs `cargo xtask claim-lane T021`, sees `claimed T021 on t021-schema-migration at .worktrees/t021-schema-migration (slot 3)`, runs `cd .worktrees/t021-schema-migration && eval "$(cargo xtask allocate-fixture T021)"`, implements and runs `cargo xtask test-feature F006`, runs `cargo xtask collect-artifacts T021`, commits, then `cargo xtask release-lane T021 --outcome done`.
- Success: one summary line per command and exit 0. Refused: `REFUSED: lane.precondition T021: depends_on S011 is not archived`, exit 3. Failure: `BLOCKED:` findings from the embedded validators, exit 1. Error: git or I/O error text, exit 2.
- Empty: `claim-lane --list` with no lanes prints `no active lanes`.
- Denied: a non-owner running `release-lane` sees `REFUSED: lane.not_owner T021: owned by a@example.test`.
- Stale/conflict: if the lane file exists but the worktree is missing, commands print `lane.inconsistent` and point at `--repair`.
- Keyboard/screen reader: no prompts; destructive actions require explicit flags. Responsive/tokens/icons: not applicable.

## 4. Technical specification

Canonical contract: aggregate `execution-lane`; module `xtask-lanes`; surface `cargo xtask claim-lane <ID>`, `release-lane <ID>`, `allocate-target <ID>`, `allocate-fixture <ID>`, `collect-artifacts <ID>`; events none; persistence `work/inprogress/**`, `.lanes/<ID>.toml`; role maintainer. Decision link: `docs/architecture-decisions.md` sections 7, 9, and 10.

### Rust backend

- `lanes.rs` types: `struct Lane { id: ItemId, kind: ItemKind, branch: String, worktree: PathBuf, owner: String, claimed_at: OffsetDateTime, base_commit: String, slot: u8, target_dir: PathBuf, fixture: Fixture, artifacts_dir: PathBuf, history: Vec<LaneEvent> }`, `struct Fixture { tenant_id: Uuid, schema: String, nats_prefix: String, port_base: u16, clock: String, worker_id: String, seed: u32 }`, `struct Slots { taken: BTreeMap<u8, ItemId> }`, `enum Outcome { Done, Abandoned }`, `struct Manifest { id, branch, base_commit, head_commit, collected_at, owner, lanes: BTreeMap<String, LaneEvidence>, commands: Vec<CommandRecord> }`, `struct LaneEvidence { status: EvidenceStatus, files: Vec<FileRecord> }`, `struct FileRecord { path: String, sha256: String, bytes: u64 }`, `struct CommandRecord { cmd: String, exit: i32, duration_ms: u64, started_at: String }`.
- Use-case functions: `lanes::claim(id, opts) -> Result<Lane, Refusal>`, `lanes::release(id, outcome, opts)`, `lanes::allocate_target(id) -> TargetEnv`, `lanes::allocate_fixture(id) -> FixtureEnv`, `lanes::collect_artifacts(id) -> Manifest`, `lanes::list()`, `lanes::repair(id)`, `lanes::current_lane(cwd) -> Option<Lane>` (used by `test-feature`/`test-all`), `lanes::slots::acquire()`/`release(slot)` under `flock`, `lanes::env::export_lines(&Lane) -> String`.
- Persistence: `.lanes/<ID>.toml` (TOML via `toml` crate), `.lanes/slots.toml`, `.lanes/history.log`; the work file move rewrites only the `status`, `started_at`, and `finished_at` lines and preserves every other byte.
- Git access through `support::git`: `worktree add`, `worktree remove`, `worktree list --porcelain`, `rev-parse`, `status --porcelain`, `config user.email`.
- Error mapping: precondition failures → `Refusal { code, message }` exit 3; validator findings → exit 1; git/I-O → exit 2; `--json` errors carry the same `code`.
- Authorization: maintainer role implicit; lane ownership by email enforced per FR-F043-13; overrides logged.
- Telemetry: `history.log` lines and manifest `commands`; no events (contracts row lists none).
- Refusal codes: `lane.precondition`, `lane.exists`, `lane.branch_exists`, `lane.slots_exhausted`, `lane.not_owner`, `lane.dirty`, `lane.inconsistent`, `lane.port_in_use`, `artifacts.too_large`, `artifacts.symlink_escape`.
- Limits: 100 slots; 512 MiB evidence per lane; lane file ≤ 64 KiB including history; `history.log` rotated by the maintainer, never by the tool.

### PostgreSQL/SQLx

No database owned by this feature. `allocate-fixture` only names the PostgreSQL schema `lane_<id>` and NATS prefix; the F004 runtime and `testing/harness/db.rs` create and drop the schema from `OPSHUB_TEST_SCHEMA`. Invariants: one lane per id, one slot per lane, `port_base` unique per slot, `tenant_id` unique per lane by UUIDv5 construction. No migrations; rollback is deleting `.lanes/`, removing worktrees, and moving files back with `release-lane --outcome abandoned`.

### React/TypeScript

No UI. The command line contract replaces the React section: five subcommands plus `--list` and `--repair`, POSIX `export` output or JSON, exit codes 0/1/2/3, and the manifest JSON schema documented in `testing/features/F043/api/cases.md` and consumed by F044 `verify-release`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F043-01 through FR-F043-15 in `testing/features/F043/requirements/cases.md`
- [ ] Failure/edge-case tests: claim with unmet dependency, claim overlapping active feature, double claim, all slots taken, branch already exists, dirty worktree release, crash between move and lane file then repair, artifact set over 512 MiB, symlink escape in artifacts
- [ ] Permission-negative tests: non-owner release refused; owner override recorded; claim of an item whose parent feature owns overlapping paths with another active feature refused
- [ ] Rust unit tests: `lanes.rs` fixture derivation, slot acquisition under contention, export line quoting, manifest hashing
- [ ] CLI integration tests: scratch repositories with a `main` branch and `work/` fixtures
- [ ] Database lane: lane-file and slot-registry persistence cases (atomic write, flock, history append)
- [ ] Frontend lane: no UI, covered by CLI output cases
- [ ] E2E: two concurrent lanes end to end through claim, allocate, test-feature, collect, release
- [ ] Accessibility: `eval`-safe export lines, plain output
- [ ] Performance: claim under 5 s, allocations under 100 ms, collection memory bound

### Fast fanout configuration

- Test harness path: `testing/features/F043/`
- Feature flag: `F043_FEATURE`
- Fixture/seed factory: `testing/harness/repo.rs::scratch_repo` plus `testing/features/F043/fixtures/{graph,artifacts}`; `graph` holds an archived S011-like story and planned tasks
- Deterministic test data: `XTASK_NOW=2026-09-03T00:00:00Z`, `XTASK_OWNER=fixture@example.test`, fixed ids `T900`–`T903`
- Mock/stub contracts: none; real `git`; artifact fixtures are small generated files with known hashes
- Parallel isolation: one scratch repository per test; concurrent-claim tests spawn two processes against one repository
- Targeted command: `cargo xtask test-feature F043`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F043/`

## 6. Acceptance criteria

```gherkin
Feature: Lane claiming and isolated execution

Scenario: Claim a ready task
  Given T900 is planned, its story S900 is archived as done, and no lane is active
  When the agent runs cargo xtask claim-lane T900 with XTASK_NOW fixed
  Then work/inprogress/T900-alpha.md has status in-progress and started_at 2026-09-03T00:00:00Z
  And branch t900-alpha exists with worktree .worktrees/t900-alpha and .lanes/T900.toml has slot 0

Scenario: Claim refused on unmet dependency
  Given T901 depends on T900 which is still in work/tasks
  When the agent runs cargo xtask claim-lane T901
  Then stderr contains "REFUSED: lane.precondition T901: depends_on T900 is not archived"
  And the exit code is 3 and no file moved

Scenario: Deterministic fixture allocation
  Given lane T900 holds slot 0
  When allocate-fixture T900 runs twice
  Then both outputs are identical and contain OPSHUB_TEST_SCHEMA=lane_t900 and OPSHUB_TEST_PORT_BASE=20000

Scenario: Non-owner cannot release
  Given lane T900 owned by a@example.test
  When XTASK_OWNER=b@example.test runs release-lane T900 --outcome done
  Then stderr contains "REFUSED: lane.not_owner T900" and the lane is unchanged

Scenario: Evidence collected and lane released
  Given lane T900 has junit and axe outputs under its target dir
  When collect-artifacts T900 and then release-lane T900 --outcome done run
  Then testing/evidence/T900/manifest.json lists every file with sha256
  And work/archived/T900-alpha.md has finished_at set and .lanes/T900.toml is gone
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F041 (`WorkGraph`, reporter), F042 (`ownership::check_overlap`, dependency gate); decisions sections 7, 9, 10; contracts row F043
- Blocks: none directly; every product feature's fanout uses these commands
- Conflicts with: none; `.lanes/`, `.worktrees/`, `.agent-target/` are new git-ignored directories
- External dependencies: `git` ≥ 2.40 with worktree support; crates `toml`, `uuid` (v5), `sha2`, `fs2` (flock), `crc32fast`
- Risks and mitigations: git worktrees share one object store so a corrupted index in one lane can affect others, mitigated by `--repair` and by never running git write commands in another lane's worktree; port blocks assume no other process uses 20000–20999, so `allocate-fixture` probes the block and reports `lane.port_in_use` with the conflicting port; long-lived abandoned lanes exhaust slots, so `claim-lane --list` shows `claimed_at` and the release command frees slots even when the worktree is already gone.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F041 and F042 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F043/`
- [ ] `.gitignore` entries for `.lanes/`, `.worktrees/`, `.agent-target/` agreed (added by T169)
- [ ] `testing/harness/repo.rs` supports creating a `main` branch and a bare remote

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Two real lanes (for example T005 and T013 from E001) claimed concurrently on CI, tested, collected, and released without interference
- [ ] `check-ownership` passes on commits made inside a lane worktree
- [ ] All changed files ≤ 500 lines; `validate-work` and `validate-tickets` pass
- [ ] Rollback verified: `release-lane --outcome abandoned` on every open lane restores the planning tree byte-for-byte
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- New `claim-lane`, `release-lane`, `allocate-target`, `allocate-fixture`, and `collect-artifacts` commands give each work item its own branch, worktree, build target, fixture tenant, port block, and evidence manifest, with dependency, overlap, owner, and slot enforcement.
- No database or runtime change; lane state lives in git-ignored `.lanes/`. Rollback is abandoning lanes and reverting the code. `F043_FEATURE` gates only the harness suite.
