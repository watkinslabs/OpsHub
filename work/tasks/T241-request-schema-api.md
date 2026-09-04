---
id: T241
type: task
status: planned
parent_epic: E008
parent_feature: F061
parent_story: S121
depends_on: [S121]
owned_paths: [services/api/migrations/*_update-requests_*.sql, crates/domain/src/update-requests/**, crates/persistence/src/update-requests/**, services/api/src/update-requests/**, testing/features/F061/api/**, testing/features/F061/database/**]
feature_flag: F061_FEATURE
branch: t241-request-schema-api
started_at: null
finished_at: null
---

# T241 — Request schema and API

## Identity

- Parent story: `S121` Request lifecycle
- Owner: platform
- Branch: `t241-request-schema-api`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 6; `docs/capability-contracts.md` row F061

## Objective

Create the `update-requests` schema and implement request creation with scope validation and per-recipient hashed tokens, the list and detail reads, cancellation, and the completion evaluator, so that S121 has a persisted, audited request aggregate for the reminder and recipient work to build on.

## Specification

- Owned paths: `services/api/migrations/<ts>_update-requests_create_tables.sql` and `.down.sql`, `crates/domain/src/update-requests/{mod.rs, request.rs, recipient.rs, scope.rs, completion.rs, errors.rs, service.rs}`, `crates/persistence/src/update-requests/{mod.rs, request_repository.rs, recipient_repository.rs, response_repository.rs}`, `services/api/src/update-requests/{mod.rs, routes.rs, handlers_request.rs, dto.rs}`
- Contract/input: `CreateUpdateRequest { sheet_id, title, message, row_ids, column_ids, recipients, due_at, expires_at?, allow_partial, reminder_policy }`; list query `{ cursor?, limit?, status?, sheet_id?, requested_by?, due_before? }`; `CancelRequest { reason? }`; secret manager key `update-requests/token-pepper`
- Output/behavior: routes `GET /api/v1/update-requests`, `POST /api/v1/update-requests`, `GET /api/v1/update-requests/{id}`, `POST /api/v1/update-requests/{id}/cancel`. `scope.rs` verifies every `row_id` belongs to `sheet_id` and every `column_id` is writable by the actor under F003 `cell.write`, rejects formula and system columns, caps the scope at 200 rows and 20 columns, and emits the opaque `row_key` and `field_key` values that `UpdateRequestRepository::insert_with_scope` writes as one `update_request_scope_rows` row per row, one `update_request_scope_fields` row per column, and one `update_request_reminder_offsets` row per scheduled reminder expanded from `cadence` and `max_reminders`. `recipient.rs` mints one 32-byte CSPRNG token per recipient, stores only its SHA-256 `token_hash`, and returns the link once in the send payload. Creation publishes `update-request.sent.v1` and calls `NotificationService::create` per recipient with category `update_request`. `completion.rs` recomputes recipient and request status after each applied response. Cancel sets `cancelled`, nulls every `token_hash`, cancels pending `reminder_schedules` rows, and publishes `update-request.cancelled.v1`. Detail returns recipient states and the per-cell `changes` list with masked emails for non-owners. DDL creates `update_requests`, `update_request_recipients`, `update_request_responses`, and `reminder_schedules` together with `update_request_scope_rows`, `update_request_scope_fields`, `update_request_reminder_offsets`, `update_request_response_values`, and `update_request_response_row_versions`, with the declared foreign keys, the closed-enum `check` constraints on `status`, `cadence`, `kind`, `state`, and `reason`, the composite foreign keys from the response child tables into the two scope tables, the unique and partial indexes, and the `update_request_responses_append_only` trigger from ticket section 4. No array or queried `jsonb` column is created; `update_request_response_values.value` is the module's only `jsonb` column.
- Data access: all SQL for this task lives in `crates/persistence/src/update-requests/` — `UpdateRequestRepository` (`update_requests`, `update_request_scope_rows`, `update_request_scope_fields`, `update_request_reminder_offsets`) with `insert_with_scope`, `load_scope`, `count_removed_scope_rows`, `list_by_filters`, `mark_cancelled`, `mark_completed`; `UpdateRequestRecipientRepository` (`update_request_recipients`) with `insert_recipients`, `list_by_request`, `revoke_all_for_request`; `UpdateRequestResponseRepository` (`update_request_responses`, `update_request_response_values`, `update_request_response_row_versions`) with `list_submitted_pairs` and `list_changes_for_request`. `scope.rs`, `completion.rs`, `service.rs`, and the handlers contain no `sqlx::query*` call; create and cancel each commit in one `UnitOfWork` alongside the F003 audit write and the outbox enqueue (decision section 2.1).
- Dependencies: F008 row versions and `cell_history` for the `changes` list; F007 column metadata for writability; F003 `record_audit` and permission checks; F037 `NotificationService::create`; F004 secret manager.
- Feature flag: `F061_FEATURE` gates the routes; the migration runs regardless.

## TDD

- Failing test first: `testing/features/F061/database/migration_tests.rs::update_request_tables_exist_with_constraints`, `::token_hash_unique_where_present`, `::responses_append_only_trigger_blocks_value_update`, `::scope_row_key_unique_per_request`, `::scope_field_column_unique_per_request`, `::response_value_outside_scope_violates_foreign_key`, `::reminder_offset_sequence_bounded`, `::closed_enum_checks_reject_unknown_status_cadence_kind_state`, `::rollback_drops_update_request_tables`; `testing/features/F061/api/request_tests.rs::create_rejects_unwritable_column`, `::create_rejects_row_outside_sheet`, `::create_caps_scope_at_200_rows_and_20_columns`, `::create_mints_one_hashed_token_per_recipient`, `::expiry_beyond_ninety_days_rejected`, `::detail_masks_email_for_non_owner`, `::cancel_revokes_tokens_and_pending_reminders`, `::cancel_on_completed_returns_conflict`, `::request_completes_when_every_scoped_pair_filled`, `::member_cannot_create_or_cancel_request`, `::foreign_tenant_request_not_found`
- Targeted command: `cargo xtask test-feature F061`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/update_requests.rs` seeded sheet `Site works` with 250 rows and a formula column, requester, sheet-admin, member, three recipients; recorded `NotificationService` and outbox; fixed token seed and clock `2026-09-03T00:00:00Z`

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; routes registered behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S121
- [ ] `finished_at` recorded
