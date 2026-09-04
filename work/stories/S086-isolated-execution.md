---
id: S086
type: story
status: planned
parent_epic: E000
parent_feature: F043
depends_on: [S085]
owned_paths: [automation/xtask/src/lanes.rs, .lanes/**, .agent-target/**, testing/features/F043/**]
feature_flag: F043_FEATURE
branch: s086-isolated-execution
started_at: null
finished_at: null
---

# S086 — Isolated execution

## Identity

- Parent feature: `F043` Fanout orchestration
- Owner: platform
- Branch: `s086-isolated-execution`
- Decision references: `docs/architecture-decisions.md` sections 7, 9, 10; `docs/capability-contracts.md` row F043

## Vertical slice

As an agent working in a claimed lane, I want a deterministic fixture tenant, schema, NATS prefix, port block, clock, worker id, and seed injected into `test-feature` and `test-all`, and I want `collect-artifacts` to gather my test evidence into a hashed manifest that `release-lane --outcome done` requires, so that parallel lanes never share state and every lane leaves auditable proof.

## Requirements

- **SR-S086-01:** `allocate-fixture <ID>` derives `tenant_id` by UUIDv5, `schema = lane_<id>`, `nats_prefix = lane.<id>.`, `port_base = 20000 + slot * 10`, fixed clock, `worker_id`, and `seed = crc32(ID)`, prints them as `export` lines or JSON, stores them in the lane file, and probes the port block (`lane.port_in_use`) (covers FR-F043-07).
- **SR-S086-02:** `test-feature` and `test-all` detect the current lane from the worktree root and export the lane environment before running the harness (FR-F043-08).
- **SR-S086-03:** `collect-artifacts <ID>` copies junit, Playwright, axe, criterion, xtask JSON, and `commands.log` outputs into `testing/evidence/<ID>/<lane>/` and writes `manifest.json` with sorted file records and SHA-256 hashes (FR-F043-09).
- **SR-S086-04:** The manifest is deterministic apart from `collected_at` and `head_commit`, the copy is capped at 512 MiB, and symlinks leaving the worktree are refused (FR-F043-10, NFR-F043-02).
- **SR-S086-05:** `release-lane --outcome done` requires a manifest whose applicable lanes all pass, sets `finished_at`, archives the file, removes a clean worktree, frees the slot, and keeps the branch (FR-F043-11).
- **SR-S086-06:** Collection streams files with under 64 MiB resident memory (NFR-F043-01).
- **SR-S086-07:** Two lanes claimed concurrently run `test-feature` for different features at the same time with distinct schemas, prefixes, and ports, and produce two independent manifests (FR-F043-07, FR-F043-09).

## Surfaces

- Infrastructure/container: none; `allocate-fixture` only names the PostgreSQL schema, opens no connection and issues no SQL (decision 2.1), and schema and NATS stream creation from the exported names belongs to `testing/harness/db.rs` (F004 runtime) through `crates/persistence`
- Rust service/API: `automation/xtask/src/lanes.rs` (`Fixture`, `allocate_fixture`, `current_lane`, `env::export_lines` fixture half, `collect_artifacts`, `Manifest`, `LaneEvidence`, `FileRecord`, `CommandRecord`, `release` done path); `test_feature`/`test_all` in `release.rs` call `lanes::current_lane` (the call site is a one-line hook in F044's module)
- Data/migration: none; `testing/evidence/<ID>/**`
- React/UI: none (no UI)
- Mocks/fixtures: `testing/features/F043/fixtures/artifacts` (junit, trace, axe, criterion, xtask JSON samples with known hashes, one 600 MiB sparse file for the cap test, one escaping symlink)

## TDD harness

- Test path: `testing/features/F043/{api,database,e2e,accessibility,performance}/`
- Feature flag: `F043_FEATURE`
- Targeted command: `cargo xtask test-feature F043`
- Full command: `cargo xtask test-all`
- First failing tests: `fixture_values_deterministic_for_lane`, `port_block_derived_from_slot`, `test_feature_inside_lane_exports_environment`, `manifest_lists_files_sorted_with_sha256`, `artifacts_over_cap_refused`, `symlink_escape_refused`, `release_done_requires_passing_manifest`, `two_lanes_run_concurrently_without_shared_state`

## Exit criteria

- [ ] Requirement tests SR-S086-01 through SR-S086-07 written first and failing
- [ ] Tasks T171 and T172 complete; commands dispatched from `main()`
- [ ] Unit, CLI integration, persistence, E2E, accessibility, and performance tests pass in targeted and full modes
- [ ] Production call path named: `lanes::allocate_fixture`, `lanes::collect_artifacts`, `lanes::release` dispatched from `main()` in `automation/xtask/src/main.rs`; `lanes::current_lane` called from `test_feature` and `test_all`
- [ ] Handoff evidence recorded in the F043 ticket
