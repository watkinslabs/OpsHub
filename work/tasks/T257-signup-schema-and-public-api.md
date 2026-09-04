---
id: T257
type: task
status: planned
parent_epic: E006
parent_feature: F065
parent_story: S129
depends_on: [S129]
owned_paths: [services/api/migrations/*_signup_*.sql, crates/domain/src/signup/**, crates/persistence/src/signup/**, services/api/src/signup/**, testing/features/F065/api/**, testing/features/F065/database/**]
feature_flag: F065_FEATURE
branch: t257-signup-schema-and-public-api
started_at: null
finished_at: null
---

# T257 — Signup schema and public API

## Identity

- Parent story: `S129` public signup and verification
- Owner: platform
- Branch: `t257-signup-schema-and-public-api`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 9; `docs/capability-contracts.md` row F065

## Objective

Create the `signup` schema and the anonymous route surface: `signup_requests`, `signup_tokens`, and `reserved_slugs` with their indexes, checks and seeded reservations, plus `POST /public/signup`, `GET /public/signup/availability`, `GET /public/signup/{token}`, and the `POST /api/v1/signup/invitations` operator route, with the non-enumerating response contract wired end to end.

## Specification

- Owned paths: `services/api/migrations/<ts>_signup_create_tables.sql` and `.down.sql`, `crates/domain/src/signup/{mod.rs, request.rs, token.rs, slug.rs, errors.rs, service.rs}`, `crates/persistence/src/signup/{mod.rs, request_repository.rs, token_repository.rs, reserved_slug_repository.rs}`, `services/api/src/signup/{mod.rs, routes.rs, handlers_public.rs, handlers_token.rs, handlers_invitation.rs, dto.rs}`
- Data access: this task creates the module's only SQL. `SignupRequestRepository` owns `signup_requests`, `signup_request_risk_flags`, and `signup_request_utm` and exposes `insert_pending`, `find_by_id`, `find_by_tenant_id`, `find_soft_reservation_for_slug`, `clear_requested_slug`, `mark_verified`, `mark_provisioned`, `count_recent_by_email_hash`, `increment_resend_count`, `add_risk_flags`, `list_risk_flags`, `save_utm`, `list_pending_past_expiry`, `mark_abandoned_batch`, `scrub_personal_data_batch`, and `delete_requests_created_before`; `SignupTokenRepository` owns `signup_tokens` with `insert_for_request`, `find_live_by_token_hash`, `record_attempt`, and `consume`; `ReservedSlugRepository` owns `reserved_slugs` with `is_reserved`, `pin_for_request`, and `release_expired_pins`. No generic query method is exposed. `service.rs` and the four handlers depend on these traits and contain no `sqlx::query*` call, connection, or SQL string; availability checks tenant slugs through F002's `TenantRepository::slug_exists`; and a signup insert writes the request, its flag rows, and its utm row in one `UnitOfWork` (decision section 2.1).
- Contract/input: `StartSignupRequest { email, company_name, bot_token, company_website, elapsed_ms, utm?, requested_slug? }`; availability query `{ slug }`; token path parameter; `CreateInvitationRequest { email, company_name, slug?, trial_days, note? }`; secrets `signup/email_pepper` and `signup/turnstile_secret` through the F004 `SecretSource`.
- Output/behavior: `POST /public/signup` returns `202 { status: "pending_verification", expires_in_seconds: 86400 }` for every accepted shape and pads to a 250 ms floor; it inserts a `signup_requests` row with the peppered `email_hash` plus one `signup_request_risk_flags` row per raised flag and a `signup_request_utm` row when the DTO carries `utm`, publishes `signup.started.v1` on the platform tenant id, and mints one `signup_tokens` row holding only `SHA-256(token)` with a 24-hour expiry. `GET /public/signup/availability` returns `{ slug, available }` with one negative answer for taken, reserved, and soft-reserved names. `GET /public/signup/{token}` returns `{ email_masked, company_name, requested_slug, slug_available, expires_at, terms_version }` or `410 gone` with `expired`, `consumed`, or `abandoned`, treating an unknown token as expired, incrementing `attempts`, and rejecting the sixth; the first successful read sets `verified_at` and publishes `signup.verified.v1` once. `POST /api/v1/signup/invitations` requires `platform-operator`, pins the slug into `reserved_slugs` with `reason: "pinned"`, and returns `201 { request_id, expires_at }`. The migration creates the five tables — `signup_requests`, its `signup_request_risk_flags` and `signup_request_utm` children, `signup_tokens`, and `reserved_slugs` — with the partial unique index on `lower(requested_slug)` for `status in ('pending','verified')`, the unique `token_hash` index, the `attempts <= 5` and `resend_count <= 3` checks, the status and `tenant_id` agreement check, the `source`, `status`, `reason`, `trial_days`, and `flag` enum checks, the `on delete cascade` keys from both children to `signup_requests` and the `on delete restrict` key from `signup_requests.tenant_id` to `tenants`, the `signup_request_risk_flags(flag, request_id)` and `signup_request_utm(source, created_at desc)` indexes, and 240 seeded routing, brand, and profanity reservations.
- Dependencies: F038 `check_rate_limit` buckets for the four public buckets; F003 `record_audit` for `signup.invitation-created`; F004 outbox `enqueue` and secret source; the `/public` router mounted outside the tenant gate and session extractor.
- Feature flag: `F065_FEATURE` gates the router mount so the routes return `404` when off; the migration runs regardless.

## TDD

- Failing test first: `testing/features/F065/api/public_routes_tests.rs::signup_returns_generic_accepted_body`, `::existing_email_response_is_indistinguishable`, `::availability_hides_reason_for_unavailable_slug`, `::token_read_returns_masked_email_and_slug_state`, `::first_token_read_verifies_and_publishes_once`, `::token_read_after_expiry_returns_gone`, `::unknown_token_matches_expired_response`, `::sixth_token_attempt_is_rejected`, `::invitation_requires_platform_operator`, `::invitation_pins_reserved_slug`; `testing/features/F065/database/migration_tests.rs::signup_tables_exist_with_constraints`, `::soft_reservation_index_blocks_second_pending_slug`, `::token_hash_is_unique`, `::risk_flag_row_rejects_duplicate_and_unknown_flag`, `::utm_row_is_one_per_request`, `::request_delete_cascades_to_children`, `::seeded_reserved_slugs_present`, `::rollback_drops_signup_tables_children_first`
- Targeted command: `cargo xtask test-feature F065`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/signup.rs` seeded tenant `acme` with an active user, a platform operator, fixed clock `2026-09-03T00:00:00Z`, fixed token bytes and pepper, per-test rate-limit key prefix

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; routes registered behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes and no file in this task writes `tenants`, `users`, or `role_bindings`; `cargo xtask check-persistence` passes, proving the handlers and domain files hold no SQL
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S129
- [ ] `finished_at` recorded
