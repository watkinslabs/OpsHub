---
id: F042
type: feature
status: planned
priority: P0
owner: platform
estimate: 5
target_milestone: M0
parent_epic: E000
depends_on: [F041]
blocks: [F043, F044, F001]
conflicts_with: []
parallel_safe: true
owned_paths: [automation/xtask/src/policy.rs, .githooks/**, testing/features/F042/**]
feature_flag: F042_FEATURE
flag_default: off
branch: f042-xtask-audit-gates
started_at: null
finished_at: null
---

# F042 — xtask audit/gates

## 1. Identity and dates

- Branch: `f042-xtask-audit-gates`
- Capability area: developer workflow control plane (spec section 8 release gates, section 7 Phase 0; plan rules on owned paths and build order; `automation/README.md` policy statement)
- Decision references: `docs/architecture-decisions.md` sections 9, 10; `docs/capability-contracts.md` row F042
- Module slug: `xtask-policy` (Rust module `automation/xtask/src/policy.rs`; hook scripts `.githooks/pre-commit`, `commit-msg`, `pre-push`)

- Design: this feature has no user surface; it ships tooling, runtime or contracts only.

## 2. Requirement specification

### Problem and user outcome

The repository must never carry attribution text for the configured assistant or provider names, and no change may land outside the `owned_paths` of a claimed ticket. Today the token scan is a plain substring match that prints the blocked word into the log, the ownership check treats globs as string prefixes, and nothing checks that an in-progress item's dependencies are actually finished or that two in-progress items do not overlap.

As a maintainer, I want `audit-staged`, `audit-message`, `audit-range`, `audit-pr`, `check-ownership`, and `self-test` to reject blocked tokens in every text surface (including case, Unicode, and zero-width evasions), reject staged paths outside active ownership, reject claims whose dependencies are unmet or whose paths overlap, and prove their own detection with positive controls, so that hooks and CI stop bad changes before they reach `main`.

### Functional requirements

- **FR-F042-01:** `policy::Policy::default()` builds the blocked token list from per-character arrays (the source never contains a token literal) and `policy::scan(label, text) -> Vec<Finding>` reports every occurrence after NFKC normalisation, ASCII case folding, and removal of zero-width characters (U+200B, U+200C, U+200D, U+2060, U+FEFF), as `policy.token` with the label, 1-based line and column in the original text, and a masked token rendering (`first letter + asterisks`, never the full token).
- **FR-F042-02:** `audit-staged` lists staged paths with `git diff --cached --name-only -z --diff-filter=ACMR`, reads each blob with `git show :<path>`, skips paths where `support::policy_file` is true (the repository rules file, `MANIFEST.md`, `automation/README.md`, `work/templates/PROJECT_STRUCTURE.md`, `automation/xtask/**`, `.githooks/**`; that function is the single source of truth and is not restated here, so this ticket does not trip its own scanner) and binary blobs (NUL in first 8 KiB), scans the rest, then runs the ownership gate; any finding exits 1.
- **FR-F042-03:** `audit-message FILE` scans the commit message after removing lines starting with `#` and everything after the `# ------------------------ >8 ------------------------` scissors line, and reports `policy.token` with `label = commit message`; there is no exemption.
- **FR-F042-04:** `audit-range RANGE` scans `git log --format=%H%x1f%an%x1f%ae%x1f%B%x1e RANGE` and reports each finding with the abbreviated commit sha and whether it came from the subject, body, author name, or author email; an invalid range exits 2 with the git error.
- **FR-F042-05:** `audit-pr TITLE_FILE BODY_FILE` scans both files with labels `PR title` and `PR body`; a missing file exits 2.
- **FR-F042-06:** `check-ownership` reads every item in `work/inprogress/`, compiles each `owned_paths` entry with `globset` (`**` and `*` semantics, not prefix match), and reports `ownership.outside` for every staged path not matched by any active glob and not a policy file, naming the active ids; when `work/inprogress/` is empty the command prints `check-ownership skipped: no active items` and exits 0.
- **FR-F042-07:** `check-ownership` also reports `ownership.overlap` when two active items belong to different features and their globs can match a common path, and `ownership.ambiguous` when a staged path is matched by active items of two different features; items of the same feature (a story and its tasks) may overlap.
- **FR-F042-08:** `check-ownership` reports `depends.unmet` for any active item whose `depends_on` contains an id that is not in `work/archived/` with `status: done|archived`, and `depends.conflict` when an active item's `conflicts_with` names another active item; both are evaluated from the F041 `WorkGraph`.
- **FR-F042-09:** `self-test` runs positive controls and exits 1 if any fails: clean text yields zero findings; every blocked token is detected in lower, upper, mixed case, with a zero-width joiner inserted after the first character, and in full-width Unicode form; a policy file path is skipped by `audit-staged` logic; glob `services/api/src/sheets/**` matches `services/api/src/sheets/a/b.rs` and not `services/api/src/sheetsx/b.rs`; `sh -n` succeeds on each `.githooks/*` script; and the three hook scripts are executable.
- **FR-F042-10:** `install-hooks` sets `core.hooksPath` to `.githooks`, marks `pre-commit`, `commit-msg`, and `pre-push` mode 0755, and prints the resolved hook path; running it twice is idempotent.
- **FR-F042-11:** `.githooks/pre-commit` runs `audit-staged`, `validate-plan`, `validate-work`, `check-contracts`, and stops at the first failing command; `.githooks/commit-msg` runs `audit-message "$1"`; `.githooks/pre-push` runs `audit-range` for every pushed ref (using `<remote_oid>..<local_oid>` or the whole history for a new branch), then `validate-plan`, `validate-work`, `check-contracts`; all three export `CARGO_TARGET_DIR=${CARGO_TARGET_DIR:-/tmp/opshub-xtask-target}`.
- **FR-F042-12:** Every command supports `--json` and the exit code contract from F041 (0 pass, 1 findings, 2 usage or git failure); findings carry `code`, `path` (or `commit:<sha>`), `line`, `column`, and `message`.
- **FR-F042-13:** Scan input is bounded: a single staged blob over 8 MiB is scanned in 1 MiB windows with a 64-byte overlap so a token spanning a window boundary is still found; a range with more than 5,000 commits is scanned in batches and the finding count is exact.
- **FR-F042-14:** A finding never prints the matched token; log output shows `token #<n> (<masked>)` and the surrounding line with the match replaced by asterisks, so hook and CI logs themselves stay clean.

### Non-functional requirements

- **NFR-F042-01 Performance:** `audit-staged` on 200 staged files totalling 20 MiB completes in under 1 s; `audit-range` over 1,000 commits under 2 s; `self-test` under 500 ms; measured on `ubuntu-latest`.
- **NFR-F042-02 Security/privacy:** the policy runs only `git` subprocesses with fixed argument lists (no shell), reads no environment beyond `CARGO_TARGET_DIR`, `NO_COLOR`, `GITHUB_ACTIONS`, and `XTASK_FORMAT`, never writes to the repository, and never echoes a blocked token or author email in full.
- **NFR-F042-03 Accessibility:** output follows the F041 text and JSON rules (plain ASCII, `NO_COLOR`, ≤ 200 characters per line, `BLOCKED:` prefix, no colour-only status).
- **NFR-F042-04 Reliability/observability:** results are deterministic for the same index and history; `self-test` runs in CI on every push so a silent regression of the detector fails the build; every command reports `checked` counts (files, commits, bytes) in JSON.

### Scope

Included: token policy with evasion-resistant scanning and masking, staged, message, range, and PR audits, glob-based ownership with overlap and ambiguity detection, dependency and conflict gates over active items, positive-control self-test, `install-hooks`, and the three hook scripts.

Excluded: the CI workflow file (F001 owns `.github/workflows/**` and calls these commands), lane claiming that moves files into `work/inprogress/` (F043), contract and migration drift (F044), and any change to the token list itself, which is a policy decision recorded in `automation/README.md`.

## 3. UX specification

No UI. The surface is the command line and git hooks.

- Entry points: `cargo xtask audit-staged`, `audit-message FILE`, `audit-range RANGE`, `audit-pr TITLE BODY`, `check-ownership`, `self-test`, `install-hooks`; hooks `.githooks/pre-commit`, `commit-msg`, `pre-push`; CI `gates.yml` steps `policy and backlog gates` and `pull request text gate`.
- Primary flow: a developer stages `services/api/src/sheets/service.rs` while `T022` is in `work/inprogress/`; `git commit` runs `pre-commit`; `audit-staged` scans the blob, `check-ownership` matches the path against `services/api/src/sheets/**`, all validators pass, the commit proceeds. If the developer also staged `apps/web/src/features/sheets/api.ts`, the hook prints `BLOCKED: ownership.outside apps/web/src/features/sheets/api.ts:0: not matched by owned_paths of active items T022` and the commit is refused.
- Success: summary line `audit-staged passed (12 files, 84 KiB)`. Failure: `BLOCKED:` lines plus `audit-staged failed: 2 findings`, exit 1. Empty: no staged files → `audit-staged passed (0 files)`. Usage: exit 2 with the usage line.
- Denied: a maintainer cannot bypass the hooks except with `git commit --no-verify`, which CI detects because `gates.yml` reruns the same commands on the pushed range and PR.
- Keyboard/screen reader: line-oriented output only; no prompts. Responsive/tokens/icons: not applicable.
- Stale: `check-ownership` reads `work/inprogress/` on every invocation; there is no cache, so releasing a lane (F043) takes effect on the next commit.

## 4. Technical specification

Canonical contract: aggregate `policy-gate`; module `xtask-policy`; surface `cargo xtask audit-staged`, `audit-message`, `audit-range`, `audit-pr`, `check-ownership`, `self-test`; events none; persistence `.githooks/**`, `automation/xtask/**`; role maintainer. Decision link: `docs/architecture-decisions.md` sections 9 and 10.

### Rust backend

- `policy.rs` types: `struct Policy { tokens: Vec<Token>, exempt: Vec<&'static str> }`, `struct Token { chars: Vec<char>, index: usize }` with `fn masked(&self) -> String`, `enum Source { StagedFile(PathBuf), CommitMessage(PathBuf), Commit { sha: String, part: CommitPart }, PrTitle, PrBody }`, `enum CommitPart { Subject, Body, AuthorName, AuthorEmail }`, `struct Match { token: usize, line: usize, column: usize, context: String }`, `struct OwnershipSet { items: Vec<ActiveItem> }`, `struct ActiveItem { id: ItemId, feature: ItemId, globs: GlobSet, depends_on: Vec<ItemId>, conflicts_with: Vec<ItemId> }`.
- Use-case functions: `policy::normalise(text) -> (String, Vec<usize>)` (NFKC + casefold + zero-width strip with an offset map back to original line/column), `policy::scan(&Policy, Source, &str) -> Vec<Finding>`, `policy::scan_windows(reader, window = 1 MiB, overlap = 64)`, `policy::audit_staged()`, `audit_message(path)`, `audit_range(range)`, `audit_pr(title, body)`, `policy::ownership::load_active(&WorkGraph) -> OwnershipSet`, `check_paths(&OwnershipSet, &[PathBuf])`, `check_overlap(&OwnershipSet)`, `check_dependencies(&OwnershipSet, &WorkGraph)`, `policy::self_test()`, `policy::install_hooks()`.
- Git access: `support::git(args) -> Result<Vec<u8>, XtaskError>` via `std::process::Command` with `-c core.quotepath=off`; staged blobs read with `git show :<path>` (never from the working tree); ranges via `git log` with `%x1f`/`%x1e` separators so multi-line bodies parse unambiguously.
- Error mapping: git non-zero exit → exit 2 with stderr trimmed; unreadable message file → exit 2; findings → exit 1; `self-test` control failure → `policy.selftest` finding naming the control, exit 1.
- Data access (decision 2.1): this feature owns no table and adds no repository; the `policy-gate` commands read git and the file system only, with no SQL string, `sqlx` dependency, or database connection anywhere in `automation/xtask`.
- Authorization: maintainer role is implicit for anyone who can commit; the gate cannot be disabled by environment variables; the only exemption is the static `policy_file` list, and that exemption never applies to commit messages, ranges, or PR text.
- Telemetry: JSON `checked: { files, commits, bytes }`; no events (contracts row lists none).
- Finding codes: `policy.token`, `policy.selftest`, `ownership.outside`, `ownership.overlap`, `ownership.ambiguous`, `depends.unmet`, `depends.conflict`, `hooks.not_executable`, `hooks.syntax`, `io.git`.
- Limits: token list ≤ 32 entries; active items ≤ 64; staged paths ≤ 10,000 per run (more is `io.git` with a hint to commit in batches).
- Exit codes: 0 pass, 1 findings, 2 usage or git failure; `self-test` returns 1 on any failed control so CI cannot pass with a broken detector.

### PostgreSQL/SQLx

No database. Persistence is the git index and history read through `git`, the hook scripts under `.githooks/`, and the active item files under `work/inprogress/` (written by F043). Invariant enforced at check time: every staged path is covered by exactly one feature's active ownership; no active item has an unmet dependency. No migrations; rollback is a code revert plus `git config --unset core.hooksPath` if hooks must be disabled.

### React/TypeScript

No UI. The command line contract replaces the React section: seven subcommands, `--json`, exit codes 0/1/2, masked findings with `path:line:column`, and hook scripts that fail fast. The PR gate reads the title and body from files written by the CI step, never from arguments, so shell quoting cannot bypass it.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F042-01 through FR-F042-14 in `testing/features/F042/requirements/cases.md`
- [ ] Failure/edge-case tests: token split across a 1 MiB window boundary, full-width Unicode token, zero-width joiner inside a token, token in author email, scissors line in message, binary staged blob, deleted staged file (`--diff-filter` excludes), empty `work/inprogress/`
- [ ] Permission-negative tests: staged path outside active ownership rejected; overlapping claims by two features rejected; active item with an unarchived dependency rejected; `--no-verify` commit caught by `audit-range` in CI
- [ ] Rust unit tests: `policy.rs` normalise offset map, masking, glob compile, overlap detection
- [ ] CLI integration tests: scratch repositories with staged content, commits, and active items under `testing/features/F042/fixtures/`
- [ ] Database lane: git-index and hook-file persistence cases
- [ ] Frontend lane: no UI, covered by CLI output cases
- [ ] E2E: commit, commit-msg, and push through installed hooks; PR gate script
- [ ] Accessibility: masked output, `NO_COLOR`, line width
- [ ] Performance: 200 files / 20 MiB, 1,000 commits, self-test budget
- [ ] Hook script tests: `sh -n`, executable bit, fail-fast order verified by inserting a failing validator fixture
- [ ] Determinism tests: two runs of every command byte-identical in text and JSON modes
- [ ] Masking tests: grep of all captured output for every token returns no match

### Fast fanout configuration

- Test harness path: `testing/features/F042/`
- Feature flag: `F042_FEATURE`
- Fixture/seed factory: `testing/harness/repo.rs::scratch_repo` plus `testing/features/F042/fixtures/{clean,tokens,ownership,overlap,unmet}` each containing a `work/` tree and a `stage.sh` that stages files
- Deterministic test data: fixed author `Fixture Author <fixture@example.test>`, fixed dates via `GIT_AUTHOR_DATE=2026-09-03T00:00:00Z`, token strings generated at test time from character arrays
- Mock/stub contracts: none; real `git` binary (≥ 2.40) required on the runner
- Parallel isolation: one scratch repository per test in a temp dir
- Targeted command: `cargo xtask test-feature F042`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F042/`

## 6. Acceptance criteria

```gherkin
Feature: Policy audit and ownership gates

Scenario: Blocked token in a staged file is rejected and masked
  Given a staged file docs/notes.md containing blocked token #1 in mixed case with a zero-width joiner
  When a maintainer runs cargo xtask audit-staged
  Then stderr contains "BLOCKED: policy.token docs/notes.md:3:12: token #1" and does not contain the token itself
  And the exit code is 1

Scenario: Policy files are exempt from staged scanning only
  Given automation/README.md is staged and contains the token list
  And a commit message file containing the same tokens
  When a maintainer runs audit-staged and then audit-message
  Then audit-staged exits 0 and audit-message exits 1

Scenario: Change outside active ownership is rejected
  Given T022 is in work/inprogress with owned_paths services/api/src/sheets/**
  And apps/web/src/features/sheets/api.ts is staged
  When a maintainer runs cargo xtask check-ownership
  Then stderr contains "ownership.outside apps/web/src/features/sheets/api.ts" naming T022
  And the exit code is 1

Scenario: Unmet dependency blocks an active item
  Given T023 is in work/inprogress and depends on T022 which is still in work/tasks
  When a maintainer runs cargo xtask check-ownership
  Then stderr contains "depends.unmet" naming T023 and T022 and the exit code is 1

Scenario: Self-test proves detection
  When CI runs cargo xtask self-test
  Then every token variant control is detected, the clean control is not, the hook scripts parse, and the exit code is 0
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F041 (`WorkGraph`, `Finding`, `Report`, `--json`); decisions sections 9–10; contracts row F042
- Blocks: F043, F044, F001
- Conflicts with: none; `automation/xtask/**` and `.githooks/**` are policy files exempt from ownership so the `mod policy;` line in `main.rs` (owned by F041) can be added without a conflict.
- External dependencies: `git` ≥ 2.40 on developer machines and CI; crates `globset`, `unicode-normalization`
- Risks and mitigations: NFKC normalisation can shift offsets, so the offset map is unit-tested against the original text; blocking author emails could reject legitimate addresses that contain a token substring, so `audit-range` reports author fields at `policy.token` severity only when the token is a whole word in the local part; hook runtime depends on a warm `CARGO_TARGET_DIR`, so `install-hooks` prints a one-time `cargo build` hint.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F041 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F042/`
- [ ] Scratch repository helper with `git init`, staging, and commit support available in `testing/harness/repo.rs`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] `self-test` green in CI on three consecutive pushes; hooks installed on a clean clone reject the token and ownership fixtures
- [ ] Every finding in hook and CI logs is masked (grep for the tokens over `testing/evidence/F042/` returns nothing)
- [ ] All changed files ≤ 500 lines; `validate-work` and `validate-tickets` pass
- [ ] Rollback verified: reverting the commit restores the previous scanner; `git config --unset core.hooksPath` disables hooks locally
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Token audits now normalise Unicode, strip zero-width characters, scan author fields and PR text, and mask matches in output; ownership uses real globs with overlap, ambiguity, unmet-dependency, and conflict detection; `self-test` covers every control.
- No database or runtime change; rollback is a code revert. `F042_FEATURE` gates only the harness suite.
