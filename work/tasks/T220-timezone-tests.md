---
id: T220
type: task
status: planned
parent_epic: E008
parent_feature: F055
parent_story: S110
depends_on: [T219]
owned_paths: [testing/features/F055/**]
feature_flag: F055_FEATURE
branch: t220-timezone-tests
started_at: null
finished_at: null
---

# T220 — Timezone tests

## Identity

- Parent story: `S110` Publishing
- Owner: platform
- Branch: `t220-timezone-tests`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 6, 9; `docs/capability-contracts.md` row F055

## Objective

Complete the F055 harness with daylight-saving and timezone suites across API, ICS, and UI, plus the E2E, accessibility, and ICS performance lanes, so every FR/NFR has executable evidence before acceptance.

## Specification

- Owned paths: `testing/features/F055/api/timezone_tests.rs`, `testing/features/F055/database/constraint_tests.rs`, `testing/features/F055/e2e/calendar.spec.ts`, `testing/features/F055/accessibility/calendar.a11y.spec.ts`, `testing/features/F055/performance/{ics_bench.rs, reschedule_bench.rs}`, `testing/features/F055/requirements/cases.md` (final traceability), `testing/features/F055/README.md`
- Contract/input: fixture rows on every 2026 transition (Europe/London 2026-03-29 and 2026-10-25, America/Los_Angeles 2026-03-08 and 2026-11-01, Australia/Sydney 2026-04-05 and 2026-10-04), sources with `timezone_source` `tenant`, `column:<id>`, and `fixed:<zone>`; RFC 5545 parser helper; Playwright sessions per role with browser timezone emulation; 5,000-event generator.
- Output/behavior: timezone suite proves nonexistent local times (01:30 → 02:30 spring forward) and ambiguous times (fall back) resolve deterministically and identically in `GET /events`, the ICS feed, and the rendered grid; all-day events never gain an offset; `duration_column_id` across a transition keeps wall-clock duration; `tz` switch in the UI updates every event chip and the week gutter; E2E covers create → add sources → switch zone → drag reschedule → publish → fetch ICS in an external-client simulation → revoke → 404; accessibility covers axe on three layouts, roving-tabindex grid, keyboard reschedule announcements, color text labels; performance covers ICS 5,000 events under 2 s, reschedule p95 under 800 ms; the requirements table maps FR-F055-01..14 and NFR-F055-01..04 to case IDs with lanes.
- Data access: no test opens a connection or issues SQL of its own — every fixture calendar, source, column-map row, and publication is written through the `crates/persistence/src/calendar-app/` repositories and every assertion reads back through them, so the suites exercise the production path (decision section 2.1). `constraint_tests.rs` asserts the normalized shape at the database level: `calendar_source_column_maps` rejects a duplicate `(source_id, role)`, rejects a `role` outside `start|end|duration|title|color`, and blocks deleting a mapped column through its foreign key; a source without a `start` or `title` role row is rejected; `timezone_source_kind` must match its payload column; and no `jsonb` column exists in the module's four tables.
- Dependencies: T219 UI and ICS route; F011 working calendars for reschedule; F049 tenant zone settings.
- Feature flag: `F055_FEATURE` on for the suite; one E2E case runs with the flag off and asserts the navigation entry is absent and the ICS route returns not-found.

## TDD

- Failing test first: `testing/features/F055/api/timezone_tests.rs::spring_forward_nonexistent_time_shifts_forward`, `::fall_back_ambiguous_time_not_duplicated`, `::all_day_events_have_no_offset`, `::duration_keeps_wall_clock_across_transition`, `::ics_matches_events_api_for_three_zones`; `testing/features/F055/database/constraint_tests.rs::column_map_rejects_duplicate_role`, `::column_map_rejects_unknown_role`, `::column_delete_blocked_by_map_foreign_key`, `::source_requires_start_and_title_roles`, `::timezone_source_kind_requires_matching_payload`; `testing/features/F055/e2e/calendar.spec.ts::create_sources_switch_zone_reschedule_publish`, `::viewer_is_read_only`; `testing/features/F055/accessibility/calendar.a11y.spec.ts::three_layouts_have_no_serious_axe_violations`; `testing/features/F055/performance/ics_bench.rs::ics_5000_events_under_2s`
- Targeted command: `cargo xtask test-feature F055`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: DST fixture sheets from `testing/fixtures/calendar_app.rs`; Playwright `timezoneId` emulation; RFC 5545 parser; k6 script for ICS and reschedule

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Timezone, E2E, accessibility, and performance lanes pass; evidence stored under `testing/evidence/F055/`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S110
- [ ] `finished_at` recorded
