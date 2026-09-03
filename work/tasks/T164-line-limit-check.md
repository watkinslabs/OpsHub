---
id: T164
type: task
status: planned
parent_epic: E000
parent_feature: F041
parent_story: S082
depends_on: [T163]
owned_paths: [automation/xtask/src/support.rs, testing/features/F041/database/**, testing/features/F041/performance/**, testing/features/F041/accessibility/**]
feature_flag: F041_FEATURE
branch: t164-line-limit-check
started_at: null
finished_at: null
---

# T164 — Line-limit check

## Identity

- Parent story: `S082` Story/task schema
- Owner: platform
- Branch: `t164-line-limit-check`
- Decision references: `docs/architecture-decisions.md` section 9; `docs/capability-contracts.md` row F041

## Objective

Rewrite `support::check_line_limits` as a streaming, symlink-safe, binary-aware scan that meets the 2-second budget on a 20,000-file tree, and make the reporter's plain-text and JSON output accessible and deterministic.

## Specification

- Owned paths: `automation/xtask/src/support.rs` (`check_line_limits`, `is_binary`, `walk`, `Report::emit`, `OutputFormat`)
- Contract/input: repository root; exclusion set `.git`, `target`, `.agent-target`, `.worktrees`, `node_modules`, `.lanes`; limit 500 lines; binary detection = NUL byte within the first 8 KiB; symlinks are never followed (`symlink_metadata`), and a symlink pointing outside the root is `io.symlink_escape`
- Output/behavior: `line.limit` finding at line 501 with message `<n> lines; limit is 500`; files read through a 64 KiB `BufReader` counting `\n` (a trailing partial line counts); walk order sorted by path so findings are stable; `Report::emit` honours `NO_COLOR` (no ANSI when set or when stderr is not a TTY), truncates any echoed source line to 200 characters, and prints `duration_ms` only in JSON
- Dependencies: T163 (the reporter is exercised by every check)
- Feature flag: `F041_FEATURE`
- Budget: 20,000 files totalling 200 MiB scanned in under 2 s on `ubuntu-latest`; memory under 64 MiB resident

## TDD

- Failing test first: `testing/features/F041/database/fs_tests.rs::file_with_501_lines_reported`, `::binary_file_skipped`, `::symlink_outside_root_reported_not_followed`, `::crlf_counts_lines_once`, `testing/features/F041/performance/scan_bench.rs::scan_20k_files_under_2s`, `::validate_work_500_items_under_2s`, `testing/features/F041/accessibility/output_tests.rs::no_color_env_disables_ansi`, `::lines_never_exceed_200_chars`, `::json_findings_equal_text_findings`
- Targeted command: `cargo xtask test-feature F041`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/harness/repo.rs::wide_tree(20_000)` generator with fixed seed; a 501-line fixture; a fixture containing a NUL byte

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Performance lane meets NFR-F041-01; accessibility lane meets NFR-F041-03
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S082
- [ ] `finished_at` recorded
