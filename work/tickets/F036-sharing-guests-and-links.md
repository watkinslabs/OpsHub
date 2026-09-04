---
id: F036
type: feature
status: planned
priority: P1
owner: platform
estimate: 8
target_milestone: M3
parent_epic: E004
depends_on: [F003, F005]
blocks: [F023, F045, F050, F059]
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/sharing/**, crates/persistence/src/sharing/**, crates/auth/src/sharing/**, services/api/src/sharing/**, apps/web/src/features/sharing/**, services/api/migrations/*_sharing_*.sql, testing/features/F036/**]
feature_flag: F036_FEATURE
flag_default: off
branch: f036-sharing-guests-and-links
started_at: null
finished_at: null
---

# F036 — Sharing, guests, and links

## 1. Identity and dates

- Branch: `f036-sharing-guests-and-links`
- Capability area: authorization and collaboration (spec 5.4b COLLAB-03, 5.4a DOC-02 share links, 5.8 SEC-01 sharing administration, section 10 external sharing decision)
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4; `docs/capability-contracts.md` row F036
- Aggregate: `share`
- Module slug: `sharing`

## 2. Requirement specification

### Problem and user outcome

Workspace membership from F005 is too coarse: a sheet owner needs to give one contractor comment access to one sheet, hand a client a read-only link that stops working after the review week, and block one group from a sensitive dashboard even though they can see the rest of the workspace. None of that may leak tenant discovery to outsiders.

As a resource owner, I want to share a sheet, report, dashboard, folder, or workspace with users, groups, guests, or an expiring link using a specific role, and to deny a principal explicitly, so that collaborators get exactly the access they need and nothing more.

### Functional requirements

- **FR-F036-01:** An actor with `resource-owner` (or the `admin` role) on the target can `POST /api/v1/shares` with `{ target_kind, target_id, principal: { kind: user|group|guest, id }, role: owner|admin|editor|commenter|viewer|form_submitter, effect: allow|deny, expires_at? }` where `target_kind` is `workspace`, `folder`, `sheet`, `view`, `report`, `dashboard`, or `document`; the response returns the share with UUIDv7 `id` and `version` 1 and publishes `share.granted.v1`.
- **FR-F036-02:** One grant exists per `(target, principal)`; a second `POST` for the same pair returns `409 conflict` with `field_errors.principal = "already_shared"`; `PATCH /api/v1/shares/{id}` changes `role`, `effect`, or `expires_at` with `If-Match` and publishes `share.updated.v1`.
- **FR-F036-03:** `DELETE /api/v1/shares/{id}` revokes the grant and publishes `share.revoked.v1`; revoking or downgrading the last `owner` grant on a target returns `409 conflict` with `field_errors.role = "last_owner"`.
- **FR-F036-04:** Effective access is evaluated by the F003 engine through the `ShareGrantSource`: any `deny` grant for the actor or its groups on the target or an ancestor denies; otherwise the `allow` grant closest to the target wins, so a sheet-level `viewer` narrows a workspace-level `editor`; with no applicable grant the result is deny.
- **FR-F036-05:** `GET /api/v1/{target_kind}/{target_id}/shares` lists direct grants and inherited grants (each inherited entry carries `inherited_from: { target_kind, target_id }`) with cursor paging, `limit` 1–200, and filters `principal_kind` and `effect`; it requires `resource-owner` or `admin` on the target.
- **FR-F036-06:** `POST /api/v1/guests/invite` with `{ email, target_kind, target_id, role: editor|commenter|viewer|form_submitter, message? (≤ 1,000 chars), expires_in_days (1–14, default 7) }` creates a `guest_invitations` row with a SHA-256 token hash, publishes `guest.invited.v1` carrying the accept URL for F037 email delivery, and returns `{ invitation_id, accept_url, expires_at }` only to the inviter; `owner` and `admin` roles for guests return `400 invalid` with `field_errors.role = "guest_role_not_allowed"`.
- **FR-F036-07:** `POST /public/guests/accept/{token}` with `{ display_name (1–120 chars) }` validates the unexpired, unused token, creates or reuses the `guest_users` row for the email in that tenant, creates the `shares` grant from the invitation, marks the invitation `accepted_at`, publishes `guest.accepted.v1`, establishes an F038 session, and returns `{ redirect_to }`; an expired, used, or unknown token returns `404 not_found`.
- **FR-F036-08:** Guest principals never inherit tenant-wide or workspace-member access: `GET /api/v1/workspaces` for a guest returns only workspaces reachable through explicit grants, search is limited to granted targets, and any route outside granted targets returns `404 not_found`.
- **FR-F036-09:** An actor with `resource-owner` or `admin` can `POST /api/v1/share-links` with `{ target_kind, target_id, role: viewer|commenter|form_submitter, expires_at (≤ 30 days from now, default 7 days), max_uses? (1–10,000), label? }`; the response returns the URL with the 43-character token exactly once and publishes `share-link.created.v1`; an `expires_at` beyond 30 days returns `400 invalid` with `field_errors.expires_at = "max_30_days"`.
- **FR-F036-10:** `DELETE /api/v1/share-links/{id}` revokes the link immediately, publishes `share-link.revoked.v1`, and every later `GET /public/share/{token}` and scoped-token use returns `404 not_found`.
- **FR-F036-11:** `GET /public/share/{token}` resolves an unexpired, unrevoked link under its `max_uses`, increments `use_count`, and returns `{ target_kind, target_id, role, expires_at, scoped_token }` where `scoped_token` is a 15-minute bearer whose gateway context is `{ tenant_id, actor_id: link principal, roles: [], scopes: ["share-link:<target_kind>:<target_id>:<role>"] }`; the route is rate limited to 60 requests per minute per IP and 600 per hour per token.
- **FR-F036-12:** A scoped-token context can read only its target (and the target's rows, views, comments, and files per role) and never lists workspaces, searches, or reads other resources; writes return `403 denied` except `form_submitter` submissions to a published form (F014) and edits inside an explicitly scoped view (F013, F050), and the target owner is never revealed beyond display name.
- **FR-F036-13:** Grants with `expires_at` in the past are ignored by evaluation and swept hourly into `share.revoked.v1` with `reason = expired`; expired links and invitations are swept the same way.
- **FR-F036-14:** The web app renders a `ShareDialog` on workspace, sheet, report, and dashboard headers with a people list and role selectors, add-people search for users and groups, a `Deny` option for admins, a guest invite form, a link section with role, expiry (max 30 days), copy-once URL, and revoke, plus a public `/share/{token}` landing page that renders the target read-only or the form.
- **FR-F036-15:** Every mutation requires `Idempotency-Key`, writes an `audit_events` row with actor, before/after, and correlation ID, and publishes the matching event through the outbox; cross-tenant IDs return `404 not_found`; an `editor` without owner or admin rights calling any share route returns `403 denied`.

### Non-functional requirements

- **NFR-F036-01 Performance:** share grant evaluation adds at most 5 ms p95 to an authorization check through a per-request cache keyed by `(actor_id, target)`; listing 200 grants responds under 500 ms p95; link resolution responds under 300 ms p95 (spec section 6).
- **NFR-F036-02 Security/privacy:** link and invitation tokens are 32 random bytes encoded base64url, stored only as SHA-256 hashes, and compared in constant time; links expire within 30 days, are revocable, grant no tenant discovery, and cannot write except through published forms or scoped views (spec section 10); rate limits and audit entries apply to every public route; guests are isolated by explicit grants only.
- **NFR-F036-03 Accessibility:** the share dialog and public landing page pass axe with zero serious violations; role selectors are native selects or ARIA listboxes; copy-link success and revocation are announced via a live region; the dialog traps and restores focus.
- **NFR-F036-04 Reliability/observability:** grant evaluation failures fail closed (`denied`); sweeper jobs are idempotent; metrics `share_grants_total`, `share_link_resolutions_total`, `share_link_rate_limited_total`, and `guest_accepts_total` are exported; spans carry `tenant_id`, `target_kind`, `target_id`, `principal_kind`, and `correlation_id`.

### Scope

Included: share grants with six roles and allow/deny effect, inheritance and narrowing rules through `ShareGrantSource`, last-owner protection, share listing with inherited entries, guest invitations and acceptance with guest identity, share links with 30-day cap, use limits, revocation, scoped tokens, rate limits, expiry sweeper, share dialog, public landing page, audit and outbox events.

Excluded: role definitions and ACL storage for roles (F003), workspace membership (F005), invitation and link email delivery (F037 consumes `guest.invited.v1` and `share-link.created.v1`), public form submission semantics (F014), scoped-view editing rules (F013, F050), publication and embed tokens (F059), SCIM-provisioned guests (F026), document-specific link previews (F045).

## 3. UX specification

- Entry points: `Share` button on workspace, sheet, report, and dashboard headers opening `ShareDialog`; folder context menu `Share`; guest email link `/guests/accept/{token}`; public link `/share/{token}`; admin `Sharing` tab in workspace settings listing all links.
- Primary flow: owner opens `Share` on sheet "Launch plan", types `dana` and picks her as `Commenter`, adds group `Contractors` as `Viewer`, invites `client@example.com` as `Viewer` for 7 days, creates a `Viewer` link expiring in 14 days, clicks `Copy link`; the client opens the link and sees the sheet read-only with an `Expires in 14 days` banner; the owner later revokes the link and the client sees `This link is no longer valid`.
- Loading: skeleton rows in the people list; Empty: `Only you have access`; Error: banner with `correlation_id` and retry; Success: toast `Shared with Dana Ruiz`, `Link copied`; Stale/conflict: role change on a stale version shows `Sharing changed` with reload; Offline: dialog read-only with offline badge.
- Permission-denied: editors see a read-only people list with `Only owners and admins can change sharing`; guests never see the `Share` button; a link holder sees the landing page without navigation, search, or workspace chrome; a revoked or expired link shows the not-found page with `This link is no longer valid`.
- Responsive: dialog becomes a full-screen sheet under 640 px; the landing page reuses the responsive grid or form.
- Keyboard: Tab through people rows, arrow keys change role in the select, `Delete` on a row prompts revoke, `Escape` closes; copy button is a real button with announced result; focus returns to the `Share` button on close; motion respects `prefers-reduced-motion`.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide `Share2`, `Link`, `UserPlus`, `Ban`, `Copy`, `Clock`, `ShieldOff`; tokens from `apps/web/src/design/tokens.css`.

- Design: `design/artboards/Sharing.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

### Rust backend

- Domain entities in `crates/domain/src/sharing/`: `Share { id, tenant_id, target: TargetRef, principal: PrincipalRef { kind: User|Group|Guest, id }, role: ShareRole, effect: Effect { Allow, Deny }, expires_at, version, audit fields }`, `ShareLink { id, tenant_id, target, role: LinkRole, token_hash, label, expires_at, max_uses, use_count, revoked_at, version, audit fields }`, `GuestInvitation { id, tenant_id, email, target, role, message, token_hash, expires_at, accepted_at, invited_by, created_at }`, `GuestUser { id, tenant_id, user_id, email, display_name, invited_by, created_at, deactivated_at }`, `EffectiveAccess { role: Option<ShareRole>, denied: bool, source: GrantSource }`.
- Use cases: `grant_share`, `update_share`, `revoke_share`, `list_shares`, `evaluate_access`, `invite_guest`, `accept_invitation`, `create_link`, `revoke_link`, `resolve_link`, `sweep_expired`; `crates/auth/src/sharing/`: `ShareGrantSource` implementing the F003 `GrantSource` trait, `LinkPrincipal` context builder, and `ScopedToken` mint and verify (HMAC-SHA256 with the F038 signing key, 15-minute TTL).
- API endpoints (`services/api/src/sharing/`): `GET /api/v1/{target_kind}/{target_id}/shares`, `POST /api/v1/shares`, `PATCH /api/v1/shares/{id}`, `DELETE /api/v1/shares/{id}`, `POST /api/v1/share-links`, `DELETE /api/v1/share-links/{id}`, `GET /public/share/{token}`, `POST /api/v1/guests/invite`, `POST /public/guests/accept/{token}`. DTOs `CreateShareRequest`, `UpdateShareRequest`, `ShareResponse { id, target, principal: { kind, id, display_name }, role, effect, expires_at, inherited_from?, version }`, `Page<ShareResponse>`, `CreateShareLinkRequest`, `ShareLinkResponse { id, url? (create only), role, expires_at, max_uses, use_count, revoked_at, version }`, `ResolveLinkResponse`, `InviteGuestRequest`, `InviteGuestResponse`, `AcceptInvitationRequest`, `AcceptInvitationResponse`.
- Events: `share.granted.v1`, `share.updated.v1`, `share.revoked.v1`, `share-link.created.v1`, `share-link.revoked.v1`, `guest.invited.v1`, `guest.accepted.v1`; payloads carry `target_kind`, `target_id`, `principal_kind`, `principal_id`, `role`, `effect`, and for invitations `email`, `accept_url`, `expires_at`.
- Authorization: share, link, and invite mutations require `resource-owner` or `admin` on the target through `authz::require(actor, Permission::Share, target)`; listing requires the same; `evaluate_access` walks `target → folder → workspace` ancestors from F005, collects grants for the actor and its F002 groups, applies deny-wins then closest-allow; guest and link principals skip role bindings entirely; failures fail closed.
- Validation: `target_kind` enum, `role` enum with guest and link restrictions, `expires_at` ≤ now + 30 days for links and ≤ 14 days for invitations, `max_uses` 1–10,000, `email` RFC 5322 and ≤ 254 chars, `display_name` 1–120; idempotency for 24 hours; `If-Match` on share updates; rate limits via F038 `rate_limit_buckets`.
- Error mapping: `ShareError::AlreadyShared → 409 conflict`, `ShareError::LastOwner → 409 conflict`, `ShareError::GuestRoleNotAllowed → 400 invalid`, `ShareError::LinkExpiryTooLong → 400 invalid`, `ShareError::LinkExhausted → 404 not_found`, `ShareError::TokenInvalid → 404 not_found`, `ShareError::StaleVersion → 409 conflict`, `ShareError::NotFound → 404 not_found`, `AuthzError::Denied → 403 denied`, `RateLimit::Exceeded → 429 rate_limited`.
- Persistence (`crates/persistence/src/sharing/`): `ShareRepository` owns `shares`; `ShareLinkRepository` owns `share_links`; `GuestInvitationRepository` owns `guest_invitations`; `GuestUserRepository` owns `guest_users`. Each implements the shared `Repository` contract (`get`, `list` with cursor pagination, `insert`, `update` under an expected version, `soft_delete`, `restore`, `purge`) and adds named queries `list_for_target(target_kind, target_id)`, `list_for_principal(principal_kind, principal_id)`, `find_grant(target, principal)`, `lock_owner_grants(target_kind, target_id)`, `count_owners(target_kind, target_id)`, `revoke(share_id)`, `find_link_by_token_hash(hash)`, `increment_use_count(link_id)`, `list_active_links(target_kind, target_id)`, `find_invitation_by_token_hash(hash)`, `accept_invitation(invitation_id, user_id)`, `find_guest_by_email(tenant_id, email)`, `claim_expired(cutoff, limit)`; the tenant predicate, soft-delete filter, version check, audit row, and outbox enqueue come from the base contract. `lock_owner_grants` is the former `select ... for update` on the target's owner grants: the same row lock in the same transaction still serializes concurrent revokes and downgrades, only the SQL moved into `crates/persistence`. Multi-table writes — granting and updating a share (grant plus audit plus outbox), revoking under the last-owner lock, link resolution with its `use_count` increment and resolve audit, and guest acceptance (invitation `accepted_at`, `guest_users` row, `shares` grant, session) — each run in one `UnitOfWork` that owns the transaction. Token hashes are compared inside `find_link_by_token_hash` and `find_invitation_by_token_hash` and are never logged or returned. The F003 policy engine reads effective grants through `ShareRepository::list_for_principal` and `list_for_target`, never through its own SQL. Per decision 2.1 the use cases above depend on these repository traits and contain no SQL: no SQL string, `sqlx::query*` call, or connection exists in `crates/domain/src/sharing` or `services/api/src/sharing`, and the permission-negative tests drive the repository traits rather than raw queries.

### PostgreSQL/SQLx

- Migration `*_sharing_*.sql` creates `shares(id uuid pk, tenant_id uuid not null references tenants(id) on delete restrict, target_kind text not null, target_id uuid not null, principal_kind text not null, principal_id uuid not null, role text not null, effect text not null default 'allow', expires_at timestamptz, version bigint not null default 1, created_by uuid not null references users(id) on delete restrict, created_at timestamptz not null default now(), updated_by uuid references users(id) on delete restrict, updated_at timestamptz)`, `share_links(id uuid pk, tenant_id uuid not null references tenants(id) on delete restrict, target_kind text not null, target_id uuid not null, role text not null, token_hash bytea not null, label text, expires_at timestamptz not null, max_uses int, use_count int not null default 0, revoked_at timestamptz, version bigint not null default 1, created_by uuid not null references users(id) on delete restrict, created_at timestamptz not null default now(), updated_by uuid references users(id) on delete restrict, updated_at timestamptz)`, `guest_invitations(id uuid pk, tenant_id uuid not null references tenants(id) on delete restrict, email citext not null, target_kind text not null, target_id uuid not null, role text not null, message text, token_hash bytea not null, expires_at timestamptz not null, accepted_at timestamptz, invited_by uuid not null references users(id) on delete restrict, created_at timestamptz not null default now())`, `guest_users(id uuid pk, tenant_id uuid not null references tenants(id) on delete restrict, user_id uuid not null references users(id) on delete restrict, email citext not null, display_name text not null, invited_by uuid references users(id) on delete restrict, created_at timestamptz not null default now(), deactivated_at timestamptz)`.
- Column shapes per decision section 2: this feature's schema carries no array column and no `jsonb` column — every enumerable set it needs is already a row (one `shares` row per grant, one `share_links` row per link) rather than a repeating group. `shares.role`, `shares.effect`, `share_links.role`, `guest_invitations.role`, `shares.target_kind`, `share_links.target_kind`, `guest_invitations.target_kind`, and `shares.principal_kind` are closed enums whose members carry no data and that a tenant cannot extend, so decision section 2's enum rule keeps them as `text` with the `check` constraints below; they are deliberately not lookup tables and must not be converted into any.
- Polymorphic references: `target_id` addresses one of seven target tables selected by `target_kind` (`workspace`, `folder`, `sheet`, `view`, `report`, `dashboard`, `document`), and `shares.principal_id` addresses `users` when `principal_kind` is `user` or `guest` and `groups` when it is `group`, so neither column can carry a single declared foreign key. Integrity is enforced instead by the `target_kind`/`principal_kind` `check` constraints, by `ShareRepository::insert` and `ShareLinkRepository::insert` resolving the referent in the same `UnitOfWork` transaction before the row is written and returning `ShareError::NotFound` when it is absent or in another tenant, by each target feature publishing its delete so the `sharing.sweep_expired` job's `claim_expired` pass also revokes grants whose target no longer resolves, and by the migration test `sharing_polymorphic_refs_have_no_orphans` asserting the reconciliation leaves no orphan grant. Every non-polymorphic reference above is declared, with `on delete restrict` so a tenant, inviter, or guest identity cannot be removed while a grant references it.
- Invariants: unique `shares(tenant_id, target_kind, target_id, principal_kind, principal_id)`; `check (role in ('owner','admin','editor','commenter','viewer','form_submitter'))`; `check (effect in ('allow','deny'))`; `check (principal_kind <> 'guest' or role in ('editor','commenter','viewer','form_submitter'))`; `check (share_links.role in ('viewer','commenter','form_submitter'))`; `check (share_links.expires_at <= created_at + interval '30 days')`; unique `share_links(token_hash)`; unique `guest_invitations(token_hash)`; unique `guest_users(tenant_id, email)`; the last-owner rule is unchanged and still enforced by a row lock on the target's owner grants inside the revoke transaction, taken by `ShareRepository::lock_owner_grants` and counted by `count_owners` within the same `UnitOfWork`.
- Indexes: `shares(tenant_id, target_kind, target_id)`, `shares(tenant_id, principal_kind, principal_id)`, `shares(expires_at) where expires_at is not null`, `share_links(tenant_id, target_kind, target_id) where revoked_at is null`, `share_links(expires_at) where revoked_at is null`, `guest_invitations(expires_at) where accepted_at is null`.
- Audit events: `share.grant`, `share.update`, `share.revoke`, `share.expire`, `share-link.create`, `share-link.revoke`, `share-link.resolve` (with IP hash), `guest.invite`, `guest.accept`.
- Retention/deletion: grants are hard-deleted on revoke because the audit row keeps the history; links and invitations keep rows with `revoked_at` or `accepted_at` for 90 days then are purged by the F027 job; migration rollback drops the four tables.

### React/TypeScript

- Routes: `/share/:token` and `/guests/accept/:token` in `apps/web/src/features/sharing/`; components `ShareDialog`, `PeopleList`, `PersonRow`, `RoleSelect`, `AddPeopleSearch`, `GuestInviteForm`, `LinkSection`, `LinkRow`, `CreateLinkForm`, `PublicShareLanding`, `GuestAcceptPage`, `SharingSettingsTab`.
- State: TanStack Query keys `['shares', targetKind, targetId, { cursor, principalKind, effect }]`, `['share-links', targetKind, targetId]`, `['share-resolve', token]`; scoped token kept in memory and attached by the API client for landing-page requests.
- API client: generated `SharingApi` with `listShares`, `createShare`, `updateShare`, `revokeShare`, `createShareLink`, `revokeShareLink`, `resolveShareLink`, `inviteGuest`, `acceptInvitation`.
- Optimistic updates: role change applies locally and rolls back on `conflict` with the stale banner; revoke removes the row and restores on error.
- Telemetry: `share_dialog_opened`, `share_granted`, `share_denied_set`, `share_revoked`, `guest_invited`, `share_link_created`, `share_link_copied`, `share_link_revoked`, `share_link_opened` with `target_kind` and `role`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F036-01 through FR-F036-15 in `testing/features/F036/requirements/cases.md`
- [ ] Failure/edge-case tests: duplicate grant, last owner revoke, guest owner role, link beyond 30 days, exhausted `max_uses`, expired token, revoked link reuse, stale version
- [ ] Permission-negative and tenant-isolation tests: editor calling share routes returns `denied`, guest listing workspaces sees only granted, link token cannot search or write, cross-tenant share returns `not_found`, deny beats inherited allow; these tests read and write through the sharing repository traits and contain no SQL of their own
- [ ] Rust unit tests: `crates/domain/src/sharing/` evaluation order, token hashing, expiry math against fake repository traits; `crates/auth/src/sharing/` scoped token mint and verify; `crates/persistence/src/sharing/` named queries and `lock_owner_grants` under concurrent revokes
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: uniqueness, role and effect checks, 30-day check, declared foreign keys and their `on delete restrict` behaviour, polymorphic reference reconciliation leaving no orphan grant, indexes, rollback
- [ ] React component tests: `ShareDialog`, `LinkSection`, `PublicShareLanding` states
- [ ] Browser E2E tests: share with user and group, invite guest and accept, create link, open, revoke
- [ ] Accessibility tests: axe on dialog and landing, keyboard role change, live region on copy
- [ ] Performance/load tests: evaluation overhead, 200-grant list, link resolution under rate limit

### Fast fanout configuration

- Test harness path: `testing/features/F036/`
- Feature flag: `F036_FEATURE`
- Fixture/seed factory: `testing/fixtures/sharing.rs` builds tenant, workspace with folder and sheet, owner, admin, editor, viewer, group `Contractors`, foreign tenant, and seeded grants (workspace editor for group, sheet deny for one user)
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC, fixed token RNG seed and signing key
- Mock/stub contracts: outbox recorder in memory; F038 session store real against the test schema; rate limiter with fixed clock
- Parallel isolation: one schema per test worker, tenant ID per test
- Targeted command: `cargo xtask test-feature F036`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F036/`

## 6. Acceptance criteria

```gherkin
Feature: Share grants, guests, and links

Scenario: Sheet-level viewer narrows workspace-level editor
  Given group Contractors has an editor grant on workspace "Ops"
  And Dana, a member of Contractors, has a viewer grant on sheet "Launch plan"
  When Dana patches a row in "Launch plan"
  Then the response is 403 denied and Dana can still read the sheet

Scenario: Explicit deny wins over inherited allow
  Given Dana has an editor grant on workspace "Ops"
  When an owner adds a deny grant for Dana on dashboard "Exec"
  Then Dana's read of "Exec" returns 404 not_found and share.granted.v1 with effect deny is published

Scenario: Editor cannot change sharing
  Given Eli has editor access to sheet "Launch plan"
  When Eli posts a share grant for Vic on the sheet
  Then the response is 403 denied and no grant exists

Scenario: Link expires and is revocable
  Given a viewer link on "Launch plan" expiring in 14 days
  When the client resolves the link, then the owner revokes it, then the client resolves again
  Then the first resolution returns a scoped token and the second returns 404 not_found

Scenario: Link holder cannot discover the tenant
  Given a scoped token from a viewer link on "Launch plan"
  When the holder calls GET /api/v1/workspaces and GET /api/v1/search
  Then both responses are 403 denied
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F003 (`GrantSource` trait, `authz::require`, audit writer, `resource_acls`), F005 (workspace and folder ancestry, membership); decisions sections 2–4; contracts row F036
- Blocks: F023 (dashboard sharing), F045 (document links and guest permissions), F050 (external editing through scoped views), F059 (publication tokens reuse the scoped-token pattern)
- Conflicts with: none (disjoint owned paths)
- External dependencies: none
- Risks and mitigations: ancestry walks on every check would be slow, so `evaluate_access` loads the ancestor chain once per request and caches results per `(actor, target)`; token leakage through logs is prevented by redacting `/public/share/*` and `/public/guests/accept/*` path parameters in tracing; the last-owner rule races under concurrent revokes, so `revoke_share` calls `ShareRepository::lock_owner_grants` and `count_owners` inside its `UnitOfWork`, which takes the same row lock in the same transaction and serializes the same writers; a guest accepted with a mistyped email creates an orphan identity, so acceptance reuses an existing `guest_users` row by email and admins can deactivate guests through F002.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F003 and F005 accepted and archived; `GrantSource` extension point present in `crates/auth`
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F036/`
- [ ] Migration file name and owned paths claimed
- [ ] Fixture factory and schema-per-worker isolation available in `testing/harness/`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation and sweep
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets`, `check-contracts`, and `check-persistence` pass
- [ ] Rollback verified: disable `F036_FEATURE` (evaluation falls back to F003 ACLs only), run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Owners can share workspaces, folders, sheets, views, reports, dashboards, and documents with users, groups, and invited guests using owner, admin, editor, commenter, viewer, or form submitter roles, deny specific principals, and create revocable links that expire within 30 days.
- Migration adds `shares`, `share_links`, `guest_invitations`, and `guest_users`; rollback drops them. Feature is off by default behind `F036_FEATURE`.
