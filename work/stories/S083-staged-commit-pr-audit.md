---
id: S083
type: story
status: planned
parent_epic: E000
parent_feature: F042
depends_on: [F041]
owned_paths: [automation/xtask/src/policy.rs, .githooks/**, testing/features/F042/**]
feature_flag: F042_FEATURE
branch: s083-staged-commit-pr-audit
started_at: null
finished_at: null
---

# S083 — Staged/commit/PR audit

## Identity

- Parent feature: `F042` xtask audit/gates
- Owner: platform
- Branch: `s083-staged-commit-pr-audit`
- Decision references: `docs/architecture-decisions.md` sections 9–10; `docs/capability-contracts.md` row F042

## Vertical slice

As a maintainer, I want every text surface that reaches the repository (staged blobs, commit messages, pushed history, PR title and body) scanned for blocked attribution tokens with evasion-resistant matching and masked output, so that hooks and CI stop attributed changes without leaking the tokens into logs.

## Requirements

- **SR-S083-01:** `policy::scan` finds every token after NFKC normalisation, case folding, and zero-width stripping and reports original line and column with a masked rendering (covers FR-F042-01, FR-F042-14).
- **SR-S083-02:** `audit-staged` reads staged blobs from the index with `--diff-filter=ACMR`, skips policy files and binary blobs, and scans in 1 MiB windows with 64-byte overlap (FR-F042-02, FR-F042-13).
- **SR-S083-03:** `audit-message` strips comment lines and the scissors section before scanning and has no exemption (FR-F042-03).
- **SR-S083-04:** `audit-range` scans subject, body, author name, and author email of every commit in the range using `%x1f`/`%x1e` separators and batches ranges over 5,000 commits (FR-F042-04, FR-F042-13).
- **SR-S083-05:** `audit-pr` scans the title and body files and exits 2 when a file is missing (FR-F042-05).
- **SR-S083-06:** `.githooks/pre-commit`, `commit-msg`, and `pre-push` invoke the commands in the documented order, fail fast, and export `CARGO_TARGET_DIR`; `install-hooks` is idempotent (FR-F042-10, FR-F042-11).
- **SR-S083-07:** All commands support `--json`, exit 0/1/2, and meet the performance budgets (FR-F042-12, NFR-F042-01).

## Surfaces

- Infrastructure/container: `.githooks/pre-commit`, `.githooks/commit-msg`, `.githooks/pre-push` (POSIX sh)
- Rust service/API: `automation/xtask/src/policy.rs` (`Policy`, `Token`, `Source`, `CommitPart`, `Match`, `normalise`, `scan`, `scan_windows`, `audit_staged`, `audit_message`, `audit_range`, `audit_pr`, `install_hooks`); dispatch arms in `main.rs` (F041-owned, exempt policy file)
- Data/migration: none; reads the git index and history
- React/UI: none (no UI)
- Mocks/fixtures: `testing/features/F042/fixtures/{clean,tokens,windows,scissors}`; scratch repositories with fixed author and dates

## TDD harness

- Test path: `testing/features/F042/api/`, `testing/features/F042/e2e/`, `testing/features/F042/performance/`
- Feature flag: `F042_FEATURE`
- Targeted command: `cargo xtask test-feature F042`
- Full command: `cargo xtask test-all`
- First failing tests: `mixed_case_token_with_zero_width_joiner_detected`, `fullwidth_token_detected_with_original_column`, `finding_output_masks_token`, `staged_policy_file_skipped_but_message_not`, `token_across_window_boundary_detected`, `range_reports_author_email_part`, `pr_missing_body_file_exits_two`

## Exit criteria

- [ ] Requirement tests SR-S083-01 through SR-S083-07 written first and failing
- [ ] Tasks T165 and T166 complete; hooks updated and executable
- [ ] Unit, CLI integration, E2E hook, and performance tests pass in targeted and full modes
- [ ] Production call path named: `policy::audit_staged`, `audit_message`, `audit_range`, `audit_pr` dispatched from `main()` in `automation/xtask/src/main.rs`, invoked by `.githooks/pre-commit`, `.githooks/commit-msg`, `.githooks/pre-push`, and `gates.yml`
- [ ] Handoff evidence recorded in the F042 ticket
