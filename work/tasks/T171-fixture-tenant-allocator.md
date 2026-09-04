---
id: T171
type: task
status: planned
parent_epic: E000
parent_feature: F043
parent_story: S086
depends_on: [T170]
owned_paths: [automation/xtask/src/lanes.rs, .lanes/**, testing/features/F043/api/**, testing/features/F043/e2e/**]
feature_flag: F043_FEATURE
branch: t171-fixture-tenant-allocator
started_at: null
finished_at: null
---

# T171 — Fixture/tenant allocator

## Identity

- Parent story: `S086` Isolated execution
- Owner: platform
- Branch: `t171-fixture-tenant-allocator`
- Decision references: `docs/architecture-decisions.md` section 9 (isolated tenant IDs, deterministic seeds, UTC, fixed clocks, unique worker IDs); `docs/capability-contracts.md` row F043

## Objective

Implement `allocate-fixture` and lane detection so every test run inside a claimed worktree receives a deterministic, non-overlapping tenant, schema, NATS prefix, port block, clock, worker id, and seed.

## Specification

- Owned paths: `automation/xtask/src/lanes.rs` (`Fixture`, `allocate_fixture`, `fixture::derive(id, slot)`, `fixture::probe_ports`, `current_lane`, fixture half of `env::export_lines`)
- Contract/input: lane id with slot; `XTASK_OWNER`; the current directory for `current_lane`
- Output/behavior: `tenant_id = Uuid::new_v5(&Uuid::NAMESPACE_DNS, b"opshub-lane:<ID>")`, `schema = lane_<lowercase id>`, `nats_prefix = lane.<lowercase id>.`, `port_base = 20000 + slot * 10`, `clock = 2026-09-03T00:00:00Z`, `worker_id = lane-<lowercase id>`, `seed = crc32(ID)`; printed as `export OPSHUB_TEST_TENANT_ID`, `OPSHUB_TEST_SCHEMA`, `OPSHUB_TEST_NATS_PREFIX`, `OPSHUB_TEST_PORT_BASE`, `OPSHUB_TEST_CLOCK`, `OPSHUB_TEST_WORKER_ID`, `OPSHUB_TEST_SEED`, plus `CARGO_TARGET_DIR` from T170; stored under `[fixture]` in the lane file; `probe_ports` binds each of the ten ports briefly and refuses with `lane.port_in_use <port>` if any is taken; `current_lane(cwd)` returns the lane whose `worktree` is an ancestor of `cwd`; `test-feature` and `test-all` call it and export the environment for child processes
- Dependencies: T170 target allocation; F004 harness consumes the names (no code dependency)
- Feature flag: `F043_FEATURE`
- Data access (decision 2.1): `allocate_fixture` only names the schema `lane_<id>`; it opens no connection, issues no SQL, and carries no `sqlx` dependency. Creating, seeding, and dropping that schema belongs to the F004 harness runtime through `crates/persistence`.
- Crates: `uuid` with `v5`, `crc32fast`

## TDD

- Failing test first: `testing/features/F043/api/fixture_tests.rs::fixture_values_deterministic_for_lane`, `::port_block_derived_from_slot`, `::port_in_use_refused`, `::tenant_ids_differ_between_lanes`, `::current_lane_detected_from_nested_directory`, `::test_feature_inside_lane_exports_environment`, `testing/features/F043/e2e/lanes.spec.sh::two_lanes_run_concurrently_without_shared_state`, `::outside_lane_test_feature_uses_defaults`
- Targeted command: `cargo xtask test-feature F043`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: two claimed lanes in one scratch repository; a listener bound to port 20005 for the in-use case; a stub harness script that echoes its environment

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] `allocate-fixture` dispatched from `main()`; `test-feature`/`test-all` export lane environment
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S086
- [ ] `finished_at` recorded
