---
id: S088
type: story
status: planned
parent_epic: E000
parent_feature: F044
depends_on: [S087]
owned_paths: [automation/xtask/src/release.rs, testing/evidence/**, testing/features/F044/**]
feature_flag: F044_FEATURE
branch: s088-release-evidence
started_at: null
finished_at: null
---

# S088 — Release evidence

## Identity

- Parent feature: `F044` Contract/release control
- Owner: platform
- Branch: `s088-release-evidence`
- Decision references: `docs/architecture-decisions.md` sections 9, 10; `docs/capability-contracts.md` row F044

## Vertical slice

As a release manager, I want `check-flags` to enforce the flag registry and lifecycle and `verify-release` to assemble lane evidence, gate results, and rollback proof into a signed record per feature and per milestone, so that a release decision is reproducible from repository content alone.

## Requirements

- **SR-S088-01:** `check-flags` parses `crates/contracts/src/feature_flags.rs` into `FlagDef` values and enforces ticket flag names and defaults, registry-to-ticket parity, harness `feature.toml` parity, and that every code reference names a registered flag (covers FR-F044-10).
- **SR-S088-02:** Lifecycle rules produce `flag.stale`, `flag.premature_default`, and `flag.removed_reference` from milestone and archive state (FR-F044-11).
- **SR-S088-03:** `verify-release <ID>` requires archived ticket, stories, and tasks, a passing F043 manifest for every applicable lane, passing contract, migration, and flag gates, `rollback.json`, and non-empty release notes, with one finding code per missing element (FR-F044-12).
- **SR-S088-04:** On success `release.json` is written atomically with input hashes and a deterministic signature; repeated runs on unchanged inputs give the same signature (FR-F044-13, NFR-F044-04).
- **SR-S088-05:** Without `XTASK_ROLE=release-manager` or CI on `main`, the command performs a dry run and exits 3 without writing (FR-F044-14).
- **SR-S088-06:** `--milestone M#` verifies every feature with that `target_milestone` and writes `testing/evidence/milestones/M#.json` (FR-F044-15).
- **SR-S088-07:** `verify-release` completes in under 5 s per feature and 30 s per 10-feature milestone, with `--json` and gate lines in text mode (FR-F044-16, NFR-F044-01, NFR-F044-03).

## Surfaces

- Infrastructure/container: none
- Rust service/API: `automation/xtask/src/release.rs` (`FlagDef`, `FlagState`, `load_flags`, `check_flag_registry`, `check_flag_references`, `check_flag_lifecycle`, `check_flags`, `ReleaseRecord`, `RollbackEvidence`, `InputHash`, `verify_release`, `verify_milestone`, `signature`, `test_feature`, `test_all`)
- Data/migration: none; writes `testing/evidence/<ID>/release.json` and `testing/evidence/milestones/M#.json`
- React/UI: none (no UI)
- Mocks/fixtures: `testing/features/F044/fixtures/{flags,release}` with a registry source, code files referencing flags, an archived `F900` with two stories and four tasks, a passing and a failing F043 manifest, and `rollback.json`

## TDD harness

- Test path: `testing/features/F044/{api,database,e2e,frontend,accessibility}/`
- Feature flag: `F044_FEATURE`
- Targeted command: `cargo xtask test-feature F044`
- Full command: `cargo xtask test-all`
- First failing tests: `unregistered_flag_reference_reported_with_line`, `archived_feature_with_stale_flag_reported`, `verify_release_refuses_open_child_task`, `verify_release_refuses_failed_lane`, `verify_release_dry_run_without_role_writes_nothing`, `verify_release_signature_stable_across_runs`, `milestone_run_lists_every_failing_feature`

## Exit criteria

- [ ] Requirement tests SR-S088-01 through SR-S088-07 written first and failing
- [ ] Tasks T175 and T176 complete; `check-flags` and `verify-release` dispatched from `main()`
- [ ] Unit, CLI integration, persistence, E2E, and accessibility tests pass in targeted and full modes
- [ ] Production call path named: `release::check_flags`, `release::verify_release`, `release::verify_milestone` dispatched from `main()` in `automation/xtask/src/main.rs`; `check-flags` invoked by `gates.yml`; `verify-release` invoked by the release manager or the CI `main` job
- [ ] Handoff evidence recorded in the F044 ticket
