---
id: T048
type: task
status: planned
parent_epic: E003
parent_feature: F012
parent_story: S024
depends_on: [T047]
owned_paths: [apps/web/src/features/dependencies/**, testing/features/F012/e2e/**, testing/features/F012/accessibility/**, testing/features/F012/performance/**]
feature_flag: F012_FEATURE
branch: t048-schedule-e2e
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 6, 9
- Capability contract: `docs/capability-contracts.md` row F012

# T048 — Schedule E2E

## Identity

- Parent story: `S024` Schedule shifts
- Owner: platform
- Branch: `t048-schedule-e2e`
- Decision references: `docs/architecture-decisions.md` sections 6, 9; `docs/capability-contracts.md` row F012

## Objective

Prove the full dependency, critical-path, and shift path through the browser with Playwright, the accessibility lane with axe and keyboard-only flows, and the performance lane with the large-schedule benchmarks, fixing any UI gaps found.

## Specification

- Owned paths: `testing/features/F012/e2e/{gantt.spec.ts, shift.spec.ts}`, `testing/features/F012/accessibility/gantt.a11y.spec.ts`, `testing/features/F012/performance/{critical_path_bench.rs, shift_bench.rs}`, `apps/web/src/features/dependencies/{GanttChart.tsx, ShiftDialog.tsx, DependencyDialog.tsx}` for fixes only
- Contract/input: seeded tenant with the 12-row schedule (parent, milestone, holiday exception, 9 links), editor and viewer logins, foreign-tenant login; performance fixtures of 10,000 rows/20,000 links and a 1,000-successor chain.
- Output/behavior: E2E covers link creation with lag and successor movement, cycle rejection text, critical toggle, drag shift preview and commit persisting after reload, keyboard-only shift, viewer read-only, and non-member not-found; accessibility covers zero serious axe violations, focusable bars and arrows with labels, live-region announcements, focus trap in dialogs, contrast on critical bars, reduced motion; performance covers critical path p95 under 500 ms, 1,000-successor shift p95 under 800 ms, dependency list p95 under 500 ms, and the 10,000-row budget rejection under 2 s.
- Dependencies: T047 Gantt and shift route; Playwright harness from `testing/harness/`; seeded fixture from `testing/fixtures/dependencies.rs`.
- Feature flag: `F012_FEATURE` enabled for the test tenant.

## TDD

- Failing test first: `testing/features/F012/e2e/gantt.spec.ts::link_tasks_and_successor_moves`, `::cycle_rejected_in_dialog`, `::critical_path_toggle_highlights_chain`; `testing/features/F012/e2e/shift.spec.ts::drag_shift_preview_then_commit_persists`, `::keyboard_only_shift`, `::viewer_cannot_shift`; `testing/features/F012/accessibility/gantt.a11y.spec.ts::gantt_has_no_serious_axe_violations`, `::bars_and_arrows_keyboard_reachable`, `::shift_announced_by_live_region`; `testing/features/F012/performance/shift_bench.rs::shift_1000_successors_p95`, `::shift_budget_rejects_under_2s`
- Targeted command: `cargo xtask test-feature F012`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: real API against a seeded tenant; no MSW in this lane

## Exit criteria

- [ ] Tests written before fixes and observed failing where a gap exists
- [ ] E2E, accessibility, and performance lanes pass in targeted and full modes
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S024 and the F012 ticket
- [ ] `finished_at` recorded
