---
id: T218
type: task
status: planned
parent_epic: E008
parent_feature: F055
parent_story: S109
depends_on: [T217]
owned_paths: [crates/domain/src/calendar-app/**, services/api/src/calendar-app/**, testing/features/F055/api/**, testing/features/F055/requirements/**, testing/features/F055/performance/**]
feature_flag: F055_FEATURE
branch: t218-calendar-permissions
started_at: null
finished_at: null
---

# T218 — Calendar permissions

## Identity

- Parent story: `S109` Multi-source calendar
- Owner: platform
- Branch: `t218-calendar-permissions`
- Decision references: `docs/architecture-decisions.md` sections 4, 9, 10; `docs/capability-contracts.md` row F055

## Objective

Enforce calendar-level and per-source permissions, module entitlement gating, `can_edit` computation, and tenant isolation on every calendar route, with the permission-negative and performance suites proving it.

## Specification

- Owned paths: `crates/domain/src/calendar-app/{authz.rs, aggregate.rs}`, `services/api/src/calendar-app/{routes.rs, guard.rs, handlers_events.rs}`, `testing/features/F055/api/permission_tests.rs`, `testing/features/F055/performance/events_bench.rs`, `testing/features/F055/requirements/cases.md`
- Contract/input: gateway context `{ tenant_id, actor_id, roles, scopes, correlation_id }`; F003 `authz::require(actor, Permission::CalendarEdit, calendar)` for mutations and `Permission::CalendarRead` via the calendar ACL and F036 shares for reads; per-source `Permission::SheetRead`/`SheetEdit` checks and F013 view filters; `RequireModule(ModuleSlug::CalendarApp)` from `crates/auth/src/entitlements/`.
- Output/behavior: mutations require `calendar-editor` on the workspace or calendar ownership, otherwise `403 denied`; reads follow the calendar ACL; `aggregate` evaluates each source with the viewer's identity, omits unreadable sources, reports only `hidden_sources: n`, and sets `can_edit` from `SheetEdit` on the source row set; foreign-tenant IDs → `404 not_found`; non-entitled tenant → `403 denied` with `field_errors.module` before handlers run; event spans carry `tenant_id`, `calendar_id`, `source_count`, `hidden_sources`, `correlation_id`; metric `calendar_events_duration_seconds` recorded; 31-day window over 20 sources totalling 100,000 rows under 500 ms p95.
- Dependencies: T217 services; F003 engine and fixture bindings; F036 share grants for viewer access; F048 evaluator in app state.
- Feature flag: `F055_FEATURE` gates router mounting.

## TDD

- Failing test first: `testing/features/F055/api/permission_tests.rs::viewer_cannot_replace_sources`, `::viewer_cannot_patch_calendar`, `::partial_viewer_sees_only_readable_sources`, `::hidden_sources_never_include_ids`, `::can_edit_false_without_sheet_editor`, `::calendar_cross_tenant_not_found`, `::calendar_route_denied_without_entitlement`, `::guest_share_grants_read_only`; `testing/features/F055/performance/events_bench.rs::events_31_days_20_sources_p95`, `::events_per_source_cap_marks_truncated`
- Targeted command: `cargo xtask test-feature F055`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/calendar_app.rs` editor, viewer, partial viewer, guest via F036 share, tenant B; entitlement suspended variant; 100,000-row performance calendar; k6 script for the events route

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Permission-negative and performance lanes pass; requirements table maps FR-F055-01..14 and NFR-F055-01..04
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S109
- [ ] `finished_at` recorded
