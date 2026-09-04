---
id: T055
type: task
status: planned
parent_epic: E003
parent_feature: F014
parent_story: S028
depends_on: [T054]
owned_paths: [crates/domain/src/forms/**, crates/persistence/src/forms/**, services/api/src/forms/**, apps/web/src/features/forms/**, testing/features/F014/api/**, testing/features/F014/frontend/**]
feature_flag: F014_FEATURE
branch: t055-submission-endpoint
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 6
- Capability contract: `docs/capability-contracts.md` row F014

# T055 — Submission endpoint

## Identity

- Parent story: `S028` Public submission
- Owner: platform
- Branch: `t055-submission-endpoint`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 6; `docs/capability-contracts.md` row F014

## Objective

Implement the two public routes and the submissions list: token resolution, public schema, intake event before row creation, idempotent retries, identity capture, drafts, confirmation rendering, and the public form page.

## Specification

- Owned paths: `crates/domain/src/forms/{submission.rs, intake.rs, drafts.rs, confirmation.rs, public_schema.rs}` (repository traits only, no SQL), `crates/persistence/src/forms/{form_submission_repository.rs, form_version_repository.rs}`, `services/api/src/forms/{handlers_public.rs, handlers_submissions.rs, headers.rs}`, `apps/web/src/features/forms/{PublicFormPage.tsx, PublicField.tsx, ClosedNotice.tsx, ConfirmationPage.tsx, SubmissionsList.tsx, draft.ts, publicApi.ts}`
- Contract/input: `GET /public/forms/{token}` (no session); `POST /public/forms/{token}/submissions` with header `Idempotency-Key` and body `SubmitRequest { values: Map<key, Value>, files?, draft?, draft_token?, captcha_token?, honeypot?, email? }` capped at 1 MB; `GET /api/v1/forms/{id}/submissions` query `{ cursor?, limit? ≤ 200, status?, received_from?, received_to? }`.
- Data access: `FormVersionRepository::find_by_submission_token_hash(hash)` and `load_published_schema(version_id)` resolve the token and compose the public schema from the version columns and its `form_fields`, `form_field_options`, and `form_version_upload_mime_types` rows; `FormSubmissionRepository::find_by_idempotency_key(form_id, key)`, `find_by_draft_token(token)`, and `page_submissions(form_id, filter, cursor)` serve replay, drafts, and the admin list. Accept-submission runs in one `UnitOfWork`; the row and its cells are written through F006/F007's repositories, never by this feature's SQL, and no `sqlx::query*` call or connection appears in the handlers or the domain module.
- Output/behavior: `PublicFormSchema` keeps its nested JSON shape, omits `sheet_id`, `column_id`, `tenant_id`, and user IDs, and is cached per token for 60 seconds; submission order is rate limit (T056), CAPTCHA and honeypot (T056) read from `captcha_enabled`/`honeypot_enabled`, open window from `opens_at`/`closes_at`, identity mode (`anonymous|email|authenticated`), server-side `show_if`, validation; accepted path inserts `form_submissions` with `status: received` and the typed `submitter_kind`, `submitter_email`, `submitter_user_id` columns, creates the row through the F006/F007 repositories in the same transaction, updates to `accepted` with `row_id`, emits `form.submitted.v1`; failures write `rejected` with reason and emit `form.submission-rejected.v1`; replay by key returns the original `SubmitResponse { submission_id, row_id, status, confirmation_html }`; `{ draft: true }` stores by `draft_token` with `expires_at = now + 7 days`; responses under `/public/forms` send a `Content-Security-Policy: frame-ancestors` header assembled from the version's `form_version_frame_ancestors` origin rows and no `X-Frame-Options`; `PublicFormPage` keeps a local draft, announces conditional fields, shows field errors, closed, offline, and confirmation states; `SubmissionsList` pages events with row links; telemetry `form_opened_public`, `form_submitted`.
- Dependencies: T054 evaluator and validation; F006 row create; F007 typed cells; F038 session lookup for `authenticated` mode.
- Feature flag: `F014_FEATURE`; public routes return 404 when off.

## TDD

- Failing test first: `testing/features/F014/api/public_tests.rs::public_schema_omits_internal_ids`, `::revoked_token_not_found`, `::submission_intake_event_precedes_row`, `::submission_replay_returns_original_ids`, `::submission_validation_error_records_rejection`, `::submission_closed_window_rejected`, `::authenticated_mode_without_session_denied`, `::submitter_mode_check_rejects_email_without_address`, `::frame_ancestors_header_lists_every_origin_row`, `::draft_saved_without_row`; `testing/features/F014/frontend/PublicFormPage.test.tsx::renders_conditional_field_after_value`, `::shows_field_errors_from_response`, `::restores_local_draft`
- Targeted command: `cargo xtask test-feature F014`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: published 8-field form fixture; in-memory outbox recorder; MSW handlers for the public routes

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Public router mounted at `/public/forms` in `services/api/src/router.rs`; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S028
- [ ] `finished_at` recorded
