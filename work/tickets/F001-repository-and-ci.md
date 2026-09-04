---
id: F001
type: feature
status: planned
priority: P0
owner: platform
estimate: 5
target_milestone: M1
parent_epic: E001
depends_on: [F041, F042]
blocks: [F002, F004]
conflicts_with: []
parallel_safe: true
owned_paths: [Cargo.toml, rust-toolchain.toml, .cargo/config.toml, rustfmt.toml, clippy.toml, crates/*/Cargo.toml, services/*/Cargo.toml, package.json, pnpm-workspace.yaml, apps/web/package.json, apps/web/vite.config.ts, apps/web/tsconfig.json, apps/web/src/main.tsx, apps/web/src/features/platform/**, .github/workflows/**, testing/features/F001/**]
feature_flag: F001_FEATURE
flag_default: off
branch: f001-repository-and-ci
started_at: null
finished_at: null
---

# F001 — Repository and CI

## 1. Identity and dates

- Branch: `f001-repository-and-ci`
- Capability area: platform foundation (spec section 7 Phase 0, section 8 release gates)
- Module slug: `platform`; aggregate `repository`
- Kind: tooling feature; no HTTP routes and no domain events

### Decision references

- Architecture: `docs/architecture-decisions.md` sections 1 (runtime and repository), 9 (testing), 10 (ticket gate)
- Canonical contract: `docs/capability-contracts.md` row F001 (surface `cargo build --workspace`, `pnpm --filter web build`, CI workflow `gates.yml`; events none; persistence `Cargo.toml`, `apps/web/package.json`, `.github/workflows/**`; role maintainer)

## 2. Requirement specification

### Problem and user outcome

There is no buildable monorepo. Every later feature needs a Cargo workspace with the five shared crates and four services, a React application that compiles, and a CI pipeline that refuses invalid backlog items, forbidden attribution, oversized files, and failing tests before a merge.

As a maintainer, I want a clean checkout to build both the Rust workspace and the web app with one command each, and I want every pull request gated by the same checks locally and in CI, so that agents and humans fan out on independent lanes without breaking `main`.

### Functional requirements

- **FR-F001-01:** On a clean checkout with Rust stable from `rust-toolchain.toml`, `cargo build --workspace` exits 0 and produces binaries `api`, `worker`, `realtime`, `mcp`, and `xtask`; a cold CI run finishes in under 10 minutes.
- **FR-F001-02:** The root `Cargo.toml` lists exactly the members `crates/domain`, `crates/persistence`, `crates/contracts`, `crates/auth`, `crates/events`, `services/api`, `services/worker`, `services/realtime`, `services/mcp`, `automation/xtask`; every member declares `edition = "2024"` and inherits `axum`, `tokio`, `sqlx`, `serde`, `tracing`, `utoipa`, `uuid`, `chrono` from `[workspace.dependencies]`.
- **FR-F001-03:** `cargo fmt --all --check` and `cargo clippy --workspace --all-targets -- -D warnings` exit 0 on `main`; any warning in a member crate exits 1 in the `rust` CI job.
- **FR-F001-04:** `pnpm install --frozen-lockfile && pnpm --filter web build` exits 0 and writes `apps/web/dist/index.html`; `pnpm --filter web typecheck` runs `tsc --noEmit` under `strict: true`.
- **FR-F001-05:** `pnpm --filter web dev` serves the app on port 5173 with route `/status` rendering the `StatusPage` that calls `GET /readyz` — not `/healthz`, which carries only a process-level status — and renders each component F004 reports with its state and latency, showing `ok`, `degraded`, or `unreachable`.
- **FR-F001-06:** `.github/workflows/gates.yml` defines five jobs named `validate-work`, `rust`, `web`, `policy`, and `line-limit`; all five are required status checks and a pull request into `main` cannot merge while any of them is failing or missing.
- **FR-F001-07:** The `validate-work` job runs `cargo xtask validate-work`, `validate-plan`, `validate-tickets`, `check-contracts`, `check-migrations`, `check-persistence`, `check-roles`, `check-design`, and `check-references` in that order and exits 1 with the `BLOCKED:` lines from the first failing command.
- **FR-F001-08:** The `policy` job runs `cargo xtask self-test`, `cargo xtask audit-range origin/main..HEAD`, and `cargo xtask audit-pr title.txt body.txt`; a commit message, title, or body containing a forbidden attribution token fails the job with output starting `BLOCKED:`.
- **FR-F001-15:** A `supply-chain` job runs on every pull request and nightly on `main`: `cargo audit` against the RustSec advisory database and `pnpm audit --audit-level=high`, both failing the build on a high or critical advisory with no fix available marked as an explicit, expiring exception rather than a silent ignore; a licence check refusing any dependency outside the allow-list (MIT, Apache-2.0, BSD-2/3, ISC, Unicode, Zlib) so a copyleft or unlicensed package cannot arrive unnoticed; and an SBOM in CycloneDX format generated for both workspaces and uploaded as a release artifact, because answering "are we affected by this CVE" requires knowing what shipped. Version pins and lockfiles are already enforced by FR-F001-04; this job covers what pinning cannot, which is that a pinned version became vulnerable after it was pinned.
- **FR-F001-09:** The `line-limit` job fails with `<path>: <n> lines; limit is 500` for any tracked text file over 500 lines and passes otherwise.
- **FR-F001-10:** The `rust` job starts service containers `postgres:18` and `nats:2.11` with JetStream enabled, exports `DATABASE_URL` and `NATS_URL`, runs `cargo test --workspace`, and uploads JUnit output to the artifact `rust-junit`.
- **FR-F001-11:** The `web` job runs `pnpm lint`, `pnpm typecheck`, `pnpm test -- --reporter=junit`, and `pnpm build`, and uploads `apps/web/dist` and the JUnit file as artifact `web-build`.
- **FR-F001-12:** Workflow runs use `concurrency: { group: gates-${{ github.ref }}, cancel-in-progress: true }`; pushes that change only `docs/**` or `*.md` outside `work/` skip `rust` and `web` through path filters while `validate-work`, `policy`, and `line-limit` always run.
- **FR-F001-13:** `.cargo/config.toml` honors `CARGO_TARGET_DIR` so `cargo xtask allocate-target <ID>` gives each lane an isolated target directory; two lanes building concurrently never share `target/`.
- **FR-F001-14:** `cargo xtask test-feature F001` and `cargo xtask test-all` exit 0 on a clean checkout once this feature is merged, and every job writes its evidence under `testing/evidence/F001/`.

### Non-functional requirements

- **NFR-F001-01 Performance:** warm `cargo build --workspace` with cache restored finishes under 4 minutes; `pnpm --filter web build` under 90 seconds; the full `gates.yml` run under 15 minutes wall clock.
- **NFR-F001-02 Security/privacy:** workflows use pinned action SHAs, `permissions: contents: read` by default, no secrets in logs, `pnpm` with `--frozen-lockfile`, and `cargo deny check advisories` in the `rust` job.
- **NFR-F001-03 Accessibility:** the `/status` page passes axe with zero serious violations, has a single `h1`, and announces state changes through a polite live region.
- **NFR-F001-04 Reliability/observability:** CI jobs are retry-safe (idempotent caches, no shared mutable state), each job emits a step summary, and flaky-test retries are disabled so failures are attributable.

### Scope

Included: Cargo workspace and toolchain pins, shared dependency versions, lint configuration, pnpm workspace, Vite/React/TypeScript baseline, `/status` page, `gates.yml` with five jobs, required-check configuration, evidence upload, lane-isolated target directories.

Excluded: xtask commands themselves (F041, F042, F043, F044), container images and compose (F004), domain crates' real code (F002 onward), authentication (F038), any product UI beyond `/status`.

## 3. UX specification

- Surface: command line and GitHub checks. No UI beyond the `/status` page.
- Entry points: `cargo build --workspace`, `pnpm --filter web build`, `pnpm --filter web dev` then browser route `/status`, pull request checks tab.
- `/status` states: loading (spinner with `aria-busy`), success (`ok` badge with build SHA and API version), degraded (`degraded` badge listing failed dependencies), error (`unreachable` badge with retry button and correlation ID if the response carried one), offline (badge `offline` when `navigator.onLine` is false).
- CI output: every failing gate prints one `BLOCKED:` line per finding with path and reason; the job summary lists findings as a markdown table.
- Keyboard: retry button is a native `button`; focus is moved to the status badge after retry completes; motion respects `prefers-reduced-motion`.
- Font/icon/design tokens: the `/status` page uses only browser defaults and two Lucide icons `Activity`, `RefreshCw`; it ships before F062 and deliberately consumes no design token, so F001 owns no file under `apps/web/src/design/`.

- Design: `design/artboards/Status.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

### Rust backend

- Root `Cargo.toml`: `[workspace] resolver = "3"`, members listed in FR-F001-02, `[workspace.package] edition = "2024", rust-version = "1.89", license = "UNLICENSED"`.
- `[workspace.dependencies]` pins: `axum = "0.8"`, `tokio = { version = "1", features = ["full"] }`, `sqlx = { version = "0.8", features = ["runtime-tokio", "postgres", "uuid", "chrono", "json", "migrate"] }`, `serde = { version = "1", features = ["derive"] }`, `serde_json = "1"`, `tracing = "0.1"`, `tracing-subscriber = { version = "0.3", features = ["env-filter", "json"] }`, `utoipa = { version = "5", features = ["axum_extras", "uuid", "chrono"] }`, `uuid = { version = "1", features = ["v7", "serde"] }`, `chrono = { version = "0.4", features = ["serde"] }`, `thiserror = "2"`, `anyhow = "1"`.
- `[workspace.lints.rust] unsafe_code = "forbid"`; `[workspace.lints.clippy] pedantic = "warn", unwrap_used = "warn", expect_used = "warn", module_name_repetitions = "allow"`; CI passes `-D warnings`.
- Each member crate: `crates/<name>/Cargo.toml` with `lints.workspace = true`, a `src/lib.rs` exporting an empty `pub mod` placeholder; `services/<name>/Cargo.toml` with `[[bin]]` and a `main.rs` that starts Tokio and logs `service started`.
- `rust-toolchain.toml`: `channel = "stable"`, `components = ["rustfmt", "clippy"]`, `profile = "minimal"`.
- `.cargo/config.toml`: `[build] target-dir = "target"` overridable by `CARGO_TARGET_DIR`; `[env] SQLX_OFFLINE = "true"`; `[alias] xtask = "run --package xtask --"`.
- `rustfmt.toml`: `edition = "2024"`, `max_width = 110`; `clippy.toml`: `too-many-arguments-threshold = 8`.
- Data access (decision 2.1): this feature owns no table and adds no repository. The `sqlx` pin lives in `[workspace.dependencies]` but only `crates/persistence` declares it as a member dependency, so every table is reached through a repository class in that crate; `crates/domain`, the four services, and `automation/xtask` take no SQLx dependency in their skeleton manifests, and the F068 `check-persistence` gate keeps it that way.
- Error mapping: none (no runtime code); build failures map to non-zero process exit and `BLOCKED:` lines from xtask.

### PostgreSQL/SQLx

- No tables in this feature. The `rust` job provisions `postgres:18` with `POSTGRES_DB=opshub_test`, `POSTGRES_USER=opshub`, and `DATABASE_URL=postgres://opshub:opshub@localhost:5432/opshub_test`, and runs `cargo sqlx database create` so later features' migration tests have a database.
- `SQLX_OFFLINE=true` in `.cargo/config.toml` so builds never need a live database; `cargo sqlx prepare --check --workspace` runs in the `rust` job once any query macros exist (F002 onward).
- `services/api/migrations/` is created empty with a `.gitkeep`; `cargo xtask check-migrations` reports `no migrations created`.

### React/TypeScript

No UI beyond the `/status` page. The real surface is CLI commands and workflow YAML.

- `pnpm-workspace.yaml`: `packages: ["apps/*"]`; root `package.json` scripts `lint`, `typecheck`, `test`, `build` fan out with `pnpm -r`.
- `apps/web/package.json`: `react@19`, `react-dom@19`, `@tanstack/react-router@1`, `@tanstack/react-query@5`, `lucide-react`, dev `vite@6`, `typescript@5`, `vitest@3`, `@testing-library/react`, `@playwright/test`, `eslint@9` flat config, `prettier@3`, `axe-core`; scripts `dev`, `build`, `preview`, `lint`, `typecheck`, `test`, `e2e`.
- `apps/web/tsconfig.json`: `strict`, `noUncheckedIndexedAccess`, `verbatimModuleSyntax`, `moduleResolution: bundler`, path alias `@/*`.
- `apps/web/vite.config.ts`: React plugin, `server.port = 5173`, proxy `/healthz` and `/api` to `http://localhost:8080`, `build.sourcemap = true`.
- `apps/web/src/main.tsx` mounts `RouterProvider` and `QueryClientProvider`; `apps/web/src/features/platform/{routes.ts, StatusPage.tsx, useHealth.ts, api.ts}`; query key `['platform', 'health']`, refetch every 30 s; telemetry event `status_page_viewed` with `state`.
- Workflow `gates.yml` (YAML surface): trigger `pull_request` and `push` to `main`; jobs and steps per FR-F001-06 through FR-F001-12; caches `~/.cargo/registry`, `target`, and the pnpm store keyed by lockfile hashes; `actions/upload-artifact` for `rust-junit`, `web-build`, and `testing/evidence/F001/**`.
- Commands: `cargo build --workspace`, `cargo fmt --all --check`, `cargo clippy --workspace --all-targets -- -D warnings`, `cargo test --workspace`, `cargo deny check advisories`, `pnpm install --frozen-lockfile`, `pnpm --filter web build`, `cargo xtask validate-work`, `cargo xtask audit-range origin/main..HEAD`, `cargo xtask audit-pr title.txt body.txt`, `cargo xtask self-test`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F001-01 through FR-F001-14 in `testing/features/F001/requirements/cases.md`
- [ ] Failure/edge-case tests: missing workspace member, clippy warning injected, 501-line file, attribution token in commit body, lockfile drift
- [ ] Permission-negative tests: branch protection rejects direct push to `main` by a non-maintainer; a check cannot be skipped by editing the workflow in the same PR
- [ ] Rust unit tests: none beyond crate smoke tests (`lib.rs` compiles, `main` starts)
- [ ] API contract/integration tests: workflow and command assertions in `testing/features/F001/api/`
- [ ] Database migration/constraint tests: service container boot and empty migration dir in `testing/features/F001/database/`
- [ ] React component tests: `StatusPage` states in `testing/features/F001/frontend/`
- [ ] Browser E2E tests: clean checkout build, dev server and `/status`, PR gate flow
- [ ] Accessibility tests: axe on `/status`, keyboard retry, live region
- [ ] Performance/load tests: cold/warm build times and workflow wall clock

### Fast fanout configuration

- Test harness path: `testing/features/F001/`
- Feature flag: `F001_FEATURE`
- Fixture/seed factory: `testing/fixtures/platform.rs` creates a temporary git clone with a fixture commit, an oversized file, and a poisoned commit message for gate tests
- Deterministic test data: fixed commit SHAs from the fixture repository, fixed clock `2026-09-03T00:00:00Z`
- Mock/stub contracts: `act`-style local workflow runner for `gates.yml`; MSW handler for `GET /healthz`
- Parallel isolation: each lane gets `CARGO_TARGET_DIR=.agent-target/<ID>` and a temporary clone
- Targeted command: `cargo xtask test-feature F001`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F001/`

## 6. Acceptance criteria

```gherkin
Feature: Repository and CI gates

Scenario: Clean checkout builds
  Given a fresh clone of main with the pinned toolchain
  When a maintainer runs cargo build --workspace and pnpm --filter web build
  Then both commands exit 0 and apps/web/dist/index.html exists

Scenario: Forbidden attribution blocks the pull request
  Given a pull request whose commit body contains a forbidden attribution token
  When the policy job runs cargo xtask audit-range origin/main..HEAD
  Then the job fails with a line starting BLOCKED: and the PR cannot merge

Scenario: Oversized file blocks the pull request
  Given a pull request adding a 501-line Rust file
  When the line-limit job runs
  Then it fails with "<path>: 501 lines; limit is 500"

Scenario: Non-maintainer cannot bypass gates
  Given a contributor without maintainer rights
  When they push directly to main or dismiss a failing required check
  Then the push is rejected by branch protection and the check remains required
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F041 (work-item schema commands), F042 (policy gate commands); decisions sections 1, 9, 10; contracts row F001
- Blocks: F002, F004
- Conflicts with: none (disjoint owned paths; xtask source belongs to F041/F042)
- External dependencies: GitHub Actions runners, `postgres:18` and `nats:2.11` images, crates.io and npm registries
- Risks and mitigations: dependency drift breaks builds, so all versions are pinned and Renovate-style bumps go through the same gates; cold cache builds exceed the budget, so registry and target caches are keyed by lockfile hash and restored per job; a workflow edit in the same PR could weaken gates, so branch protection requires the five named checks and workflow files require maintainer review.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F041 and F042 accepted so `cargo xtask validate-work` and `audit-range` exist
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F001/`
- [ ] Owned paths claimed; branch protection rules agreed with repository admins
- [ ] Fixture repository builder available in `testing/fixtures/platform.rs`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] `gates.yml` green on `main` with all five required checks
- [ ] Cold and warm build budgets met and recorded in `testing/evidence/F001/performance/`
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: reverting the workflow file restores the previous gate set without breaking builds
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Adds the Cargo workspace, pnpm workspace, toolchain pins, lint configuration, and the `/status` page. Design tokens and the shared UI library arrive with F062.
- Adds `gates.yml` with `validate-work`, `rust`, `web`, `policy`, and `line-limit` required checks. No migrations. `F001_FEATURE` gates only the `/status` route.
