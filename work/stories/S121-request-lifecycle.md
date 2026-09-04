---
id: S121
type: story
status: planned
parent_epic: E008
parent_feature: F061
depends_on: [F061]
owned_paths: [crates/domain/src/update-requests/**, crates/persistence/src/update-requests/**, services/api/src/update-requests/**, services/worker/src/update-requests/**, apps/web/src/features/update-requests/**, services/api/migrations/*_update-requests_*.sql, testing/features/F061/api/**, testing/features/F061/database/**, testing/features/F061/performance/**]
feature_flag: F061_FEATURE
branch: s121-request-lifecycle
started_at: null
finished_at: null
---

# S121 — Request lifecycle

## Identity

- Parent feature: `F061` Update requests
- Owner: platform
- Branch: `s121-request-lifecycle`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 6; `docs/capability-contracts.md` row F061

## Vertical slice

As a sheet owner, I want to create an update request over chosen rows and columns, address it to named people, watch reminders go out on my chosen cadence, cancel it when it is no longer needed, and see exactly which recipient changed which cell, so that chasing status is a tracked, revocable, auditable operation rather than an email thread.

## Requirements

- **SR-S121-01:** `POST /api/v1/update-requests` validates the scope against the sheet, rejects columns the actor cannot write with `field_errors.column_ids`, caps the scope at 200 rows and 20 columns, mints one hashed token per recipient, and writes the whole aggregate through `UpdateRequestRepository::insert_with_scope` — the request row, one `update_request_scope_rows` row per row, one `update_request_scope_fields` row per column, one `update_request_reminder_offsets` row per scheduled reminder — with the recipient rows from `UpdateRequestRecipientRepository::insert_recipients` in the same `UnitOfWork`, keeping the `row_ids`, `column_ids`, `recipients`, and `reminder_policy` request and response shapes unchanged; publishes `update-request.sent.v1`, and notifies every recipient through F037 category `update_request` (covers FR-F061-01, FR-F061-02, FR-F061-03).
- **SR-S121-02:** `expires_at` defaults to `due_at + 7 days`, is rejected beyond 90 days after creation with `400 invalid`, and the `expire` worker job closes lapsed requests as `expired`, revokes their tokens, and cancels their pending reminders (FR-F061-02, FR-F061-09).
- **SR-S121-03:** The `remind` worker job holds no SQL: it claims due `reminder_schedules` rows through `ReminderScheduleRepository::claim_due`, which applies `for update skip locked` inside `crates/persistence`, sends through `NotificationService::create` with `dedupe_key = update-request:{recipient_id}:{sequence}`, publishes `update-request.reminded.v1`, advances the sequence to the `next_run_at` given by the request's `update_request_reminder_offsets` row for that sequence, and stops when no offset row remains, at `expires_at`, or at the first response when `stop_on_response` is set (FR-F061-10, NFR-F061-04).
- **SR-S121-04:** `POST /api/v1/update-requests/{id}/remind` sends immediately to pending, opened, and partial recipients, returns `skipped` entries with reasons for completed, revoked, and expired recipients, reuses the existing token, and returns `429 rate_limited` past 3 manual reminders per recipient per 24 hours (FR-F061-11).
- **SR-S121-05:** `POST /api/v1/update-requests/{id}/cancel` sets `cancelled`, nulls every `token_hash`, cancels pending `reminder_schedules` rows, publishes `update-request.cancelled.v1`, is idempotent on repeat, and returns `409 conflict` on a completed request (FR-F061-12).
- **SR-S121-06:** `GET /api/v1/update-requests` pages by cursor and filters by `status`, `sheet_id`, `requested_by`, and `due_before`; `GET /api/v1/update-requests/{id}` returns recipient states from `UpdateRequestRecipientRepository::list_by_request` and the per-cell `changes` list from `UpdateRequestResponseRepository::list_changes_for_request`, joining `update_request_response_values` to `update_request_scope_fields` and `cell_history` for old and new values and the contributing `recipient_id`, masking emails for non-owners (FR-F061-13).
- **SR-S121-07:** Recipient and request completion are recomputed after every applied response by `UpdateRequestResponseRepository::list_submitted_pairs`, which anti-joins `update_request_scope_rows` × `update_request_scope_fields` against `update_request_response_values`: a recipient is `completed` when nothing remains for its own submitted responses, the request is `completed` when nothing remains across all recipients, and both transitions cancel outstanding reminders through `ReminderScheduleRepository::cancel_pending_for_recipient` and `cancel_pending_for_request` (FR-F061-09).
- **SR-S121-08:** Every mutation writes an `audit_events` row through F003 `record_audit` in the same transaction, requires `Idempotency-Key`, and shares its `correlation_id` with the `cell_history` rows produced by the response (FR-F061-14).
- **SR-S121-09:** A member without `requester` on the sheet gets `403 denied` on create, remind, and cancel; a non-owner without `sheet.admin` gets `403 denied` on read; another tenant's request id returns `404 not_found` on every route (NFR-F061-02).

## Surfaces

- Infrastructure/container: worker schedules `update-requests.remind` (every minute), `update-requests.expire` (every 5 minutes), and `update-requests.purge_drafts` (nightly) registered in the F004 job registry; token pepper read from the secret manager key `update-requests/token-pepper`
- Data access: `crates/persistence/src/update-requests/{mod.rs, request_repository.rs, recipient_repository.rs, response_repository.rs, reminder_repository.rs}` hold every SQL statement for this slice — `UpdateRequestRepository` owns `update_requests`, `update_request_scope_rows`, `update_request_scope_fields`, and `update_request_reminder_offsets`; `UpdateRequestRecipientRepository` owns `update_request_recipients`; `UpdateRequestResponseRepository` owns `update_request_responses`, `update_request_response_values`, and `update_request_response_row_versions`; `ReminderScheduleRepository` owns `reminder_schedules`. The domain services, the `services/api/src/update-requests` handlers, and the `services/worker/src/update-requests` jobs depend on those traits and contain no `sqlx::query*` call or connection; create, cancel, and response-apply each run in one `UnitOfWork` (decision section 2.1)
- Rust service/API: `crates/domain/src/update-requests/{mod.rs, request.rs, recipient.rs, scope.rs, reminder.rs, completion.rs, errors.rs, service.rs}`; `services/api/src/update-requests/{mod.rs, routes.rs, handlers_request.rs, handlers_remind.rs, dto.rs}`; `services/worker/src/update-requests/{mod.rs, remind.rs, expire.rs}`
- Data/migration: `services/api/migrations/<ts>_update-requests_create_tables.sql` creating `update_requests`, `update_request_recipients`, `update_request_responses`, and `reminder_schedules` plus the child tables `update_request_scope_rows`, `update_request_scope_fields`, `update_request_reminder_offsets`, `update_request_response_values`, and `update_request_response_row_versions`, with the foreign keys, closed-enum checks, and indexes in ticket section 4
- React/UI: `apps/web/src/features/update-requests/{UpdateRequestList.tsx, UpdateRequestDetail.tsx, RecipientStatusTable.tsx, ChangeLogTable.tsx, api.ts, hooks.ts}` (the requester surfaces; the recipient page belongs to S122)
- Mocks/fixtures: `testing/fixtures/update_requests.rs` with the seeded sheet, three requests, recorded `NotificationService`, recorded outbox, fixed clock, and an `Australia/Sydney` DST case for cadence arithmetic

## TDD harness

- Test path: `testing/features/F061/{api,database,performance}/`
- Feature flag: `F061_FEATURE`
- Targeted command: `cargo xtask test-feature F061`
- Full command: `cargo xtask test-all`
- First failing tests: `create_rejects_unwritable_column`, `create_mints_one_hashed_token_per_recipient`, `create_writes_one_scope_row_and_field_row_per_pair`, `reminder_offsets_expand_cadence_once`, `expiry_beyond_ninety_days_rejected`, `remind_job_claims_due_rows_without_duplicates`, `remind_stops_after_first_response`, `manual_remind_rate_limited_after_three`, `cancel_revokes_tokens_and_pending_reminders`, `request_completes_when_every_scoped_pair_filled`, `member_cannot_create_or_cancel_request`

## Exit criteria

- [ ] Requirement tests SR-S121-01 through SR-S121-09 written first and failing
- [ ] Tasks T241 and T242 complete and wired through the API router and worker registry
- [ ] Unit, API, database, and permission tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/update-requests/routes.rs` mounted in `services/api/src/router.rs` (`/api/v1/update-requests`); `services/worker/src/update-requests/{remind.rs, expire.rs}` registered in `services/worker/src/registry.rs`
- [ ] Handoff evidence recorded in the F061 ticket
