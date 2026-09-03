---
id: S001
type: story
status: planned
parent_epic: E001
parent_feature: F001
depends_on: [F041, F042]
owned_paths: [Cargo.toml, rust-toolchain.toml, .cargo/config.toml, rustfmt.toml, clippy.toml, crates/*/Cargo.toml, services/*/Cargo.toml, package.json, pnpm-workspace.yaml, apps/web/package.json, apps/web/vite.config.ts, apps/web/tsconfig.json, apps/web/src/main.tsx, apps/web/src/features/platform/**, testing/features/F001/**]
feature_flag: F001_FEATURE
branch: s001-workspace
started_at: null
finished_at: null
---

# S001 — Workspace

## Identity

- Parent feature: `F001` Repository and CI
- Owner: platform
- Branch: `s001-workspace`

## Decision references

- `docs/architecture-decisions.md` sections 1 (runtime and repository), 6 (web experience), 9 (testing)
- `docs/capability-contracts.md` row F001

## Vertical slice

As a maintainer, I want a clean checkout to build the Rust workspace and the web app with one command each and serve a `/status` page, so that every later feature has a compiling monorepo to land in.

## Requirements

- **SR-S001-01:** Root `Cargo.toml` declares the ten members from FR-F001-02 with `edition = "2024"`, shared `[workspace.dependencies]`, and `[workspace.lints]`; `cargo build --workspace` exits 0 and yields the five binaries (covers FR-F001-01, FR-F001-02).
- **SR-S001-02:** `cargo fmt --all --check` and `cargo clippy --workspace --all-targets -- -D warnings` exit 0; an injected `let unused = 1;` in any crate makes clippy exit 1 (FR-F001-03).
- **SR-S001-03:** `pnpm install --frozen-lockfile && pnpm --filter web build` exits 0 and writes `apps/web/dist/index.html`; `pnpm --filter web typecheck` passes under `strict: true` (FR-F001-04).
- **SR-S001-04:** `pnpm --filter web dev` serves `/status`, which renders `StatusPage` from `GET /healthz` with loading, `ok`, `degraded`, `unreachable`, and offline states (FR-F001-05, NFR-F001-03).
- **SR-S001-05:** `.cargo/config.toml` respects `CARGO_TARGET_DIR`; two concurrent builds with different values never touch the same `target/` (FR-F001-13).
- **SR-S001-06:** The web baseline boots and renders `/status` using browser defaults only: it imports no stylesheet from `apps/web/src/design/`, loads no web font, and owns no design token, so F062 can introduce the token set and the shared UI library without contending for a file (decisions section 6).

## Surfaces

- Infrastructure/container: none (F004 owns compose and images)
- Rust service/API: `Cargo.toml`, `rust-toolchain.toml`, `.cargo/config.toml`, `rustfmt.toml`, `clippy.toml`, `crates/{domain,persistence,contracts,auth,events}/Cargo.toml`, `services/{api,worker,realtime,mcp}/Cargo.toml`
- Data/migration: none; `services/api/migrations/.gitkeep` only
- React/UI: `package.json`, `pnpm-workspace.yaml`, `apps/web/{package.json, vite.config.ts, tsconfig.json}`, `apps/web/src/main.tsx`, `apps/web/src/features/platform/{routes.ts, StatusPage.tsx, useHealth.ts, api.ts}`
- Mocks/fixtures: MSW handler for `GET /healthz`; `testing/fixtures/platform.rs` temporary clone builder

## TDD harness

- Test path: `testing/features/F001/{api,frontend,accessibility,performance}/`
- Feature flag: `F001_FEATURE`
- Targeted command: `cargo xtask test-feature F001`
- Full command: `cargo xtask test-all`
- First failing tests: `workspace_members_match_contract`, `cargo_build_workspace_exits_zero`, `clippy_warning_fails_build`, `web_build_writes_index_html`, `status_page_renders_ok_state`

## Exit criteria

- [ ] Requirement tests SR-S001-01 through SR-S001-06 written first and failing
- [ ] Tasks T001 and T002 complete; `cargo build --workspace` and `pnpm --filter web build` green locally
- [ ] Unit, API-lane command tests, React, accessibility, and performance budgets pass in targeted and full modes
- [ ] Production call path named: `apps/web/src/features/platform/routes.ts` mounted at `/status` in `apps/web/src/main.tsx`
- [ ] Handoff evidence recorded in the F001 ticket
