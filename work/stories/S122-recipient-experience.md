---
id: S122
type: story
status: planned
parent_epic: E008
parent_feature: F061
depends_on: [F061]
owned_paths: [crates/domain/src/update-requests/**, services/api/src/update-requests/**, apps/web/src/features/update-requests/**, testing/features/F061/api/**, testing/features/F061/frontend/**, testing/features/F061/e2e/**, testing/features/F061/accessibility/**]
feature_flag: F061_FEATURE
branch: s122-recipient-experience
started_at: null
finished_at: null
---

# S122 — Recipient experience

## Identity

- Parent feature: `F061` Update requests
- Owner: platform
- Branch: `s122-recipient-experience`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 6; `docs/capability-contracts.md` row F061

## Vertical slice

As a person who was asked to update some cells — often without an OpsHub account, often on a phone — I want a link that shows only the fields I was asked about with their current values, lets me save a draft and come back, tells me when someone else has changed a row since I opened it, and confirms exactly what I updated, so that answering takes a minute and I never see or touch data I was not asked about.

## Requirements

- **SR-S122-01:** `GET /public/update-requests/{token}` runs with no session, resolves the recipient by constant-time comparison of the SHA-256 `token_hash`, marks the recipient `opened` with `opened_at` on first load, and returns only `row_key`/`field_key` addressed cells with labels, types, options, validation, current values, and `row_version` (covers FR-F061-04, FR-F061-03).
- **SR-S122-02:** The public payload never contains `sheet_id`, `workspace_id`, `tenant_id`, `row_id`, `column_id`, or user ids, and the response carries `Referrer-Policy: no-referrer`, `X-Robots-Tag: noindex`, and `Cache-Control: no-store`; unknown, revoked, and expired tokens all return the same `404 not_found` body (FR-F061-04, NFR-F061-02).
- **SR-S122-03:** `POST /public/update-requests/{token}/responses` requires `Idempotency-Key`, validates every value with the F007 column validator, returns `field_errors.<row_key>.<field_key>` on failure, returns `404 not_found` for any key outside the scope snapshot, and is limited to 30 submissions per hour per token and IP and 300 per day per token with `429 rate_limited` and `Retry-After` (FR-F061-05).
- **SR-S122-04:** An accepted submission writes the immutable `update_request_responses` row before touching the sheet and then applies the cells through the F008 `apply_cell_edits` path with `source: update_request`, publishing `cell.updated.v1` and `update-request.responded.v1`; a replay with the same `Idempotency-Key` returns the original result and writes nothing further (FR-F061-06, NFR-F061-04).
- **SR-S122-05:** `submit: false` stores a resumable draft for 7 days that writes no cells; `submit: true` over part of the scope is accepted when `allow_partial` and marks the recipient `partial`; with `allow_partial` false a gap returns `400 invalid` with reason `incomplete` and writes nothing (FR-F061-07).
- **SR-S122-06:** A submitted `row_versions.<row_key>` that no longer matches the row returns `409 conflict` listing each stale row with its current version and values, records the response as `rejected` with reason `stale_row`, and writes no cell of that submission (FR-F061-08).
- **SR-S122-07:** Submissions after the recipient or request reaches `completed`, `cancelled`, or `expired` return `409 conflict` with reason `closed`, and the public page renders a distinct terminal screen for each of those states naming the requester and showing no cell data (FR-F061-09, FR-F061-15).
- **SR-S122-08:** The recipient page is a single-column mobile-first form of per-row `fieldset` groups with a sticky progress bar, a `Save draft` action backed by `localStorage` under `update-request-draft:{token}`, an offline badge, and a submit confirmation naming the number of updated cells; it is completable by keyboard alone, announces draft and submit results through a polite live region, and passes axe with zero serious or critical violations at 320 px (FR-F061-15, NFR-F061-03).

## Surfaces

- Infrastructure/container: public routes mounted outside the tenant-session layer with the F038 `rate_limit_buckets` limiter keyed `update-request:{token_hash}:{ip_hash}`; static assets for the public page served without the app shell's authenticated bundle
- Rust service/API: `crates/domain/src/update-requests/{public.rs, response.rs, validate.rs}`; `services/api/src/update-requests/{handlers_public.rs, public_dto.rs}` mounted at `/public/update-requests`
- Data/migration: reads `update_requests.scope_keys` and `update_request_recipients.token_hash`; writes `update_request_responses` under the append-only trigger from ticket section 4 (migration itself is owned by T241)
- React/UI: `apps/web/src/features/update-requests/{PublicRequestPage.tsx, PublicRowCard.tsx, DraftBar.tsx, ConflictPanel.tsx, TerminalNotice.tsx, RequestUpdateDialog.tsx, ScopePicker.tsx, RecipientPicker.tsx, ReminderPolicyEditor.tsx, publicApi.ts}`
- Mocks/fixtures: `testing/fixtures/update_requests.rs` tokens for an open, a completed, a cancelled, and an expired recipient; MSW handlers for the two public routes; Playwright runs the public page with no session cookie

## TDD harness

- Test path: `testing/features/F061/{api,frontend,e2e,accessibility}/`
- Feature flag: `F061_FEATURE`
- Targeted command: `cargo xtask test-feature F061`
- Full command: `cargo xtask test-all`
- First failing tests: `public_scope_omits_internal_identifiers`, `revoked_and_expired_tokens_return_same_not_found`, `field_key_outside_scope_returns_not_found`, `draft_writes_no_cells_and_resumes`, `partial_submit_marks_recipient_partial`, `incomplete_submit_rejected_when_partial_disabled`, `stale_row_version_returns_conflict_with_current_values`, `submission_replay_returns_original_result`, `public_form_completable_by_keyboard`

## Exit criteria

- [ ] Requirement tests SR-S122-01 through SR-S122-08 written first and failing
- [ ] Tasks T243 and T244 complete and wired through the API router and the web route table
- [ ] API, React, E2E, accessibility, and permission-negative tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/update-requests/handlers_public.rs` mounted in `services/api/src/router.rs` (`/public/update-requests`); `apps/web/src/features/update-requests/PublicRequestPage.tsx` registered in `apps/web/src/app/routes.tsx`
- [ ] Handoff evidence recorded in the F061 ticket
