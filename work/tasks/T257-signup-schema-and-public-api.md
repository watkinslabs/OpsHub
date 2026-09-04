---
id: T257
type: task
status: planned
parent_epic: E006
parent_feature: F065
parent_story: S129
depends_on: [S129]
owned_paths: [services/api/migrations/*_signup_*.sql, crates/domain/src/signup/**, services/api/src/signup/**, testing/features/F065/api/**, testing/features/F065/database/**]
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
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 9; `docs/capability-contracts.md` row F065

## Objective

Create the `signup` schema and the anonymous route surface: `signup_requests`, `signup_tokens`, and `reserved_slugs` with their indexes, checks and seeded reservations, plus `POST /public/signup`, `GET /public/signup/availability`, `GET /public/signup/{token}`, and the `POST /api/v1/signup/invitations` operator route, with the non-enumerating response contract wired end to end.

## Specification

- Owned paths: `services/api/migrations/<ts>_signup_create_tables.sql` and `.down.sql`, `crates/domain/src/signup/{mod.rs, request.rs, token.rs, slug.rs, errors.rs, service.rs}`, `services/api/src/signup/{mod.rs, routes.rs, handlers_public.rs, handlers_token.rs, handlers_invitation.rs, dto.rs}`
- Contract/input: `StartSignupRequest { email, company_name, bot_token, company_website, elapsed_ms, utm?, requested_slug? }`; availability query `{ slug }`; token path parameter; `CreateInvitationRequest { email, company_name, slug?, trial_days, note? }`; secrets `signup/email_pepper` and `signup/turnstile_secret` through the F004 `SecretSource`.
- Output/behavior: `POST /public/signup` returns `202 { status: "pending_verification", expires_in_seconds: 86400 }` for every accepted shape and pads to a 250 ms floor; it inserts a `signup_requests` row with the peppered `email_hash`, publishes `signup.started.v1` on the platform tenant id, and mints one `signup_tokens` row holding only `SHA-256(token)` with a 24-hour expiry. `GET /public/signup/availability` returns `{ slug, available }` with one negative answer for taken, reserved, and soft-reserved names. `GET /public/signup/{token}` returns `{ email_masked, company_name, requested_slug, slug_available, expires_at, terms_version }` or `410 gone` with `expired`, `consumed`, or `abandoned`, treating an unknown token as expired, incrementing `attempts`, and rejecting the sixth; the first successful read sets `verified_at` and publishes `signup.verified.v1` once. `POST /api/v1/signup/invitations` requires `platform-operator`, pins the slug into `reserved_slugs` with `reason: "pinned"`, and returns `201 { request_id, expires_at }`. The migration creates the three tables with the partial unique index on `lower(requested_slug)` for `status in ('pending','verified')`, the unique `token_hash` index, the `attempts <= 5` and `resend_count <= 3` checks, the status and `tenant_id` agreement check, and 240 seeded routing, brand, and profanity reservations.
- Dependencies: F038 `check_rate_limit` buckets for the four public buckets; F003 `record_audit` for `signup.invitation-created`; F004 outbox `enqueue` and secret source; the `/public` router mounted outside the tenant gate and session extractor.
- Feature flag: `F065_FEATURE` gates the router mount so the routes return `404` when off; the migration runs regardless.

## TDD

- Failing test first: `testing/features/F065/api/public_routes_tests.rs::signup_returns_generic_accepted_body`, `::existing_email_response_is_indistinguishable`, `::availability_hides_reason_for_unavailable_slug`, `::token_read_returns_masked_email_and_slug_state`, `::first_token_read_verifies_and_publishes_once`, `::token_read_after_expiry_returns_gone`, `::unknown_token_matches_expired_response`, `::sixth_token_attempt_is_rejected`, `::invitation_requires_platform_operator`, `::invitation_pins_reserved_slug`; `testing/features/F065/database/migration_tests.rs::signup_tables_exist_with_constraints`, `::soft_reservation_index_blocks_second_pending_slug`, `::token_hash_is_unique`, `::seeded_reserved_slugs_present`, `::rollback_drops_signup_tables`
- Targeted command: `cargo xtask test-feature F065`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/signup.rs` seeded tenant `acme` with an active user, a platform operator, fixed clock `2026-09-03T00:00:00Z`, fixed token bytes and pepper, per-test rate-limit key prefix

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; routes registered behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes and no file in this task writes `tenants`, `users`, or `role_bindings`
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S129
- [ ] `finished_at` recorded
