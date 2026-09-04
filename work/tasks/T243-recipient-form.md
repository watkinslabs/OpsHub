---
id: T243
type: task
status: planned
parent_epic: E008
parent_feature: F061
parent_story: S122
depends_on: [S122]
owned_paths: [crates/domain/src/update-requests/**, crates/persistence/src/update-requests/**, services/api/src/update-requests/**, apps/web/src/features/update-requests/**, testing/features/F061/api/**, testing/features/F061/frontend/**]
feature_flag: F061_FEATURE
branch: t243-recipient-form
started_at: null
finished_at: null
---

# T243 — Recipient form

## Identity

- Parent story: `S122` Recipient experience
- Owner: platform
- Branch: `t243-recipient-form`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 6; `docs/capability-contracts.md` row F061

## Objective

Implement the two unauthenticated recipient routes and the React surfaces on both sides of the request: the token-scoped public form with drafts, partial submission, and conflict handling, and the requester dialog, list, and detail views that create and monitor requests.

## Specification

- Owned paths: `crates/domain/src/update-requests/{public.rs, response.rs, validate.rs}`, `services/api/src/update-requests/{handlers_public.rs, public_dto.rs}`, `apps/web/src/features/update-requests/{PublicRequestPage.tsx, PublicRowCard.tsx, DraftBar.tsx, ConflictPanel.tsx, TerminalNotice.tsx, RequestUpdateDialog.tsx, ScopePicker.tsx, RecipientPicker.tsx, ReminderPolicyEditor.tsx, UpdateRequestList.tsx, UpdateRequestDetail.tsx, RecipientStatusTable.tsx, ChangeLogTable.tsx, api.ts, publicApi.ts, hooks.ts, routes.ts}`
- Contract/input: `GET /public/update-requests/{token}` returning `PublicScopeResponse { title, message, requester_display_name, due_at, expires_at, status, allow_partial, removed_count, rows }`; `POST /public/update-requests/{token}/responses` taking `SubmitResponseRequest { values, row_versions, comment, submit }` with `Idempotency-Key`, returning `SubmitResponseResult { response_id, cells_updated, recipient_status, request_status }`
- Output/behavior: `public.rs` resolves the recipient by constant-time SHA-256 `token_hash` comparison, treats unknown, revoked, and expired tokens identically as `404 not_found`, marks `opened_at` on first load, and projects cells through `scope_keys` so no `sheet_id`, `row_id`, `column_id`, `tenant_id`, or user id ever leaves the boundary; responses set `Referrer-Policy: no-referrer`, `X-Robots-Tag: noindex`, and `Cache-Control: no-store`. `validate.rs` runs the F007 column validator per field and returns `field_errors.<row_key>.<field_key>`. `response.rs` writes the immutable `update_request_responses` row first, checks `row_versions` against current row versions and returns `409 conflict` with current values on any mismatch, then applies cells through the F008 `apply_cell_edits` path with `source: update_request` and `source_id: recipient_id`, re-checking the requester's `cell.write` permission before the write; `submit: false` stores a 7-day draft that writes nothing; replay under the same `Idempotency-Key` returns the stored result. The React public page renders per-row `fieldset` cards in one column, a sticky progress bar, `Save draft` backed by `localStorage` under `update-request-draft:{token}`, an offline badge, a `ConflictPanel` with a `Use current` control, and a `TerminalNotice` for expired, cancelled, and completed links; the requester dialog drives scope, recipients, message, due date, and cadence, and the list and detail views show status, recipients, and the per-cell change log.
- Dependencies: F007 validators; F008 cell apply path and row versions; F038 rate-limit buckets on both public routes; T241 schema and `scope_keys`; F003 permission re-check at apply time.
- Feature flag: `F061_FEATURE` gates the public routes and the web routes; a disabled flag renders the standard not-found page.

## TDD

- Failing test first: `testing/features/F061/api/public_tests.rs::public_scope_omits_internal_identifiers`, `::revoked_and_expired_tokens_return_same_not_found`, `::first_load_marks_recipient_opened`, `::field_key_outside_scope_returns_not_found`, `::invalid_value_returns_field_errors`, `::stale_row_version_returns_conflict_with_current_values`, `::submission_replay_returns_original_result`, `::response_row_written_before_cell_apply`, `::requester_permission_revoked_rejects_apply`, `::submit_rate_limited_after_thirty`; `testing/features/F061/frontend/PublicRequestPage.test.tsx::renders_only_scoped_fields_with_current_values`, `::save_draft_persists_and_restores`, `::conflict_panel_offers_use_current`, `::terminal_notice_for_cancelled_link`; `testing/features/F061/frontend/RequestUpdateDialog.test.tsx::blocks_send_without_recipient_or_column`
- Targeted command: `cargo xtask test-feature F061`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/update_requests.rs` tokens for open, completed, cancelled, and expired recipients; MSW handlers for both public routes and the four authenticated routes; Vitest with `localStorage` reset per test; Playwright profile with no session cookie

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Public routes mounted outside the session layer and the web routes registered behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S122
- [ ] `finished_at` recorded
