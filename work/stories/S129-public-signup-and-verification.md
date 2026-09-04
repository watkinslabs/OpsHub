---
id: S129
type: story
status: planned
parent_epic: E006
parent_feature: F065
depends_on: [F002, F038, F064]
owned_paths: [crates/domain/src/signup/**, crates/persistence/src/signup/**, services/api/src/signup/**, services/worker/src/signup/**, apps/web/src/features/signup/**, services/api/migrations/*_signup_*.sql, testing/features/F065/**]
feature_flag: F065_FEATURE
branch: s129-public-signup-and-verification
started_at: null
finished_at: null
---

# S129 — Public signup and verification

## Identity

- Parent feature: `F065` Self-serve signup and trials
- Owner: platform
- Branch: `s129-public-signup-and-verification`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 9; `docs/capability-contracts.md` row F065

## Vertical slice

As a prospective customer, I want to submit my work email and company name on a public page, receive one verification link that works once and expires, and see whether the workspace address I want is free, so that I can reach the completion step without an account, a sales call, or any way for me — or an attacker using the same form — to learn who else already uses OpsHub.

## Requirements

- **SR-S129-01:** `POST /public/signup` validates the request shape, evaluates rate limits, bot check, and email domain, then calls `SignupRequestRepository::insert_pending` to write the `signup_requests` row with `email_hash`, one `signup_request_risk_flags` row per raised flag, and the `signup_request_utm` row when the DTO carries a `utm` object, publishes `signup.started.v1`, and returns `202 { status: "pending_verification", expires_in_seconds: 86400 }` (covers FR-F065-01, FR-F065-03, FR-F065-04, FR-F065-05).
- **SR-S129-02:** That `202` is byte-identical and latency-identical for a new address, an address that already belongs to an active user, a taken slug, and a silently suppressed request; only the F037 mail differs, and no route in the module confirms that an email or a tenant exists (FR-F065-02, NFR-F065-02).
- **SR-S129-03:** `GET /public/signup/availability` answers a single slug with `{ slug, available }`, returning `false` identically for taken, reserved, and soft-reserved names, rate limited to 60 per minute per IP (FR-F065-06, FR-F065-03).
- **SR-S129-04:** A signup soft-reserves `requested_slug` through the partial unique index on `signup_requests`, checked by `SignupRequestRepository::find_soft_reservation_for_slug`; a second claimant is stored with `requested_slug = null` and a `slug_taken` row in `signup_request_risk_flags` and still receives the standard `202` (FR-F065-07).
- **SR-S129-05:** `signup_tokens`, reached only through `SignupTokenRepository`, holds only `SHA-256(token)` for a 32-byte CSPRNG value valid 24 hours, compared in constant time, capped at 5 attempts, single-use; `GET /public/signup/{token}` returns the masked address and slug state for a live token and `410 gone` with `expired`, `consumed`, or `abandoned` otherwise, with an unknown token indistinguishable from an expired one; the first successful read marks the request `verified` and publishes `signup.verified.v1` once (FR-F065-08, NFR-F065-02).
- **SR-S129-06:** All signup mail is created through the F037 `NotificationService` with category `system` and `dedupe_key` `signup:{request_id}:{kind}`; resends are capped at 3 per request and 60 seconds apart and reuse the same token row; the module owns no SMTP client or template renderer (FR-F065-09).
- **SR-S129-07:** `POST /api/v1/signup/invitations` requires `platform-operator`, skips the bot and disposable-domain checks, pins the slug into `reserved_slugs` with `reason: "pinned"` for the token's life, sends the invitation mail, and returns `201 { request_id, expires_at }`; anonymous and `tenant-admin` callers are denied (FR-F065-15).
- **SR-S129-08:** The public pages `/signup`, `/signup/verify-sent`, `/signup/complete/:token`, and `/signup/expired` render outside the authenticated shell, debounce the availability check at 400 ms, keep the honeypot out of the tab order, and announce availability through a polite live region (FR-F065-16, NFR-F065-03).
- **SR-S129-09:** Anonymous rejections increment `signup_rejected_total{reason}` and insert `signup_request_risk_flags` rows but write no audit rows, and logs and spans carry `request_id` and `email_hash` only — never the address, the raw token, or `bot_token` (NFR-F065-02, NFR-F065-04, NFR-F065-05).

## Surfaces

- Infrastructure/container: deployment secrets `signup/turnstile_secret` and `signup/email_pepper` resolved through the F004 `SecretSource`; the `/public` router mounted outside the tenant gate and session extractor but inside the rate-limit and correlation layers
- Data access: `crates/persistence/src/signup/{mod.rs, request_repository.rs, token_repository.rs, reserved_slug_repository.rs}` hold every SQL statement in this slice — `SignupRequestRepository` owns `signup_requests`, `signup_request_risk_flags`, and `signup_request_utm`, `SignupTokenRepository` owns `signup_tokens`, `ReservedSlugRepository` owns `reserved_slugs`, and slug existence on `tenants` is read through F002's `TenantRepository::slug_exists`; the domain services, the `services/api/src/signup/` handlers, and `testing/fixtures/signup.rs` depend on the repository traits and contain no `sqlx::query*` call or connection, and the insert of a request with its flag and utm rows runs in one `UnitOfWork` (decision section 2.1)
- Rust service/API: `crates/domain/src/signup/{mod.rs, request.rs, token.rs, slug.rs, risk.rs, errors.rs, service.rs, bot_check.rs, mx.rs, disposable_domains.txt}`; `services/api/src/signup/{mod.rs, routes.rs, handlers_public.rs, handlers_token.rs, handlers_invitation.rs, dto.rs}`
- Data/migration: `services/api/migrations/<ts>_signup_create_tables.sql` creating `signup_requests`, `signup_request_risk_flags`, `signup_request_utm`, `signup_tokens`, and `reserved_slugs` with the indexes, enum checks, foreign keys, and 240 seeded reservations from ticket section 4
- React/UI: `apps/web/src/features/signup/{SignupPage.tsx, SignupForm.tsx, TurnstileField.tsx, HoneypotField.tsx, VerifySentPage.tsx, SlugField.tsx, ExpiredTokenPage.tsx, InvitationForm.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: `testing/fixtures/signup.rs` with `StaticBotCheck`, `StaticMxResolver`, an in-memory `NotificationSender` recording category and `dedupe_key`, a seeded existing tenant `acme`, and a fixed clock, token, and pepper

## TDD harness

- Test path: `testing/features/F065/{api,database,frontend,accessibility}/`
- Feature flag: `F065_FEATURE`
- Targeted command: `cargo xtask test-feature F065`
- Full command: `cargo xtask test-all`
- First failing tests: `signup_returns_generic_accepted_body`, `existing_email_response_is_indistinguishable`, `availability_hides_reason_for_unavailable_slug`, `second_claimant_stores_null_slug_with_flag_row`, `risk_flag_rows_are_idempotent_per_request`, `utm_object_round_trips_through_child_row`, `token_is_stored_only_as_hash`, `first_token_read_verifies_and_publishes_once`, `token_read_after_expiry_returns_gone`, `sixth_token_attempt_is_rejected`, `resend_reuses_token_and_respects_cooldown`, `invitation_requires_platform_operator`

## Exit criteria

- [ ] Requirement tests SR-S129-01 through SR-S129-09 written first and failing
- [ ] Tasks T257 and T258 complete and wired through the API router
- [ ] Unit, API, database, React, accessibility, and permission tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/signup/routes.rs` mounted in `services/api/src/router.rs` at `/public/signup` and `/api/v1/signup`; the anonymous router registered before the tenant gate
- [ ] Enumeration-negative suite green: identical status, body, and latency band across the four FR-F065-02 cases
- [ ] Handoff evidence recorded in the F065 ticket
