---
id: T165
type: task
status: planned
parent_epic: E000
parent_feature: F042
parent_story: S083
depends_on: [S083]
owned_paths: [automation/xtask/src/policy.rs, testing/features/F042/api/**, testing/features/F042/requirements/**, testing/features/F042/accessibility/**]
feature_flag: F042_FEATURE
branch: t165-forbidden-token-gate
started_at: null
finished_at: null
---

# T165 — Forbidden-token gate

## Identity

- Parent story: `S083` Staged/commit/PR audit
- Owner: platform
- Branch: `t165-forbidden-token-gate`
- Decision references: `docs/architecture-decisions.md` sections 9–10; `docs/capability-contracts.md` row F042

## Objective

Implement the evasion-resistant token scanner with masked findings and move the four audit commands (`audit-staged`, `audit-message`, `audit-range`, `audit-pr`) into `policy.rs` on top of it.

## Specification

- Owned paths: `automation/xtask/src/policy.rs` (`Policy`, `Token`, `Source`, `CommitPart`, `Match`, `normalise`, `scan`, `scan_windows`, `audit_staged` token half, `audit_message`, `audit_range`, `audit_pr`)
- Contract/input: token list built from char arrays; text from `git show :<path>`, a message file, `git log --format=%H%x1f%an%x1f%ae%x1f%B%x1e RANGE`, or the PR title/body files; policy-file exemption from `support::policy_file` applies to staged paths only
- Output/behavior: `normalise` returns the folded text plus an offset map from normalised byte index to original `(line, column)`; `scan` reports `policy.token` per occurrence with `token #<n> (<masked>)` and a context line with the match replaced by asterisks, truncated to 200 characters; `scan_windows` uses 1 MiB windows with 64-byte overlap and de-duplicates matches in the overlap; binary blobs and deleted paths are skipped; message scanning drops `#` comment lines and the scissors tail; author email matches count only when the token is a whole word in the local part; ranges over 5,000 commits are batched; exit 0/1/2 and `--json`
- Dependencies: F041 `Finding`, `Report`, `support::git`
- Feature flag: `F042_FEATURE`
- Crates: `unicode-normalization` for NFKC

## TDD

- Failing test first: `testing/features/F042/api/scan_tests.rs::mixed_case_token_with_zero_width_joiner_detected`, `::fullwidth_token_detected_with_original_column`, `::finding_output_masks_token`, `::token_across_window_boundary_detected`, `::binary_blob_skipped`, `testing/features/F042/api/audit_tests.rs::staged_policy_file_skipped_but_message_not`, `::scissors_tail_ignored_in_message`, `::range_reports_author_email_part`, `::pr_missing_body_file_exits_two`
- Targeted command: `cargo xtask test-feature F042`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: scratch repositories from `testing/harness/repo.rs` with staged files, commits, and message files generated from character arrays at test time

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] The four audit commands dispatched from `main()` through `policy.rs`; the old `findings`/`blocked_tokens` functions removed from `main.rs`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S083
- [ ] `finished_at` recorded
