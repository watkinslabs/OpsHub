---
id: T172
type: task
status: planned
parent_epic: E000
parent_feature: F043
parent_story: S086
depends_on: [T171]
owned_paths: [automation/xtask/src/lanes.rs, .lanes/**, testing/features/F043/api/**, testing/features/F043/database/**, testing/features/F043/frontend/**, testing/features/F043/performance/**]
feature_flag: F043_FEATURE
branch: t172-artifact-collector
started_at: null
finished_at: null
---

# T172 — Artifact collector

## Identity

- Parent story: `S086` Isolated execution
- Owner: platform
- Branch: `t172-artifact-collector`
- Decision references: `docs/architecture-decisions.md` section 9; `docs/capability-contracts.md` row F043

## Objective

Implement `collect-artifacts` with a hashed, deterministic manifest and the `release-lane --outcome done` path that requires it, so every finished lane leaves auditable evidence under `testing/evidence/<ID>/`.

## Specification

- Owned paths: `automation/xtask/src/lanes.rs` (`Manifest`, `LaneEvidence`, `EvidenceStatus`, `FileRecord`, `CommandRecord`, `collect_artifacts`, `artifacts::{sources, copy_streaming, hash}`, `release` done path)
- Contract/input: lane id; sources under `<target_dir>`: `junit/**/*.xml` → lane by filename prefix (`api_`, `database_`, `requirements_`, `frontend_`), `playwright/**` → `e2e`, `axe/*.json` → `accessibility`, `criterion/**/estimates.json` → `performance`, `xtask/*.json` → `xtask`, `commands.log` → `commands`; harness `feature.toml` `lanes_not_applicable` list
- Output/behavior: files copied to `testing/evidence/<ID>/<lane>/` preserving relative paths, streamed in 1 MiB chunks with SHA-256 computed during copy; `manifest.json` with `{ id, branch, base_commit, head_commit, collected_at, owner, lanes: { <lane>: { status, files: [{ path, sha256, bytes }] } }, commands: [...] }`, files sorted by path; lane `status` is `pass` when every junit file has zero failures/errors (and axe reports zero serious/critical), `fail` otherwise, `missing` when no files; cap 512 MiB total → `artifacts.too_large` listing the five largest files; symlink leaving the worktree → `artifacts.symlink_escape`; `release-lane --outcome done` requires every applicable lane `pass`, rewrites `status: done` and `finished_at`, moves the file to `work/archived/`, refuses `lane.dirty` on uncommitted changes, removes the worktree, frees the slot, deletes the lane file, keeps the branch
- Dependencies: T171 lane detection; T169 release plumbing
- Feature flag: `F043_FEATURE`
- Crates: `sha2`, `serde_json`

## TDD

- Failing test first: `testing/features/F043/api/artifacts_tests.rs::manifest_lists_files_sorted_with_sha256`, `::lane_status_from_junit_and_axe`, `::artifacts_over_cap_refused`, `::symlink_escape_refused`, `::release_done_requires_passing_manifest`, `::release_done_refuses_dirty_worktree`, `::release_done_archives_and_frees_slot`, `testing/features/F043/database/evidence_tests.rs::second_collection_identical_file_list`, `testing/features/F043/frontend/output_tests.rs::manifest_json_schema`, `testing/features/F043/performance/collect_bench.rs::collect_500mb_under_64mb_resident`
- Targeted command: `cargo xtask test-feature F043`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/features/F043/fixtures/artifacts` with known hashes, a failing junit file, a 600 MiB sparse file, and an escaping symlink

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] `collect-artifacts` and `release-lane --outcome done` dispatched from `main()`; F044 `verify-release` can read the manifest
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S086
- [ ] `finished_at` recorded
