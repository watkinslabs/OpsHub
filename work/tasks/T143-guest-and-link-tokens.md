---
id: T143
type: task
status: planned
parent_epic: E004
parent_feature: F036
parent_story: S072
depends_on: [S072]
owned_paths: [crates/domain/src/sharing/**, crates/persistence/src/sharing/**, crates/auth/src/sharing/**, services/api/src/sharing/**, apps/web/src/features/sharing/**, testing/features/F036/api/**]
feature_flag: F036_FEATURE
branch: t143-guest-and-link-tokens
started_at: null
finished_at: null
---

# T143 — Guest and link tokens

## Identity

- Parent story: `S072` Guest identity and links
- Owner: platform
- Branch: `t143-guest-and-link-tokens`
- Decision references: `docs/architecture-decisions.md` sections 3, 4, 6; `docs/capability-contracts.md` row F036

## Objective

Implement guest invitations and acceptance, share-link creation, resolution, and revocation with hashed tokens, scoped bearer tokens, rate limits, and the guest, link, and public landing UI.

## Specification

- Owned paths: `crates/domain/src/sharing/{link.rs, invitation.rs, guest.rs, token.rs, service_links.rs, service_guests.rs}` (repository traits only, no SQL), `crates/persistence/src/sharing/{mod.rs, share_link_repository.rs, guest_invitation_repository.rs, guest_user_repository.rs}`, `crates/auth/src/sharing/{link_principal.rs, scoped_token.rs}`, `services/api/src/sharing/{handlers_link.rs, handlers_guest.rs, public_routes.rs}`, `apps/web/src/features/sharing/{GuestInviteForm.tsx, LinkSection.tsx, LinkRow.tsx, CreateLinkForm.tsx, PublicShareLanding.tsx, GuestAcceptPage.tsx, SharingSettingsTab.tsx, scopedClient.ts, routes.ts}`
- Contract/input: `InviteGuestRequest { email, target_kind, target_id, role, message?, expires_in_days }`, `AcceptInvitationRequest { display_name }`, `CreateShareLinkRequest { target_kind, target_id, role, expires_at, max_uses?, label? }`; tokens are 32 random bytes base64url (43 chars) stored as SHA-256 and compared in constant time by `ShareLinkRepository::find_link_by_token_hash` and `GuestInvitationRepository::find_invitation_by_token_hash`, which never log or return the hash; `ScopedToken::mint(tenant_id, target, role, ttl 15 min)` signed with the F038 key; rate limits 60/min per IP and 600/h per token through F038 `rate_limit_buckets`.
- Output/behavior: `POST /api/v1/guests/invite` rejects `owner` and `admin` with `400 guest_role_not_allowed`, inserts through `GuestInvitationRepository`, publishes `guest.invited.v1 { email, accept_url, expires_at }`, returns `accept_url` to the inviter; `POST /public/guests/accept/{token}` runs one `UnitOfWork` that reuses or creates the guest via `GuestUserRepository::find_guest_by_email(tenant_id, email)` with an F002 user flagged `is_guest`, writes the grant with `ShareRepository::insert`, sets `accepted_at` with `GuestInvitationRepository::accept_invitation(invitation_id, user_id)`, publishes `guest.accepted.v1`, opens an F038 session, and returns `{ redirect_to }`; expired, used, or unknown tokens → `404`; `POST /api/v1/share-links` enforces the 30-day cap (`400 max_30_days`) and link roles, returns `url` once, publishes `share-link.created.v1`; `DELETE /api/v1/share-links/{id}` sets `revoked_at` through `ShareLinkRepository` and publishes `share-link.revoked.v1`; the admin settings tab lists links through `list_active_links(target_kind, target_id)`; `GET /public/share/{token}` checks revocation, expiry, and `max_uses`, increments `use_count` with `ShareLinkRepository::increment_use_count(link_id)` in the same `UnitOfWork`, mints the scoped token, audits `share-link.resolve` with an IP hash, and answers `429 rate_limited` over the limits; `LinkPrincipal` builds the gateway context `{ roles: [], scopes: ["share-link:<kind>:<id>:<role>"] }` so guest and link principals skip role bindings; UI: invite form, link section with copy-once URL and revoke, landing page rendering the target read-only or the form with an expiry banner, guest accept page, admin settings tab listing links; telemetry `guest_invited`, `share_link_created`, `share_link_copied`, `share_link_revoked`, `share_link_opened`.
- Dependencies: T141 tables, `ShareRepository`, use cases, and dialog; the shared `Repository` and `UnitOfWork` contracts in `crates/persistence`; F038 session store, signing key, and rate-limit buckets; F002 user creation for guests; tracing redaction for public path parameters.
- Feature flag: `F036_FEATURE` gates public routes and the landing route.

## TDD

- Failing test first: `testing/features/F036/api/guest_tests.rs::guest_invite_owner_role_invalid`, `::guest_invite_publishes_event_with_accept_url`, `::guest_accept_creates_identity_and_grant`, `::guest_accept_reuses_existing_email`, `::guest_accept_expired_token_not_found`, `::guest_workspace_list_only_granted`; `testing/features/F036/api/link_tests.rs::link_create_returns_url_once`, `::link_expiry_over_30_days_invalid`, `::link_resolve_mints_scoped_token`, `::link_max_uses_exhausted_not_found`, `::link_revoked_resolve_not_found`, `::link_resolve_rate_limited`, `::link_token_stored_hashed`, all driving the routes and repository traits with no SQL in the test crate
- Targeted command: `cargo xtask test-feature F036`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: fixed token RNG seed and signing key; fixed-clock rate limiter; in-memory outbox recorder; F038 session store against the test schema

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Public routes mounted under `/public` in `services/api/src/router.rs` with rate limiting; link, invitation, and guest repositories registered in `crates/persistence/src/sharing/mod.rs` and `cargo xtask check-persistence` passes; landing and accept routes registered in `apps/web/src/features/sharing/routes.ts`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S072
- [ ] `finished_at` recorded
