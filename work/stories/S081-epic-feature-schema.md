---
id: S081
type: story
status: planned
parent_epic: E000
parent_feature: F041
depends_on: [F041]
owned_paths: [automation/xtask/src/main.rs, automation/xtask/src/backlog.rs, automation/xtask/src/support.rs, automation/xtask/Cargo.toml, testing/features/F041/**]
feature_flag: F041_FEATURE
branch: s081-epic-feature-schema
started_at: null
finished_at: null
---

# S081 — Epic/feature schema

## Identity

- Parent feature: `F041` Work-item schema
- Owner: platform
- Branch: `s081-epic-feature-schema`
- Decision references: `docs/architecture-decisions.md` sections 9–10; `docs/capability-contracts.md` row F041

## Vertical slice

As a maintainer, I want `cargo xtask validate-work` to parse every epic and feature file into a typed front matter, resolve parents and dependencies across the whole graph, and compare feature dependencies with `work/plan.md`, so that a feature ticket cannot be claimed while its graph is inconsistent.

## Requirements

- **SR-S081-01:** `backlog::load_graph` parses the YAML block of every work file into `FrontMatter` and reports `front.missing_key`, `front.unknown_key`, `front.parse`, and `front.too_large` with the file path and 1-based line (covers FR-F041-01).
- **SR-S081-02:** Enumerations for `status`, `priority`, `estimate`, `target_milestone`, `flag_default`, `parallel_safe`, `feature_flag`, and RFC 3339 timestamps are validated as `front.bad_value` (FR-F041-02).
- **SR-S081-03:** Ids are unique across the six directories, match the filename prefix, and match the directory kind (FR-F041-03).
- **SR-S081-04:** `parent_epic`, `parent_feature`, and `parent_story` resolve and are mutually consistent (FR-F041-05).
- **SR-S081-05:** `depends_on`, `blocks`, and `conflicts_with` resolve, the dependency graph is acyclic, `blocks` mirrors `depends_on` for features, and empty dependency lists are rejected except for E000 features and epics (FR-F041-06).
- **SR-S081-06:** Feature `depends_on` equals the plan's `Depends on` column; `validate-plan` reports missing, orphan, mis-paired, and mis-parented items (FR-F041-07, FR-F041-13).
- **SR-S081-07:** Findings are emitted sorted, as `BLOCKED:` lines, as `--json`, and as GitHub annotations with exit codes 0/1/2 (FR-F041-15, NFR-F041-04).

## Surfaces

- Infrastructure/container: none; runs with `CARGO_TARGET_DIR=/tmp/opshub-xtask-target`
- Rust service/API: `automation/xtask/src/backlog.rs` (`FrontMatter`, `WorkItem`, `WorkGraph`, `PlanRow`, `load_graph`, `parse_plan`, `check_front_matter`, `check_hierarchy`, `check_dependencies`, `check_plan_parity`); `automation/xtask/src/support.rs` (`Finding`, `Report`, `OutputFormat`); `automation/xtask/src/main.rs` (module declarations and dispatch); `automation/xtask/Cargo.toml` (`serde`, `serde_yaml`, `serde_json`, `globset`, `time`)
- Data/migration: none; reads `work/**` and `work/plan.md`
- React/UI: none (no UI)
- Mocks/fixtures: `testing/features/F041/fixtures/{valid,cycle,orphan,bad_values}` scratch trees copied by `testing/harness/repo.rs::scratch_repo`

## TDD harness

- Test path: `testing/features/F041/api/` and `testing/features/F041/requirements/`
- Feature flag: `F041_FEATURE`
- Targeted command: `cargo xtask test-feature F041`
- Full command: `cargo xtask test-all`
- First failing tests: `front_matter_missing_key_reported_with_line`, `front_matter_bad_enum_value_reported`, `duplicate_id_across_directories_rejected`, `dependency_cycle_named_in_id_order`, `plan_depends_mismatch_lists_extra_and_missing`, `json_report_has_sorted_findings_and_exit_one`

## Exit criteria

- [ ] Requirement tests SR-S081-01 through SR-S081-07 written first and failing
- [ ] Tasks T161 and T162 complete and wired through `automation/xtask/src/main.rs` dispatch for `validate-work` and `validate-plan`
- [ ] Unit and CLI integration tests pass in targeted and full modes
- [ ] Production call path named: `backlog::validate_work` and `backlog::validate_plan` dispatched from `main()` in `automation/xtask/src/main.rs`, invoked by `.githooks/pre-commit` and `.github/workflows/gates.yml`
- [ ] Handoff evidence recorded in the F041 ticket
