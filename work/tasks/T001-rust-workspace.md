---
id: T001
type: task
status: planned
parent_epic: E001
parent_feature: F001
parent_story: S001
depends_on: [S001]
owned_paths: [Cargo.toml, rust-toolchain.toml, .cargo/config.toml, rustfmt.toml, clippy.toml, crates/*/Cargo.toml, services/*/Cargo.toml, testing/features/F001/api/**, testing/features/F001/database/**]
feature_flag: F001_FEATURE
branch: t001-rust-workspace
started_at: null
finished_at: null
---

# T001 — Rust workspace

## Identity

- Parent story: `S001` Workspace
- Owner: platform
- Branch: `t001-rust-workspace`

## Decision references

- `docs/architecture-decisions.md` section 1; `docs/capability-contracts.md` row F001

## Objective

Create the Cargo workspace with five crates, four services, pinned toolchain, shared dependencies, lint policy, and lane-isolated target directories so `cargo build --workspace` passes on a clean checkout.

## Specification

- Owned paths: `Cargo.toml`, `rust-toolchain.toml`, `.cargo/config.toml`, `rustfmt.toml`, `clippy.toml`, `crates/{domain,persistence,contracts,auth,events}/Cargo.toml`, `services/{api,worker,realtime,mcp}/Cargo.toml`
- Contract/input: member list and `[workspace.dependencies]` pins from F001 ticket section 4 (axum 0.8, tokio 1, sqlx 0.8 with `runtime-tokio, postgres, uuid, chrono, json, migrate`, serde 1, tracing 0.1, utoipa 5, uuid 1 v7, chrono 0.4); `[workspace.lints]` with `unsafe_code = "forbid"` and clippy pedantic subset; `rust-toolchain.toml` stable with rustfmt and clippy; `.cargo/config.toml` alias `xtask = "run --package xtask --"`, `SQLX_OFFLINE = "true"`, target dir overridable by `CARGO_TARGET_DIR`.
- Output/behavior: `cargo build --workspace` exits 0 and produces `api`, `worker`, `realtime`, `mcp`, `xtask`; `cargo fmt --all --check` and `cargo clippy --workspace --all-targets -- -D warnings` exit 0; each crate ships `src/lib.rs` (or `main.rs` logging `service started`) so later features add modules without touching this task's files; `services/api/migrations/.gitkeep` exists.
- Dependencies: `automation/xtask` already exists (F041/F042) and is added as a member without modification.
- Feature flag: `F001_FEATURE` (build configuration is not gated; the flag only gates the `/status` route in T002)
- Large-table note: none; no database objects.

## TDD

- Failing test first: `testing/features/F001/api/workspace_tests.rs::workspace_members_match_contract`, `::cargo_build_workspace_exits_zero`, `::clippy_warning_fails_build`, `::target_dir_override_isolates_lanes`; `testing/features/F001/database/ci_database_tests.rs::sqlx_offline_build_needs_no_database`
- Targeted command: `cargo xtask test-feature F001`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/platform.rs` temporary clone; tests shell out to `cargo` with `CARGO_TARGET_DIR` set per test

## Exit criteria

- [ ] Tests written before the workspace files and observed failing
- [ ] Clean-checkout build under 10 minutes cold on CI, under 4 minutes warm
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S001
- [ ] `finished_at` recorded
