---
id: S072
type: story
status: planned
parent_epic: E004
parent_feature: F036
depends_on: [S071]
owned_paths: [crates/domain/src/sharing/**, crates/auth/src/sharing/**, services/api/src/sharing/**, apps/web/src/features/sharing/**, testing/features/F036/**]
feature_flag: F036_FEATURE
branch: s072-guest-identity-and-links
started_at: null
finished_at: null
---

# S072 — Guest identity and links

## Identity

- Parent feature: `F036` Sharing, guests, and links
- Owner: platform
- Branch: `s072-guest-identity-and-links`
- Decision references: `docs/architecture-decisions.md` sections 3, 4, 6; `docs/capability-contracts.md` row F036

## Vertical slice

As a resource owner, I want to invite an outside collaborator by email as a scoped guest and to hand out a revocable read-only link that expires within 30 days, so that external people reach exactly one resource and never discover the rest of the tenant.

## Requirements

- **SR-S072-01:** `POST /api/v1/guests/invite` validates a guest-allowed role and `expires_in_days` 1–14, stores a SHA-256 token hash, publishes `guest.invited.v1` with `accept_url`, and returns `{ invitation_id, accept_url, expires_at }` to the inviter only (covers FR-F036-06).
- **SR-S072-02:** `POST /public/guests/accept/{token}` creates or reuses `guest_users` by `(tenant_id, email)`, writes the grant, marks `accepted_at`, publishes `guest.accepted.v1`, opens an F038 session, and returns `404 not_found` for expired, used, or unknown tokens (FR-F036-07).
- **SR-S072-03:** Guest principals bypass role bindings and workspace membership: workspace list and search return only granted targets and other routes return `404 not_found` (FR-F036-08).
- **SR-S072-04:** `POST /api/v1/share-links` enforces `expires_at` ≤ 30 days and roles `viewer|commenter|form_submitter`, returns the token URL once, and publishes `share-link.created.v1`; `DELETE` revokes with `share-link.revoked.v1` (FR-F036-09, FR-F036-10).
- **SR-S072-05:** `GET /public/share/{token}` is rate limited at 60/min per IP and 600/h per token, checks expiry, revocation, and `max_uses`, increments `use_count`, and mints a 15-minute `scoped_token` whose context carries only `share-link:<kind>:<id>:<role>` (FR-F036-11, NFR-F036-02).
- **SR-S072-06:** Scoped-token contexts read only their target and its rows, views, comments, and files per role; workspace list, search, and all writes return `403 denied` except `form_submitter` submissions and scoped-view edits (FR-F036-12).
- **SR-S072-07:** `GuestInviteForm`, `LinkSection`, `CreateLinkForm`, `PublicShareLanding`, and `GuestAcceptPage` render the states in ticket section 3 with copy-once URL and live-region announcements; expired links and invitations are swept hourly (FR-F036-13, FR-F036-14, NFR-F036-03).

## Surfaces

- Infrastructure/container: rate-limit buckets from F038 `rate_limit_buckets`; tracing redaction rule for `/public/share/*` and `/public/guests/accept/*`
- Rust service/API: `crates/domain/src/sharing/{link.rs, invitation.rs, guest.rs, token.rs, service_links.rs, service_guests.rs}`; `crates/auth/src/sharing/{link_principal.rs, scoped_token.rs}`; `services/api/src/sharing/{handlers_link.rs, handlers_guest.rs, public_routes.rs}`
- Data/migration: none new; uses `share_links`, `guest_invitations`, `guest_users` from S071
- React/UI: `apps/web/src/features/sharing/{GuestInviteForm.tsx, LinkSection.tsx, LinkRow.tsx, CreateLinkForm.tsx, PublicShareLanding.tsx, GuestAcceptPage.tsx, SharingSettingsTab.tsx, scopedClient.ts, routes.ts}`
- Mocks/fixtures: fixed token RNG and signing key; fixed-clock rate limiter; seeded viewer link with `max_uses` 2 and an invitation for `client@example.com`; Playwright uses a second browser context for the link holder

## TDD harness

- Test path: `testing/features/F036/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F036_FEATURE`
- Targeted command: `cargo xtask test-feature F036`
- Full command: `cargo xtask test-all`
- First failing tests: `guest_invite_owner_role_invalid`, `guest_accept_creates_identity_and_grant`, `guest_workspace_list_only_granted`, `link_expiry_over_30_days_invalid`, `link_revoked_resolve_not_found`, `link_scoped_token_cannot_search_or_write`, `link_resolve_rate_limited`

## Exit criteria

- [ ] Requirement tests SR-S072-01 through SR-S072-07 written first and failing
- [ ] Tasks T143 and T144 complete; public routes mounted outside the authenticated router with rate limiting
- [ ] Unit, API, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `services/api/src/sharing/public_routes.rs` mounted in `services/api/src/router.rs` under `/public`; `apps/web/src/features/sharing/PublicShareLanding.tsx` mounted at `/share/:token`
- [ ] Handoff evidence recorded in the F036 ticket
