---
id: T147
type: task
status: planned
parent_epic: E004
parent_feature: F037
parent_story: S074
depends_on: [S074]
owned_paths: [services/api/migrations/*_notifications_*.sql, crates/domain/src/notifications/**, crates/persistence/src/notifications/**, services/api/src/notifications/**, services/worker/src/notifications/**, apps/web/src/features/notifications/**, testing/features/F037/api/**, testing/features/F037/frontend/**]
feature_flag: F037_FEATURE
branch: t147-preferences-quiet-hours-digest
started_at: null
finished_at: null
---

# T147 — Preferences/quiet hours/digest

## Identity

- Parent story: `S074` Preferences and digests
- Owner: platform
- Branch: `t147-preferences-quiet-hours-digest`
- Decision references: `docs/architecture-decisions.md` sections 2, 4, 7; `docs/capability-contracts.md` row F037

## Objective

Implement the preference store and routes, quiet-hours deferral and release, digest scheduling and sending, and the `/settings/notifications` page with the channel matrix, digest, quiet hours, and push enrolment.

## Specification

- Owned paths: `services/api/migrations/<ts>_notifications_preferences.sql` and `.down.sql`, `crates/domain/src/notifications/{preferences.rs, quiet_hours.rs, digest.rs}`, `crates/persistence/src/notifications/{notification_preference_repository.rs, digest_schedule_repository.rs}`, `services/api/src/notifications/handlers_preferences.rs`, `services/worker/src/notifications/{send_digest.rs, quiet_hours_release.rs}`, `apps/web/src/features/notifications/{PreferencesPage.tsx, ChannelMatrix.tsx, DigestSettings.tsx, QuietHoursSettings.tsx, PushEnableButton.tsx, routes.ts}`
- Contract/input: `PutPreferencesRequest { scope?: user|tenant, channels: { <category>: { in_app, email, push } }, digest: { cadence: none|hourly|daily, send_at_local (HH:MM), timezone (IANA) }, quiet_hours: { start_local, end_local, timezone, enabled } }` with `If-Match` on `version` and `Idempotency-Key`; `PreferencesResponse` returns the same shape plus `version`. The nested body is unchanged on the wire: `NotificationPreferenceRepository` composes it from `notification_channel_preferences` rows and the typed `digest_*` and `quiet_hours_*` columns on read, and decomposes it back into rows and columns on write.
- Output/behavior: routes `GET /api/v1/notification-preferences` and `PUT /api/v1/notification-preferences`; resolution order unchanged — `resolve_effective_preferences(tenant_id, user_id)` reads the user's row and its channel rows, then the tenant-default row (`user_id is null`) and its own channel rows, then built-in defaults — a two-row lookup joined to `notification_channel_preferences`, not a JSON merge; `replace_channel_preferences(preference_id, rows)` and the parent update run in one `UnitOfWork`; `in_app` for `approval` and `system` is protected and returns `NotificationError::ProtectedChannel → 400 invalid` with `field_errors.channels`; `scope = tenant` requires `tenant-admin` and otherwise returns `403 denied`; a stale `version` returns `NotificationError::StaleVersion → 409 conflict`; `quiet_hours.rs` computes the window end from `quiet_hours_start`, `quiet_hours_end`, and `quiet_hours_timezone` across DST — one window that applies on every weekday, so no per-weekday table exists — and routing sets `next_attempt_at` for email and push while in-app stays immediate and `system` ignores the window, with `quiet_hours_release.rs` re-queueing at the boundary; `digest.rs` stores non-`approval`, non-`system` email deliveries as `digested` when `digest_cadence` is `hourly` or `daily`, and `send_digest.rs` takes schedules only from `DigestScheduleRepository::claim_due_digests(now, limit)`, whose `for update skip locked` claim on the `digest_schedules` row still serializes the same writers, sends one email of up to 200 items grouped by category, marks them `sent`, publishes `digest.sent.v1 { recipient_id, item_count }`, and calls `advance_digest(schedule_id, next_run_at)` in the same `UnitOfWork` even for an empty window; neither job nor handler holds a SQL string, a `sqlx::query*` call, or a connection; audit events `preferences.update` and `preferences.tenant-default.update` are written and no domain event is published; DDL for `notification_preferences` (with `digest_cadence text not null default 'none' check (digest_cadence in ('none','hourly','daily'))`, `digest_send_at_local time null`, `digest_timezone text null`, `quiet_hours_enabled boolean not null default false`, `quiet_hours_start time null`, `quiet_hours_end time null`, `quiet_hours_timezone text null`, a check that a non-`none` cadence carries both digest fields and a check that an enabled window carries all three quiet-hours fields), `notification_channel_preferences(id uuid pk, tenant_id uuid not null, preference_id uuid not null references notification_preferences(id) on delete cascade, category text not null check (category in ('mention','assignment','approval','share','review','update_request','workflow','system')), channel text not null check (channel in ('in_app','email','push')), enabled boolean not null default true, created_at timestamptz not null, updated_at timestamptz not null)` with `unique (preference_id, category, channel)` and index `(preference_id, enabled)`, and `digest_schedules` with the cadence check, `unique (tenant_id, coalesce(user_id, '00000000-0000-0000-0000-000000000000'))` on preferences, `unique (tenant_id, user_id)` on schedules, and the `digest_schedules(next_run_at)` index; the down migration drops `notification_channel_preferences` with the other tables it created; the settings page uses a labelled table matrix with row and column headers, shows `Preferences saved`, `Preferences changed elsewhere` on conflict, and `Blocked in browser settings` when push permission is denied.
- Dependencies: T145 router and delivery rows; T146 push subscription registration used by `PushEnableButton`; F004 scheduler and secret manager; F002 user timezones and `tenant-admin` role.
- Feature flag: `F037_FEATURE` gates the routes, both jobs, and the `/settings/notifications` route entry.

## TDD

- Failing test first: `testing/features/F037/api/preferences_tests.rs::preferences_resolve_user_then_tenant_then_default`, `::protected_in_app_channel_cannot_be_disabled`, `::tenant_scope_put_requires_admin`, `::stale_version_put_returns_conflict`, `::preference_update_writes_audit_and_publishes_no_event`, `::cross_tenant_preferences_return_not_found`, `::put_replaces_channel_rows_and_returns_nested_body`, `::channel_preference_pair_is_unique_per_preference`; `testing/features/F037/api/quiet_hours_tests.rs::quiet_hours_defer_email_not_in_app`, `::system_category_ignores_quiet_hours`, `::quiet_hours_boundary_survives_dst_shift`, `::quiet_hours_release_requeues_at_window_end`; `testing/features/F037/api/digest_tests.rs::digest_bundles_items_and_publishes_sent`, `::approval_email_bypasses_digest`, `::empty_digest_window_sends_nothing`, `::digest_caps_at_200_items`, `::concurrent_digest_workers_send_once`; `testing/features/F037/frontend/preferences_tests.tsx::matrix_disables_protected_in_app_checkboxes`, `::conflict_shows_stale_banner`, `::push_button_shows_blocked_state`
- Targeted command: `cargo xtask test-feature F037`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/notifications.rs` users `quiet` (20:00–07:00 Europe/Berlin) and `digest` (daily 08:00 America/New_York); fixed clock with timezone advance helpers across both DST transitions; recording email adapter capturing digest bodies; two-worker harness for the skip-locked claim

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; routes, jobs, and the settings route registered behind the flag; OpenAPI regenerated without drift
- [ ] `cargo xtask check-persistence` passes
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S074
- [ ] `finished_at` recorded
