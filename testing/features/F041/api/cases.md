# F041 api cases

File: `testing/features/F041/api/{front_matter_tests.rs,graph_tests.rs,paths_tests.rs,sections_tests.rs,harness_tests.rs}`. Each test copies a fixture tree from `testing/features/F041/fixtures/` into a temp dir, runs the prebuilt `xtask` binary with `validate-work`, `validate-plan`, or `validate-tickets`, and asserts exit code, stderr lines, and `--json` output. Flag `F041_FEATURE`.

- `front_matter_missing_key_reported_with_line` — FR-F041-01: task without `parent_story` → `BLOCKED: front.missing_key work/tasks/T900-alpha.md:2: parent_story`, exit 1.
- `front_matter_unknown_key_reported` — FR-F041-01: epic with `estimate:` → `front.unknown_key`.
- `front_matter_bad_enum_value_reported` — FR-F041-02: `estimate: 4`, `priority: P9`, `flag_default: on`, `finished_at: yesterday` → four `front.bad_value` findings naming the key and allowed set.
- `crlf_and_bom_files_parse` — FR-F041-01: CRLF file with UTF-8 BOM parses with no findings.
- `duplicate_id_across_directories_rejected` — FR-F041-03: `work/tasks/T900-a.md` and `work/archived/T900-a.md` → `id.duplicate` on both paths.
- `id_letter_must_match_directory` — FR-F041-03: `work/stories/T900-a.md` → `type.mismatch`.
- `story_with_foreign_epic_is_parent_inconsistent` — FR-F041-05: message names both files.
- `dependency_cycle_named_in_id_order` — FR-F041-06: three-node cycle T900→T902→T901→T900 reported once as `T900 -> T901 -> T902 -> T900`.
- `feature_blocks_must_mirror_depends_on` — FR-F041-06: `depends.blocks_mismatch` on the upstream feature.
- `empty_depends_allowed_only_for_e000_features` — FR-F041-06: F900 in E900 (the fixture root epic) passes; S900 with `[]` → `depends.empty`.
- `plan_depends_mismatch_lists_extra_and_missing` — FR-F041-07: message `extra: [F903] missing: [F901]`.
- `plan_row_with_three_stories_is_pairing_error` — FR-F041-13: `plan.pairing` with the row's feature id.
- `orphan_task_file_reported` — FR-F041-13: `plan.orphan_item T999`.
- `story_glob_outside_feature_is_not_subset` — FR-F041-08: message shows `services/api/src/authz/**` and parent list.
- `feature_catch_all_glob_rejected` — FR-F041-08: `services/api/**` → `paths.catch_all`.
- `migration_glob_narrower_pattern_is_subset` — FR-F041-08: task glob `services/api/migrations/*_sheets_*.sql` under the same feature glob passes.
- `overlapping_features_without_conflicts_flagged` — FR-F041-08: two features owning `crates/domain/src/sheets/**` → `paths.overlap`.
- `missing_gherkin_block_is_section_missing` — FR-F041-09: also covers a block with two scenarios.
- `changed_event_without_v1_is_marker` — FR-F041-10: `sheet.changed` in section 4 → `marker.unresolved`.
- `thin_ticket_is_too_thin` — FR-F041-10: 6 FRs / 3 NFRs → `content.too_thin` with counts.
- `inprogress_file_without_started_at_rejected` — FR-F041-11: `lifecycle.timestamp`.
- `harness_missing_lane_reported` — FR-F041-14: `harness.missing testing/features/F900/e2e/cases.md`.
- `requirements_cases_must_cite_every_fr` — FR-F041-14: `harness.uncovered FR-F900-07`.
- `usage_error_exits_two` — FR-F041-15: `validate-work --bogus` → usage line, exit 2.

Evidence: JUnit output and captured stdout/stderr under `testing/evidence/F041/api/`.
