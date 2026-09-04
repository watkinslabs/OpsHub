---
id: F014
type: feature
status: planned
priority: P1
owner: platform
estimate: 8
target_milestone: M2
parent_epic: E003
depends_on: [F007]
blocks: [F015, F051, F058]
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/forms/**, crates/persistence/src/forms/**, services/api/src/forms/**, apps/web/src/features/forms/**, services/api/migrations/*_forms_*.sql, testing/features/F014/**]
feature_flag: F014_FEATURE
flag_default: off
branch: f014-forms
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 5, 6
- Capability contract: `docs/capability-contracts.md` row F014

# F014 — Forms

## 1. Identity and dates

- Branch: `f014-forms`
- Capability area: forms and data collection (spec 5.3 FORM-01, FORM-02, FORM-03, FORM-04; section 10 external sharing decision)
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 5, 6; `docs/capability-contracts.md` row F014
- Aggregate: `form`
- Module slug: `forms`

## 2. Requirement specification

### Problem and user outcome

Requests reach teams by email and chat and are retyped into sheets by hand. A form admin needs to build a branded form over a sheet's typed columns, publish it to internal users, external requesters, or an embedded page, and have every submission land as a traceable row with an immutable intake record, so that later routing, approval, and notification features start from a trustworthy event.

As a form admin, I want to design, publish, and share a form whose submissions create rows safely, so that requests enter the sheet without manual copying and without exposing the sheet to spam or abuse.

### Functional requirements

- **FR-F014-01:** An actor with the `form-admin` role on the target sheet can create a form with `sheet_id`, `title` (1–200 chars), optional `description` (≤ 4,000 chars), and `branding { logo_file_id?, accent_color (hex), title, description }`; branding persists as the typed columns `branding_logo_file_id`, `branding_accent_color`, `branding_title`, `branding_description` on `form_versions`, the hex format is a `check` constraint rather than application-only validation, and the response returns a UUIDv7 `id`, `version` 1, `status: draft`, an empty field list, and the same nested `branding` object composed by the repository.
- **FR-F014-02:** Form fields reference a `column_id` of the target sheet and carry `key` (unique per version, `[a-z0-9_]{1,64}`), `label`, `help`, `required`, `default`, and `validation { regex?, min?, max?, options_subset? }`; `regex`, `min`, and `max` persist as the typed columns `validation_regex`, `validation_min`, `validation_max` on `form_fields` and `options_subset` is an enumerable set persisted as `form_field_options` rows ordered by `position` and unique per `(field_id, option_key)`; a field whose column does not belong to the sheet returns `invalid` with `field_errors.fields[n].column_id`, and request and response keep the nested `validation` object.
- **FR-F014-03:** Each field may carry a `show_if` expression AST of comparisons (`eq`, `ne`, `gt`, `lt`, `contains`, `is_empty`) over other field keys combined with `and`/`or` nodes up to depth 4; the same evaluator runs in the browser and on the server, and a field hidden by `show_if` is never treated as required and its value is discarded.
- **FR-F014-04:** Form versions are immutable after publish; `POST /api/v1/forms/{id}/publish` freezes the draft as `form_versions.version_number = n`, marks it current, issues a submission token, and emits `form.published.v1`; a `PATCH` on a form whose current version is published creates draft version `n+1` instead of mutating `n`.
- **FR-F014-05:** A public submission token is 32 random bytes encoded URL-safe base64, bound to one published version, never a session credential, and can be rotated or revoked through `PATCH /api/v1/forms/{id}` with `{ rotate_token: true }` or `{ revoke_token: true }`; a revoked or unknown token returns `not_found` on both public routes.
- **FR-F014-06:** `GET /public/forms/{token}` returns the published schema (fields by `key`, labels, validation with its option set, `show_if`, branding, identity mode, upload limits with the MIME allowlist, open/closed state) and never returns `sheet_id`, `column_id`, `tenant_id`, or user IDs; the response keeps its nested JSON shape and is composed by `FormVersionRepository::load_published_schema` from the version columns and the `form_fields`, `form_field_options`, and `form_version_upload_mime_types` rows, so no client contract changes.
- **FR-F014-07:** `POST /public/forms/{token}/submissions` is unauthenticated, requires `Idempotency-Key`, and is limited to 60 submissions per hour per token and client IP and 1,000 per day per token; excess returns `429 rate_limited` with a `Retry-After` header and emits `form.submission-rejected.v1` with reason `rate_limited`.
- **FR-F014-08:** A published version may enable a CAPTCHA (server-side check of the client token through the provider-neutral verification adapter) and a honeypot field, held as the boolean columns `form_versions.captcha_enabled` and `form_versions.honeypot_enabled`; a failed check rejects with reason `captcha_failed`, a filled honeypot rejects with reason `honeypot`, and both rejections return `400 invalid` without revealing which control fired.
- **FR-F014-09:** Identity capture is `anonymous`, `email` (required, RFC 5322 syntax, stored on the submission), or `authenticated` (requires a tenant session; unauthenticated callers receive `denied`); the captured identity is written to the typed columns `form_submissions.submitter_kind`, `submitter_email`, and `submitter_user_id`, where a `check` constraint requires a non-null email in `email` mode and a non-null user id in `authenticated` mode, so the three modes stay mutually exclusive and the submitter is joinable to `users`.
- **FR-F014-10:** Every accepted submission first writes an immutable `form_submissions` intake event (`payload`, `version_id`, `submitter`, `ip_hash`, `user_agent`, `received_at`, `status: received`) and then creates the row through the F006/F007 row create path in the same transaction; the intake status becomes `accepted` with `row_id`, and `form.submitted.v1` is emitted with `submission_id` and `row_id`.
- **FR-F014-11:** Replaying `POST /public/forms/{token}/submissions` with the same `Idempotency-Key` returns the original `submission_id` and `row_id` and creates no second intake event or row; the same key with a different body returns `conflict`.
- **FR-F014-12:** Validation failures return `400 invalid` with `field_errors.<key>` carrying the configured message per field, record a `rejected` intake event with reason `validation`, and emit `form.submission-rejected.v1`.
- **FR-F014-13:** File fields accept at most 10 files per submission, each ≤ 25 MB and within the version's MIME allowlist; the two limits are declarative — `form_versions.upload_max_files smallint check (between 0 and 10)` and `upload_max_bytes bigint check (<= 26214400)` — and the allowlist is a joined, constrained set of `form_version_upload_mime_types` rows unique per `(version_id, mime_type)`, so a submitted MIME type is checked by join rather than by scanning a JSON array; violations reject with reason `upload_rejected`; accepted uploads use the F017 upload flow when `F017_FEATURE` is on and otherwise are stored as `pending_attachments` on the submission.
- **FR-F014-14:** A submitter may save a draft locally (browser storage) or server-side by `draft_token` for 7 days through `POST /public/forms/{token}/submissions` with `{ draft: true }`; drafts create no row and are purged after expiry.
- **FR-F014-15:** A version has an `opens_at`/`closes_at` schedule held as two `timestamptz` columns on `form_versions` with `check (closes_at is null or opens_at is null or closes_at > opens_at)`; the open/closed state is evaluated on every public request, so it is filtered data served by the index `form_versions(opens_at, closes_at)`; submissions outside the window reject with reason `form_closed` and the public page shows the closed message; the confirmation page and optional confirmation email are stored as `confirmation_message`, `confirmation_send_email`, `confirmation_email_subject`, and `confirmation_email_body`, and support `{{field.<key>}}` and `{{submission.id}}` placeholders unchanged.
- **FR-F014-16:** Sharing modes are `internal` (workspace members with `form-submitter`), `link` (public token), and `embed` (an `<iframe>` snippet); only `/public/forms/*` responses omit `X-Frame-Options` and instead send a `Content-Security-Policy: frame-ancestors` header assembled from the version's `form_version_frame_ancestors` rows, one `origin` per row, unique per `(version_id, origin)`, so each allowed origin is joinable, constrained, and audited.
- **FR-F014-17:** `GET /api/v1/forms/{id}/submissions` lists intake events for `form-admin` with cursor paging, filters by `status` and `received_at` range, and links each to its row; `GET /api/v1/sheets/{sheet_id}/forms` lists forms with status and current version.
- **FR-F014-18:** Cross-tenant access to any form, version, or submission by ID returns `not_found`; a `form-submitter` calling admin routes receives `denied`.

### Non-functional requirements

- **NFR-F014-01 Performance:** `GET /public/forms/{token}` p95 under 300 ms and submission accept p95 under 800 ms with 40 fields; the version schema is cached per token for 60 seconds and invalidated on publish and revoke (spec section 6).
- **NFR-F014-02 Security/privacy:** public routes run without tenant session, store only a salted SHA-256 `ip_hash`, redact payloads from logs, enforce the rate limit and CAPTCHA before any database write, and never expose internal IDs; cross-tenant and role-negative tests are in the harness.
- **NFR-F014-03 Accessibility:** builder and public form pass axe with no serious violations; every field has a visible label and error announced by `aria-describedby`; conditional show/hide is announced by a live region; layout works at 320 px width.
- **NFR-F014-04 Reliability/observability:** submission spans carry `form_id`, `version_id`, `submission_id`, `correlation_id`; a row-create failure leaves the intake event in `received` with `error_code` and is retried by the same idempotency key; rejection counts by reason are exported as a metric.

### Scope

Included: form CRUD, fields over typed columns, validation rules, conditional display AST, branding, immutable versions and publish, submission tokens with rotate/revoke, public schema route, unauthenticated submission with rate limit, CAPTCHA adapter and honeypot, identity capture, immutable intake event then row creation, idempotent retries, drafts, confirmation page/email templates, upload limits, open/closed schedule, internal/link/embed sharing, submissions list, builder and public UI.

Excluded: routing and approval after submission (F018, F019, F020), update requests (F061), virus scanning and previews (F017), mobile PWA offline queue (F058), notifications delivery (F037), template packaging of forms (F015), WorkApps embedding (F051).

## 3. UX specification

- Entry points: sheet header `Forms` tab at `/w/{workspace_id}/sheets/{sheet_id}/forms`; builder at `/w/{workspace_id}/forms/{form_id}`; public page at `/public/forms/{token}`; `Share` dialog with internal, link, and embed tabs, the embed tab editing the allowed frame-ancestor origins one row at a time and rejecting a duplicate origin inline.
- Primary flow: open a sheet, click `New form`, drag columns from the field palette into the canvas, set label, help, required, validation, and `show_if`, watch the live preview, click `Publish`, copy the link or embed snippet; a requester opens the link on a phone, fills fields, sees dependent fields appear, submits, and reads the confirmation page.
- Loading: skeleton fields; Empty: palette hint `Drag a column here`; Error: banner with `correlation_id` and retry; Success: toast on save and publish, confirmation page on submit; Stale/conflict: banner `This form changed` with reload; Offline: public page keeps the local draft and shows an offline badge; Closed: closed message with `opens_at` when in the future.
- Permission-denied: `form-submitter` never sees builder routes; admin routes return `denied` inline; an unknown or revoked token renders the public not-found page without tenant details.
- Responsive: single-column public form under 640 px with sticky submit; builder collapses the palette into a drawer under 1,024 px.
- Keyboard: palette items insert with `Enter`, fields reorder with `Alt+Arrow`, condition editor is a form, not a canvas; public form uses native controls with visible focus rings; motion respects `prefers-reduced-motion`.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide icons `FormInput`, `Eye`, `Send`, `Link`, `Code2`, `ShieldCheck`; spacing and colour from `apps/web/src/design/tokens.css`; accent colour is validated for 4.5:1 contrast on the button label.

- Design: `design/artboards/Forms.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

### Rust backend

- Domain entities: `Form { id, tenant_id, sheet_id, workspace_id, title, description, status: FormStatus(Draft|Published|Closed), current_version_id, version, audit fields, deleted_at }`, `FormVersion { id, form_id, version_number, fields: Vec<FormField>, branding: Branding, identity_mode: IdentityMode, spam: SpamPolicy { captcha: bool, honeypot: bool }, uploads: UploadPolicy { max_files: 10, max_bytes: 26_214_400, mime_allowlist }, schedule: OpenWindow, confirmation: ConfirmationTemplate, frame_ancestors: Vec<String>, published_at, submission_token_hash }`, `FormField { key, column_id, label, help, required, default, validation: FieldValidation, show_if: Option<ConditionAst> }`, `FormSubmission { id, tenant_id, form_id, version_id, status: IntakeStatus(Received|Accepted|Rejected|Draft), reason: Option<RejectReason>, payload: Json, submitter: Submitter, ip_hash, user_agent, received_at, row_id, error_code, draft_token, expires_at }`. These aggregates are composed by the repositories from the parent row plus its child rows; they are not a one-to-one map of a single table.
- Use cases in `crates/domain/src/forms/`: `create_form`, `update_form_draft`, `publish_form`, `delete_form`, `list_forms`, `rotate_token`, `revoke_token`, `load_public_schema`, `evaluate_conditions`, `validate_submission`, `record_intake`, `accept_submission`, `reject_submission`, `save_draft`, `list_submissions`.
- Persistence (`crates/persistence/src/forms/`): `FormRepository` owns `forms`; `FormVersionRepository` owns `form_versions`, `form_version_frame_ancestors`, `form_version_upload_mime_types`, `form_fields`, `form_field_options`; `FormSubmissionRepository` owns `form_submissions`. Each implements the shared `Repository` contract (`get`, `list` with cursor pagination, `insert`, `update` under an expected version, `soft_delete`, `restore`, `purge`) and adds the named queries `list_for_sheet`, `find_by_submission_token_hash(hash)`, `next_version_number(form_id)`, `publish_version(version_id)`, `load_published_schema(version_id)`, `find_by_draft_token(token)`, `find_by_idempotency_key(form_id, key)`, `page_submissions(form_id, filter, cursor)`; the tenant predicate, soft-delete filter, version check, audit row, and outbox enqueue come from the base contract. Publish (freeze the draft, set `forms.current_version_id`, mint the token) and accept-submission (intake row, then the F006/F007 row create, then the status and `row_id` update) each run in one `UnitOfWork` that owns the transaction; the row and its cells are written through F006/F007's repositories, never by this feature's SQL, and the immutability triggers stay in the database. Per decision 2.1 the use cases above depend on these repository traits and contain no SQL: no SQL string, `sqlx::query*` call, or connection exists in `crates/domain/src/forms` or `services/api/src/forms`.
- API endpoints (`services/api/src/forms/`): `GET /api/v1/sheets/{sheet_id}/forms`, `POST /api/v1/forms`, `GET /api/v1/forms/{id}`, `PATCH /api/v1/forms/{id}`, `POST /api/v1/forms/{id}/publish`, `DELETE /api/v1/forms/{id}`, `GET /public/forms/{token}`, `POST /public/forms/{token}/submissions`, `GET /api/v1/forms/{id}/submissions`. DTOs: `CreateFormRequest`, `UpdateFormRequest { title?, description?, fields?, branding?, identity_mode?, spam?, uploads?, schedule?, confirmation?, frame_ancestors?, rotate_token?, revoke_token? }`, `PublishFormRequest {}`, `FormResponse`, `FormVersionResponse`, `PublicFormSchema`, `SubmitRequest { values: Map<key, Value>, files?, draft?, draft_token?, captcha_token?, honeypot?, email? }`, `SubmitResponse { submission_id, row_id?, status, confirmation_html }`, `Page<SubmissionResponse>`. The admin request bodies and every response keep their nested JSON shape on the wire; `FormVersionRepository` decomposes `branding`, `spam`, `uploads`, `schedule`, `confirmation`, `frame_ancestors`, and each field's `validation` into the typed columns and child rows on write and composes them back on read, so no client contract changes.
- Events: `form.published.v1`, `form.updated.v1`, `form.submitted.v1`, `form.submission-rejected.v1`; payload per contract conventions with `changed_fields`; rejection payload adds `reason`.
- Authorization: `form-admin` on the sheet for create, update, publish, delete, and submissions list; `form-submitter` on the workspace for `internal` sharing; public routes bypass session auth and resolve the tenant from the token; `authenticated` identity mode requires a session in the same tenant.
- Rate limiting: `rate_limit_buckets` from F038 keyed `form:{token}:{ip_hash}` (60/hour) and `form:{token}` (1,000/day); checked before CAPTCHA, CAPTCHA before validation, validation before any write.
- Error mapping: `FormError::UnknownColumn → 400 invalid`, `FormError::VersionFrozen → 409 conflict`, `FormError::StaleVersion → 409 conflict`, `FormError::TokenRevoked → 404 not_found`, `FormError::Closed → 400 invalid (reason form_closed)`, `FormError::RateLimited → 429 rate_limited`, `FormError::CaptchaFailed | Honeypot → 400 invalid`, `AuthzError::Denied → 403 denied`, cross-tenant → `404 not_found`.

### PostgreSQL/SQLx

- Migration `*_forms_*.sql` creates `forms(id uuid pk, tenant_id, sheet_id, workspace_id, title text, description text, status text, current_version_id uuid null, version bigint, audit fields, deleted_at)` and `form_versions(id uuid pk, tenant_id, form_id, version_number int, identity_mode text, branding_logo_file_id uuid null references files(id) on delete restrict, branding_accent_color text null check (branding_accent_color ~ '^#[0-9a-fA-F]{6}$'), branding_title text, branding_description text, captcha_enabled bool not null default false, honeypot_enabled bool not null default false, upload_max_files smallint not null default 10 check (upload_max_files between 0 and 10), upload_max_bytes bigint not null check (upload_max_bytes <= 26214400), opens_at timestamptz null, closes_at timestamptz null check (closes_at is null or opens_at is null or closes_at > opens_at), confirmation_message text, confirmation_send_email bool not null default false, confirmation_email_subject text, confirmation_email_body text, submission_token_hash bytea null, published_at timestamptz null, created_by, created_at)`.
- Migration also creates the version child tables `form_version_frame_ancestors(id uuid pk, tenant_id uuid not null, version_id uuid not null references form_versions(id) on delete cascade, origin text not null, created_by, created_at)` and `form_version_upload_mime_types(id uuid pk, tenant_id uuid not null, version_id uuid not null references form_versions(id) on delete cascade, mime_type text not null, created_by, created_at)`; the FR-F014-16 `Content-Security-Policy: frame-ancestors` header is assembled from the `origin` rows of the first, and the FR-F014-13 MIME allowlist is the joined, constrained set held by the second.
- Migration creates `form_fields(id uuid pk, tenant_id, version_id, key text, column_id uuid, position int, label text, help text, required bool, default_value jsonb, validation_regex text null, validation_min numeric null, validation_max numeric null, show_if jsonb null)` and its child `form_field_options(id uuid pk, tenant_id uuid not null, field_id uuid not null references form_fields(id) on delete cascade, option_key text not null, position smallint not null, created_by, created_at)`, which holds FR-F014-02's `options_subset` as an enumerable, ordered set. `default_value` stays `jsonb` because it is a typed cell value for the referenced column whose shape F007's column type defines, and it is never queried by key; `show_if` stays `jsonb` because it is the FR-F014-03 expression AST, user-authored, of arbitrary shape to depth 4, evaluated in memory by the shared evaluator and never read by key in SQL.
- Migration creates `form_submissions(id uuid pk, tenant_id, form_id, version_id, status text, reason text null, payload jsonb, submitter_kind text not null check (submitter_kind in ('anonymous','email','authenticated')), submitter_email citext null, submitter_user_id uuid null references users(id) on delete restrict, ip_hash bytea, user_agent text, received_at timestamptz, row_id uuid null, error_code text null, idempotency_key text, draft_token bytea null, expires_at timestamptz null)`. `payload` stays `jsonb` because it is the immutable submitted values keyed by field `key`, a typed cell-value payload of the intake event; the queried facts (`status`, `row_id`, `received_at`, submitter identity) are their own columns.
- Invariants: unique `(form_id, version_number)`; unique `(version_id, key)`; unique `submission_token_hash` where not null; unique `(tenant_id, form_id, idempotency_key)`; unique `(version_id, origin)` on `form_version_frame_ancestors`; unique `(version_id, mime_type)` on `form_version_upload_mime_types`; unique `(field_id, option_key)` and unique `(field_id, position)` on `form_field_options`; `check (submitter_kind <> 'email' or submitter_email is not null)` and `check (submitter_kind <> 'authenticated' or submitter_user_id is not null)` on `form_submissions`; trigger `form_versions_immutable` rejects `UPDATE` of policy columns and of the child rows of a version when `published_at is not null`; trigger `form_submissions_append_only` allows only `status`, `row_id`, `error_code` transitions `received → accepted|rejected`; `form_fields.column_id` foreign key to `columns` with `on delete restrict`.
- Indexes: `form_versions(submission_token_hash)`, `form_versions(opens_at, closes_at)`, `form_version_frame_ancestors(version_id)`, `form_version_upload_mime_types(version_id)`, `form_field_options(field_id)`, `form_submissions(form_id, received_at desc)`, `form_submissions(tenant_id, status)`, `form_submissions(tenant_id, submitter_user_id)`, `form_submissions(draft_token) where draft_token is not null`, `forms(tenant_id, sheet_id) where deleted_at is null`.
- Audit events: `form.create`, `form.update`, `form.publish`, `form.delete`, `form.token-rotate`, `form.token-revoke`, `form.submission-accept`, `form.submission-reject` with field-level diffs; submission payloads are referenced by `submission_id`, not copied into audit.
- Retention/deletion: forms soft delete; submissions and drafts follow the tenant retention policy from F027; expired drafts are purged nightly; migration rollback drops the seven tables — `forms`, `form_versions`, `form_version_frame_ancestors`, `form_version_upload_mime_types`, `form_fields`, `form_field_options`, `form_submissions` — and both triggers.

### React/TypeScript

- Routes: `/w/:workspaceId/sheets/:sheetId/forms`, `/w/:workspaceId/forms/:formId`, `/w/:workspaceId/forms/:formId/submissions`, `/public/forms/:token` in `apps/web/src/features/forms/`; components `FormBuilderPage`, `FieldPalette`, `FieldEditor`, `ConditionEditor`, `FormPreview`, `PublishDialog`, `ShareDialog`, `PublicFormPage`, `SubmissionsList`, `ClosedNotice`, `ConfirmationPage`.
- State: TanStack Query keys `['forms', sheetId]`, `['form', formId]`, `['form-submissions', formId, cursor]`, `['public-form', token]`; mutations invalidate by key and update cached `version`; the public page keeps a draft in `localStorage` under `form-draft:{token}` and optionally posts it with `draft: true`.
- API client: generated `FormsApi` with `listForms`, `createForm`, `updateForm`, `publishForm`, `deleteForm`, `listSubmissions`, and `PublicFormsApi` with `getSchema`, `submit`.
- Shared evaluator: `apps/web/src/features/forms/conditions.ts` mirrors `crates/domain/src/forms/conditions.rs` and is tested against the same JSON fixture set.
- Telemetry: `form_created`, `form_published`, `form_shared`, `form_opened_public`, `form_submitted`, `form_submission_rejected` with `form_id`, `version_number`, `reason`, and `share_mode`; no field values are sent.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F014-01 through FR-F014-18 in `testing/features/F014/requirements/cases.md`
- [ ] Failure/edge-case tests: unknown column, frozen version edit, revoked token, closed window, over-limit upload, honeypot, CAPTCHA failure, idempotent replay with mismatched body, draft expiry
- [ ] Permission-negative and tenant-isolation tests: cross-tenant form and submission read returns `not_found`, submitter on admin routes returns `denied`, `authenticated` mode without session returns `denied`
- [ ] Rust unit tests: `crates/domain/src/forms/` condition evaluator, validation rules, token generation, placeholder rendering; `crates/persistence/src/forms/` schema composition and decomposition round-trip and the publish and accept-submission `UnitOfWork` paths
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: immutability trigger, append-only trigger, unique keys on `form_version_frame_ancestors`, `form_version_upload_mime_types`, and `form_field_options`, the accent-colour, upload-limit, schedule-window, and submitter-mode `check` constraints, cascade delete of version and field children, rollback of all seven tables
- [ ] React component tests: `FormBuilderPage`, `ConditionEditor`, `PublicFormPage`, `SubmissionsList` states
- [ ] Browser E2E tests: build, publish, submit from a mobile viewport, view the row, embed page submission
- [ ] Accessibility tests: axe on builder and public form, live-region announcements, 320 px layout
- [ ] Performance/load tests: public schema p95 under 300 ms, submission p95 under 800 ms, rate limiter under burst

### Fast fanout configuration

- Test harness path: `testing/features/F014/`
- Feature flag: `F014_FEATURE`
- Fixture/seed factory: `testing/fixtures/forms.rs` builds tenant, sheet with 12 typed columns, form admin, submitter, foreign tenant, a published form with 8 fields and two conditional rules, and a fake verification adapter
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC, fixed token seed
- Mock/stub contracts: outbox recorded in memory; verification adapter stub returns pass or fail by token prefix; F017 upload stubbed as pending attachments
- Parallel isolation: one schema per test worker, tenant ID per test, rate-limit buckets namespaced by test
- Targeted command: `cargo xtask test-feature F014`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F014/`

## 6. Acceptance criteria

```gherkin
Feature: Forms and public submission

Scenario: Publish a form and submit through the public link
  Given a form admin has built form "Request" with a conditional "Budget" field on sheet "Intake"
  When they publish it and a requester submits from the public link with "Type" = "Purchase" and "Budget" = 500
  Then an intake event with status accepted exists before the row, the row exists in "Intake"
  And form.published.v1 and form.submitted.v1 are in the outbox

Scenario: Rate limit rejects a burst
  Given a published form token and one client IP
  When the client sends 61 submissions within an hour
  Then the 61st returns 429 rate_limited with Retry-After
  And form.submission-rejected.v1 with reason rate_limited is published

Scenario: Published version is immutable
  Given form "Request" version 1 is published
  When the admin edits a field label
  Then draft version 2 is created and version 1 fields are unchanged

Scenario: Submitter cannot administer
  Given a user with only form-submitter on the workspace
  When they call POST /api/v1/forms/{id}/publish
  Then the response is 403 denied and no version is published

Scenario: Revoked token does not leak
  Given a form whose token was revoked
  When anyone requests GET /public/forms/{token}
  Then the response is 404 not_found with no tenant details
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F007 (typed columns, validation engine, column options); F006 row create path; F038 `rate_limit_buckets`; decisions sections 2–6; contracts row F014
- Blocks: F015, F051, F058
- Conflicts with: none (disjoint owned paths)
- External dependencies: CAPTCHA verification provider reached through the provider-neutral adapter; unavailable provider fails closed with `unavailable` and a metric
- Risks and mitigations: the browser and server condition evaluators can drift, so both run the same JSON fixture suite in CI; public routes are unauthenticated, so rate limit and CAPTCHA run before any write and payload size is capped at 1 MB; F017 may land later, so uploads degrade to pending attachments behind a runtime check of `F017_FEATURE` while `branding_logo_file_id` stays nullable and its `files` foreign key is added by the same migration only when the `files` table is present.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F007 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F014/`
- [ ] Migration file name and owned paths claimed
- [ ] Fixture factory, verification adapter stub, and schema-per-worker isolation available in `testing/harness/`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation and rejection
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets`, `check-contracts`, and `check-persistence` pass
- [ ] Rollback verified: disable `F014_FEATURE`, public routes return 404, run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Form admins can build branded forms over sheet columns with conditional fields, publish immutable versions, and share them internally, by link, or embedded.
- Public submissions are rate-limited, spam-checked, recorded as immutable intake events, and create rows idempotently.
- Migration adds `forms`, `form_versions`, `form_fields`, and `form_submissions` plus the child tables `form_version_frame_ancestors`, `form_version_upload_mime_types`, and `form_field_options`; rollback drops all seven. Feature is off by default behind `F014_FEATURE`.
