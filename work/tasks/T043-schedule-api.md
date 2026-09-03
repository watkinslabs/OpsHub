---
id: T043
type: task
status: planned
parent_epic: E003
parent_feature: F011
parent_story: S022
depends_on: [T042]
owned_paths: [crates/domain/src/schedules/**, services/api/src/schedules/**, testing/features/F011/api/**, testing/features/F011/performance/**]
feature_flag: F011_FEATURE
branch: t043-schedule-api
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4
- Capability contract: `docs/capability-contracts.md` row F011

# T043 — Schedule API

## Identity

- Parent story: `S022` Working time
- Owner: platform
- Branch: `t043-schedule-api`
- Decision references: `docs/architecture-decisions.md` sections 2–4; `docs/capability-contracts.md` row F011

## Objective

Implement sheet schedule settings, the schedule read model, and single-row reschedule so that views and engines have one calendar-aware date operation.

## Specification

- Owned paths: `crates/domain/src/schedules/{settings.rs, schedule_read.rs, service_reschedule.rs}`, `services/api/src/schedules/{handlers_settings.rs, handlers_schedule.rs, handlers_reschedule.rs}`
- Contract/input: `PutScheduleSettingsRequest { start_column_id, end_column_id, duration_column_id?, milestone_column_id?, percent_complete_column_id?, calendar_id, timezone }`; `GET /schedule` query `{ cursor?, limit? ≤ 500 }`; `RescheduleRequest { start?, end?, duration? }` with headers `Idempotency-Key`, `If-Match`.
- Output/behavior: `PUT /api/v1/sheets/{sheet_id}/schedule-settings` validates column types via F007 and returns `ScheduleSettingsResponse`; `GET /api/v1/sheets/{sheet_id}/schedule` returns `ScheduleResponse { settings, calendar, display_timezone, rows: Page<RowSchedule> }`; `POST /api/v1/rows/{id}/reschedule` loads the row and settings, computes the missing member with `calendar_math`, applies `snap_start`/`snap_end`, enforces milestone zero duration and the `parent_rollup` rejection, writes cells through the F006 row update path with `If-Match`, and returns `RowResponse` plus `snap_applied`; events `schedule-settings.updated.v1`, `row.rescheduled.v1`; metric `schedule_reschedule_duration_ms`; errors map per ticket section 4.
- Dependencies: T042 calendar service; F006 `update_row`; F007 column type lookup; F009 `rollup_rules` lookup (absent table treated as no rules); F049 user timezone hook returns `None` until F049 lands.
- Feature flag: `F011_FEATURE`

## TDD

- Failing test first: `testing/features/F011/api/settings_tests.rs::settings_rejects_type_mismatch`, `::settings_requires_same_type_for_start_and_end`, `::settings_cross_tenant_not_found`; `testing/features/F011/api/schedule_tests.rs::schedule_read_marks_unscheduled`, `::schedule_read_uses_sheet_timezone`, `::reschedule_computes_end_from_duration`, `::reschedule_snaps_start_off_holiday`, `::reschedule_rejects_end_before_start`, `::reschedule_milestone_forces_zero_duration`, `::reschedule_parent_with_rollup_rejected`, `::reschedule_viewer_denied`; `testing/features/F011/performance/schedule_bench.rs::schedule_read_100k_p95`, `::reschedule_p95`
- Targeted command: `cargo xtask test-feature F011`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: seeded sheet with date columns and 50 rows; 100,000-row generator with fixed seed

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] p95 targets from NFR-F011-01 met in the performance lane
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S022
- [ ] `finished_at` recorded
