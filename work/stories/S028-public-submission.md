---
id: S028
type: story
status: planned
parent_epic: E003
parent_feature: F014
depends_on: [S027]
owned_paths: [crates/domain/src/forms/**, crates/persistence/src/forms/**, services/api/src/forms/**, apps/web/src/features/forms/**, testing/features/F014/**]
feature_flag: F014_FEATURE
branch: s028-public-submission
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 5, 6
- Capability contract: `docs/capability-contracts.md` row F014

# S028 — Public submission

## Identity

- Parent feature: `F014` Forms
- Owner: platform
- Branch: `s028-public-submission`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 5, 6; `docs/capability-contracts.md` row F014

## Vertical slice

As an external or internal requester, I want to open a published form by link or embed, fill it on my phone, save a draft, and submit, so that my request becomes a traceable row while the sheet stays protected from spam, abuse, and oversized uploads.

## Requirements

- **SR-S028-01:** `GET /public/forms/{token}` resolves the token hash through `FormVersionRepository::find_by_submission_token_hash(hash)` and `load_published_schema(version_id)`, which composes `PublicFormSchema` from the version columns plus the `form_fields`, `form_field_options`, and `form_version_upload_mime_types` rows; the response keeps its nested JSON shape with fields by `key`, branding, identity mode, upload limits including the MIME allowlist, and open/closed state read from `opens_at`/`closes_at`, and never includes `sheet_id`, `column_id`, `tenant_id`, or user IDs; unknown or revoked tokens return `404 not_found` (FR-F014-05, FR-F014-06).
- **SR-S028-02:** `POST /public/forms/{token}/submissions` enforces the 60/hour per token+IP and 1,000/day per token limits from `rate_limit_buckets` before any write, returning `429 rate_limited` with `Retry-After` and emitting `form.submission-rejected.v1` reason `rate_limited` (FR-F014-07).
- **SR-S028-03:** CAPTCHA verification through the provider-neutral adapter, the honeypot check, the open window, identity mode, and field validation with `show_if` applied server-side run in that order; failures write a `rejected` intake event with reason `captcha_failed`, `honeypot`, `form_closed`, or `validation` and return `400 invalid` with `field_errors.<key>` where applicable (FR-F014-08, FR-F014-09, FR-F014-12, FR-F014-15).
- **SR-S028-04:** An accepted submission runs in one `UnitOfWork`: `FormSubmissionRepository` inserts the intake event with `status: received` and the typed `submitter_kind`, `submitter_email`, `submitter_user_id` columns first, then the row is created through F006/F007's own repositories in the same transaction, then the repository sets `status: accepted` and `row_id`, and `form.submitted.v1` is emitted; a row-create failure keeps `received` with `error_code` (FR-F014-10, FR-F014-09, NFR-F014-04).
- **SR-S028-05:** `FormSubmissionRepository::find_by_idempotency_key(form_id, key)` makes a replay of the same `Idempotency-Key` return the original `submission_id` and `row_id` with no second event or row; a different body with the same key returns `409 conflict` (FR-F014-11).
- **SR-S028-06:** File fields reject more than 10 files, any file over the version's `upload_max_bytes` (≤ 25 MB), or a MIME type with no matching `form_version_upload_mime_types` row, with reason `upload_rejected`; the count limit is the declarative `upload_max_files smallint check (between 0 and 10)`; accepted files use F017 when `F017_FEATURE` is on and otherwise become `pending_attachments` (FR-F014-13).
- **SR-S028-07:** `{ draft: true }` stores a server-side draft by `draft_token` for 7 days without creating a row and is read back by `FormSubmissionRepository::find_by_draft_token(token)`; the confirmation page renders `{{field.<key>}}` and `{{submission.id}}` placeholders from the `confirmation_message`, `confirmation_email_subject`, and `confirmation_email_body` columns; `/public/forms/*` responses send a `Content-Security-Policy: frame-ancestors` header assembled from the version's `form_version_frame_ancestors` origin rows instead of `X-Frame-Options` (FR-F014-14, FR-F014-15, FR-F014-16).
- **SR-S028-08:** `FormSubmissionRepository::page_submissions(form_id, filter, cursor)` backs the admin list; `PublicFormPage` renders on a 320 px viewport, keeps a local draft, shows and hides conditional fields with a live-region announcement, displays field-level errors, closed and offline states, and the confirmation page; `SubmissionsList` pages intake events for the form admin with status filters and row links (FR-F014-17, NFR-F014-03).

## Surfaces

- Infrastructure/container: none; rate-limit buckets from F038, verification adapter configured by deployment secret
- Rust service/API: `crates/domain/src/forms/{submission.rs, intake.rs, spam.rs, uploads.rs, drafts.rs, confirmation.rs}` (repository traits only, no SQL); `crates/persistence/src/forms/{mod.rs, form_submission_repository.rs, form_version_repository.rs}` holding the token, draft, idempotency, and submission-paging queries; `services/api/src/forms/{handlers_public.rs, handlers_submissions.rs, rate_limit.rs, headers.rs}`
- Data/migration: none new; uses `form_submissions`, `form_version_frame_ancestors`, `form_version_upload_mime_types`, and the triggers from S027
- React/UI: `apps/web/src/features/forms/{PublicFormPage.tsx, PublicField.tsx, ClosedNotice.tsx, ConfirmationPage.tsx, SubmissionsList.tsx, draft.ts, publicApi.ts}`
- Mocks/fixtures: published 8-field form with two conditions and a file field; verification adapter stub keyed by token prefix; F017 upload stub; 40-field form for performance lane; Playwright mobile viewport profile

## TDD harness

- Test path: `testing/features/F014/{api,database,frontend,e2e,accessibility,performance}/`
- Feature flag: `F014_FEATURE`
- Targeted command: `cargo xtask test-feature F014`
- Full command: `cargo xtask test-all`
- First failing tests: `public_schema_omits_internal_ids`, `submission_rate_limit_returns_429_with_retry_after`, `submission_intake_event_precedes_row`, `submission_replay_returns_original_ids`, `upload_mime_outside_allowlist_rejected`, `upload_over_limit_rejected`, `public_form_mobile_submit`

## Exit criteria

- [ ] Requirement tests SR-S028-01 through SR-S028-08 written first and failing
- [ ] Tasks T055 and T056 complete; public page wired to the real public routes through the generated client
- [ ] Unit, API, database, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `services/api/src/forms/handlers_public.rs` mounted at `/public/forms` in `services/api/src/router.rs`; `apps/web/src/features/forms/PublicFormPage.tsx` mounted at `/public/forms/:token`
- [ ] Handoff evidence recorded in the F014 ticket
