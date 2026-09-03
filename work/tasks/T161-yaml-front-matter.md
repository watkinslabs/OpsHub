---
id: T161
type: task
status: planned
parent_epic: E000
parent_feature: F041
parent_story: S081
depends_on: [S081]
owned_paths: [automation/xtask/src/main.rs, automation/xtask/src/backlog.rs, automation/xtask/src/support.rs, automation/xtask/Cargo.toml, testing/features/F041/api/**, testing/features/F041/requirements/**]
feature_flag: F041_FEATURE
branch: t161-yaml-front-matter
started_at: null
finished_at: null
---

# T161 — YAML front matter

## Identity

- Parent story: `S081` Epic/feature schema
- Owner: platform
- Branch: `t161-yaml-front-matter`
- Decision references: `docs/architecture-decisions.md` sections 1, 9; `docs/capability-contracts.md` row F041

## Objective

Replace the string-prefix `front_value` reader with a typed YAML front matter parser, a finding/report model with `--json` output, and the module split of `automation/xtask/src` so every later check works on `WorkItem` values.

## Specification

- Owned paths: `automation/xtask/src/main.rs` (module declarations, `--json` flag, dispatch), `automation/xtask/src/backlog.rs` (`FrontMatter`, `WorkItem`, `WorkGraph`, `ItemId`, `ItemKind`, `Status`, `Priority`, `Milestone`, `load_graph`, `check_front_matter`), `automation/xtask/src/support.rs` (`Finding`, `Report`, `OutputFormat`, `XtaskError`), `automation/xtask/Cargo.toml` (add `serde`, `serde_yaml`, `serde_json`, `time`); empty `policy.rs`, `content.rs`, `lanes.rs`, `release.rs` created so the crate compiles with all `mod` lines
- Contract/input: a work file whose first line is `---`, followed by YAML, then `---`; per-kind key sets and enumerations from F041 FR-01 and FR-02; limits front matter ≤ 64 lines, ≤ 32 globs, ≤ 16 dependencies
- Output/behavior: `load_graph(root)` returns every item plus findings `front.parse`, `front.missing_key`, `front.unknown_key`, `front.bad_value`, `front.too_large`, `id.duplicate`, `id.filename_mismatch`, `type.mismatch`; `Report::emit` prints sorted `BLOCKED: <code> <path>:<line>: <message>` lines, the summary line, or the JSON object, GitHub annotations when `GITHUB_ACTIONS=true`, and returns exit 0/1/2
- Dependencies: none (root task of E000)
- Feature flag: `F041_FEATURE` selects the harness only
- Compatibility: existing commands keep working on the old `front_value` path until T162 switches them to `WorkGraph`

## TDD

- Failing test first: `testing/features/F041/api/front_matter_tests.rs::front_matter_missing_key_reported_with_line`, `::front_matter_bad_enum_value_reported`, `::front_matter_unknown_key_reported`, `::duplicate_id_across_directories_rejected`, `::crlf_and_bom_files_parse`, `::json_report_has_sorted_findings_and_exit_one`, `::github_annotations_emitted_when_env_set`
- Targeted command: `cargo xtask test-feature F041`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/features/F041/fixtures/{valid,bad_values,duplicate_id}` scratch trees; no external mocks

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] `cargo build --manifest-path automation/xtask/Cargo.toml` succeeds with the seven modules declared
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass (`main.rs` under 200 lines after the split)
- [ ] Handoff evidence recorded in S081
- [ ] `finished_at` recorded
