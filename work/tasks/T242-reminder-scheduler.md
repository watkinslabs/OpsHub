---
id: T242
type: task
status: planned
parent_epic: E008
parent_feature: F061
parent_story: S121
depends_on: [S121]
owned_paths: [crates/domain/src/update-requests/**, services/worker/src/update-requests/**, services/api/src/update-requests/**, testing/features/F061/api/**, testing/features/F061/performance/**]
feature_flag: F061_FEATURE
branch: t242-reminder-scheduler
started_at: null
finished_at: null
---

# T242 — Reminder scheduler

## Identity

- Parent story: `S121` Request lifecycle
- Owner: platform
- Branch: `t242-reminder-scheduler`
- Decision references: `docs/architecture-decisions.md` sections 3, 4, 6; `docs/capability-contracts.md` row F061

## Objective

Implement the reminder pipeline for update requests: cadence arithmetic, the `reminder_schedules` claim-and-send worker job, the manual remind route with its rate limit, the expiry job, and the draft purge, all idempotent per `(recipient_id, sequence)` so a worker restart never double-notifies anyone.

## Specification

- Owned paths: `crates/domain/src/update-requests/{reminder.rs, cadence.rs}`, `services/worker/src/update-requests/{mod.rs, remind.rs, expire.rs, purge_drafts.rs}`, `services/api/src/update-requests/{handlers_remind.rs}` and the remind route entry in `routes.rs`
- Contract/input: `ReminderPolicy { cadence: none|daily|every_3_days|weekly, max_reminders: 0..=5, stop_on_response: bool }` from the request row; `RemindRequest { recipient_ids? }`; `reminder_schedules` rows `{ recipient_id, sequence, kind, state, next_run_at, attempt, notification_id }`
- Output/behavior: creation inserts `sequence 1` at `due_at - cadence` (never before `now`, never after `expires_at`); `remind.rs` runs every minute, selects `reminder_schedules where state = 'pending' and next_run_at <= now()` with `for update skip locked` in batches of 200, calls `NotificationService::create` with category `update_request` and `dedupe_key = update-request:{recipient_id}:{sequence}`, publishes `update-request.reminded.v1 { request_id, recipient_id, sequence, manual: false }`, sets `state: sent`, `sent_at`, `notification_id`, increments `update_request_recipients.reminder_count`, sets `last_reminded_at`, and inserts the next sequence unless `max_reminders` is reached, `expires_at` has passed, or the recipient is `completed` or `revoked`; a recipient response with `stop_on_response` sets remaining rows to `state: cancelled`. `handlers_remind.rs` implements `POST /api/v1/update-requests/{id}/remind`: `requester` only, `Idempotency-Key` required, sends `kind: manual` rows immediately, returns `{ sent, skipped }` with reasons, and enforces 3 manual reminders per recipient per 24 hours through the F038 `rate_limit_buckets` key `update-request-remind:{recipient_id}`. `expire.rs` runs every 5 minutes, marks lapsed requests `expired`, nulls their `token_hash` values, and cancels pending schedules. `purge_drafts.rs` deletes `update_request_responses` rows with `status = 'draft'` past `draft_expires_at`. `cadence.rs` computes the next run in the recipient's tenant timezone and is stable across DST transitions.
- Dependencies: F037 `NotificationService::create` and its 24-hour dedupe; F004 job registry, transport, and dead-letter handling; F038 rate-limit buckets; F003 `record_audit` for `update-request.remind`.
- Feature flag: `F061_FEATURE` gates the remind route and all three jobs.

## TDD

- Failing test first: `testing/features/F061/api/reminder_tests.rs::first_sequence_scheduled_before_due_date`, `::remind_job_claims_due_rows_without_duplicates`, `::concurrent_workers_send_one_notification_per_sequence`, `::remind_stops_at_max_reminders`, `::remind_stops_after_first_response`, `::remind_stops_at_expiry`, `::cadence_stable_across_dst_transition`, `::manual_remind_skips_completed_recipients`, `::manual_remind_rate_limited_after_three`, `::expire_job_marks_request_expired_and_revokes_tokens`, `::purge_drafts_removes_expired_drafts_only`; `testing/features/F061/performance/reminder_bench.rs::claim_scan_over_100k_schedules_under_2s`
- Targeted command: `cargo xtask test-feature F061`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/update_requests.rs` recorded `NotificationService` returning fixed `notification_id`s, a 100,000-row `reminder_schedules` generator, two simulated workers on the same schedule row, fixed clock `2026-09-03T00:00:00Z`, and an `Australia/Sydney` tenant for the DST case

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Jobs registered in `services/worker/src/registry.rs` and the remind route mounted behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S121
- [ ] `finished_at` recorded
