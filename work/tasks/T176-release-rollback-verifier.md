---
id: T176
type: task
status: planned
parent_epic: E000
parent_feature: F044
parent_story: S088
depends_on: [T175]
owned_paths: [automation/xtask/src/release.rs, testing/evidence/**, testing/features/F044/api/**, testing/features/F044/database/**, testing/features/F044/e2e/**]
feature_flag: F044_FEATURE
branch: t176-release-rollback-verifier
started_at: null
finished_at: null
---

# T176 — Release/rollback verifier

## Identity

- Parent story: `S088` Release evidence
- Owner: platform
- Branch: `t176-release-rollback-verifier`
- Decision references: `docs/architecture-decisions.md` sections 9, 10; spec section 8 release gates; `docs/capability-contracts.md` row F044

## Objective

Implement `verify-release <ID>` and `--milestone M#` so a feature is declared releasable only from archived work items, passing lane evidence, passing gates, and rollback proof, recorded as a signed JSON file.

## Specification

- Owned paths: `automation/xtask/src/release.rs` (`ReleaseRecord`, `RollbackEvidence`, `InputHash`, `Gates`, `verify_release`, `verify_milestone`, `signature`, `evidence::{read_manifest, read_rollback, write_atomic}`, `test_feature`, `test_all` moved from `main.rs`), `testing/evidence/<ID>/release.json`, `testing/evidence/milestones/M#.json`
- Contract/input: feature id or milestone; `WorkGraph`; `testing/evidence/<ID>/manifest.json` (F043 schema); `testing/evidence/<ID>/rollback.json` `{ flag_off_verified, migration_down_verified, commands, commit }`; `testing/features/<ID>/feature.toml` `lanes_not_applicable = [{ lane, reason }]`; role from `XTASK_ROLE=release-manager` or `GITHUB_ACTIONS=true` with `GITHUB_REF=refs/heads/main`
- Output/behavior: gate lines `contracts: pass|fail`, `migrations: pass (<n> files)|fail`, `flags: pass|fail`, `lanes: <k>/7 pass`, `rollback: verified at <commit>|missing`; findings `release.not_archived`, `release.child_open`, `release.lane_missing`, `release.lane_failed`, `release.gate_failed`, `release.rollback_missing`, `release.notes_missing`; on success writes `release.json` with `inputs` hashes (ticket, stories, tasks, manifest, rollback, catalog, OpenAPI when present), `signature = sha256(sorted input hashes joined by "\n")`, atomically; without the role prints `dry run: release-manager role required to record` and exits 3 without writing; `--milestone` iterates features by `target_milestone`, writes `M#.json` `{ milestone, verified_at, features: { <id>: signature }, failures: { <id>: [findings] } }` and fails if any feature fails
- Dependencies: T175 flag gate; T173 and T174 gates; F043 manifest schema
- Feature flag: `F044_FEATURE`
- Budget: under 5 s per feature, 30 s per 10-feature milestone

## TDD

- Failing test first: `testing/features/F044/api/release_tests.rs::verify_release_refuses_unarchived_ticket`, `::verify_release_refuses_open_child_task`, `::verify_release_refuses_failed_lane`, `::verify_release_accepts_not_applicable_lane_with_reason`, `::verify_release_refuses_missing_rollback`, `::verify_release_refuses_empty_release_notes`, `::verify_release_dry_run_without_role_writes_nothing`, `::verify_release_ci_main_records`, `::verify_release_signature_stable_across_runs`, `::milestone_run_lists_every_failing_feature`, `testing/features/F044/database/evidence_tests.rs::release_json_written_atomically`, `::release_json_inputs_hash_match_files`, `testing/features/F044/e2e/release.spec.sh::full_release_flow_after_collect_artifacts`
- Targeted command: `cargo xtask test-feature F044`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/features/F044/fixtures/release` with archived `F900`, `S900`, `S901`, `T900`–`T903`, passing and failing manifests, `rollback.json`; `XTASK_NOW` fixed; `GITHUB_ACTIONS`/`GITHUB_REF` set per case

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] `verify-release` dispatched from `main()`; `test-feature`/`test-all` live in `release.rs` and inject lane environment via `lanes::current_lane`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S088
- [ ] `finished_at` recorded
