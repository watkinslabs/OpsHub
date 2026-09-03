---
id: T002
type: task
status: planned
parent_epic: E001
parent_feature: F001
parent_story: S001
depends_on: [T001]
owned_paths: [package.json, pnpm-workspace.yaml, apps/web/package.json, apps/web/vite.config.ts, apps/web/tsconfig.json, apps/web/src/main.tsx, apps/web/src/design/tokens.css, apps/web/src/features/platform/**, testing/features/F001/frontend/**, testing/features/F001/accessibility/**]
feature_flag: F001_FEATURE
branch: t002-react-app
started_at: null
finished_at: null
---

# T002 — React app

## Identity

- Parent story: `S001` Workspace
- Owner: platform
- Branch: `t002-react-app`

## Decision references

- `docs/architecture-decisions.md` sections 1, 6; `docs/capability-contracts.md` row F001

## Objective

Create the pnpm workspace and the Vite React 19 TypeScript application with design tokens, TanStack Router/Query providers, and a `/status` page that reads `GET /healthz`.

## Specification

- Owned paths: `package.json`, `pnpm-workspace.yaml`, `apps/web/package.json`, `apps/web/vite.config.ts`, `apps/web/tsconfig.json`, `apps/web/src/main.tsx`, `apps/web/src/design/tokens.css`, `apps/web/src/features/platform/{routes.ts, StatusPage.tsx, useHealth.ts, api.ts}`
- Contract/input: dependencies and scripts from F001 ticket section 4 (React 19, TanStack Router 1 and Query 5, lucide-react, Vite 6, TypeScript 5 strict with `noUncheckedIndexedAccess`, Vitest 3, Testing Library, Playwright, ESLint 9 flat config, Prettier 3, axe-core); Vite proxy of `/healthz` and `/api` to `http://localhost:8080`; `GET /healthz` response `{ status: "ok" | "degraded", version, checks: { name: "ok" | "failed" }[] }`.
- Output/behavior: `pnpm install --frozen-lockfile`, `pnpm --filter web lint`, `typecheck`, `test`, and `build` exit 0; `build` writes `apps/web/dist/index.html`; `/status` renders `StatusPage` with states loading, ok, degraded, unreachable, offline; query key `['platform', 'health']` refetches every 30 s; retry button refetches and moves focus to the badge; telemetry `status_page_viewed`; route registered only when `F001_FEATURE` is on.
- Dependencies: T001 workspace so `cargo xtask test-feature F001` can run; no API needed for component tests (MSW).
- Feature flag: `F001_FEATURE` read through `apps/web/src/features/platform/routes.ts`.

## TDD

- Failing test first: `testing/features/F001/frontend/StatusPage.test.tsx::status_page_renders_ok_state`, `::status_page_renders_degraded_checks`, `::status_page_shows_unreachable_with_retry`, `::status_page_offline_badge`; `testing/features/F001/accessibility/status.a11y.spec.ts::status_page_has_no_serious_axe_violations`, `::retry_moves_focus_to_badge`
- Targeted command: `cargo xtask test-feature F001`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: MSW handlers for `GET /healthz` returning ok, degraded, 503, and network error

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] `pnpm --filter web build` under 90 seconds warm; axe serious violations zero
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S001
- [ ] `finished_at` recorded
