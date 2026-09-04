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

### Interface

Conventions are F028's: `Page<T>`, the signed cursor, the error body with its six codes,
`Idempotency-Key`, and `If-Match`. `T?` is nullable; an absent optional field and an explicit `null`
are the same thing; timestamps are RFC 3339 UTC; ids are UUIDv7 strings; `version` increments by one
per write. Unlisted request fields are rejected with `400 invalid`. The two `/public/**` routes take
no session and no `Idempotency-Key`.

**`TargetRef`** — the addressed resource, used by every shape below

| Field | Type | Required | Constraint |
|---|---|---|---|
| `target_kind` | enum | yes | `workspace`, `folder`, `sheet`, `view`, `report`, `dashboard`, `document`, or `dynamic-view`; anything else → `400 invalid` with `field_errors.target_kind`. `dynamic-view` is grantable to users and groups (F050 FR-F050-05) but never to a `share_links` row: a dynamic view's public tokens are F050's own, so that kind is rejected on the link route with `field_errors.target_kind = "not_linkable"` |
| `target_id` | uuid | yes | must resolve in the caller's tenant; absent or foreign → `404 not_found`, never `denied` |

**`PrincipalRef`**

| Field | Type | Required | Constraint |
|---|---|---|---|
| `kind` | `"user" \| "group" \| "guest"` | yes | |
| `id` | uuid | yes | a `users` row for `user` and `guest`, a `groups` row for `group`, in the same tenant; otherwise `404 not_found` |

**`ShareRole`** — `owner`, `admin`, `editor`, `commenter`, `viewer`, `form_submitter`. These are the
authorization model's base roles; `form_submitter` is its `form-submitter`. Guests may hold only
`editor`, `commenter`, `viewer`, or `form_submitter` (`400 invalid` with
`field_errors.role = "guest_role_not_allowed"`); links may carry only `viewer`, `commenter`, or
`form_submitter`.

**`CreateShareRequest`** — `POST /api/v1/shares` (FR-F036-01)

| Field | Type | Required | Constraint |
|---|---|---|---|
| `target_kind` / `target_id` | `TargetRef` | yes | caller holds `share` on the target through `owner` or `admin`, else `403 denied` |
| `principal` | `PrincipalRef` | yes | one grant per `(target, principal)`; a second → `409 conflict` with `field_errors.principal = "already_shared"` |
| `role` | `ShareRole` | yes | guest restriction above |
| `effect` | `"allow" \| "deny"` | no | default `allow`; `deny` requires `admin` or `owner` on the target |
| `expires_at` | timestamp? | no | must be in the future; a past value → `400 invalid` with `field_errors.expires_at` |

**`UpdateShareRequest`** — `PATCH /api/v1/shares/{id}`, every field optional, at least one present

| Field | Type | Required | Constraint |
|---|---|---|---|
| `role` | `ShareRole` | no | downgrading the last `owner` grant → `409 conflict` with `field_errors.role = "last_owner"` |
| `effect` | `"allow" \| "deny"` | no | |
| `expires_at` | timestamp? | no | explicit null clears the expiry |

**`ShareResponse`**

| Field | Type | Notes |
|---|---|---|
| `id` | uuid | |
| `target` | `TargetRef` | the target the grant is stored against, which for an inherited entry is the ancestor |
| `principal` | `{ kind, id, display_name }` | `display_name` is the user, group, or guest label; a guest's email is not returned |
| `role` | `ShareRole` | |
| `effect` | `"allow" \| "deny"` | |
| `expires_at` | timestamp? | |
| `inherited_from` | `{ target_kind, target_id }`? | present only on an entry inherited from an ancestor; absent on a direct grant (FR-F036-05) |
| `version` | integer | |
| `created_at` / `created_by` / `updated_at` / `updated_by` | | direct grants only |

`GET /api/v1/{target_kind}/{target_id}/shares` returns `Page<ShareResponse>` sorted by
`principal.display_name` with `id` as tiebreak, `limit` 1–200 (default 50), filters
`principal_kind` (`user`, `group`, `guest`) and `effect` (`allow`, `deny`). Direct grants come before
inherited ones. `DELETE /api/v1/shares/{id}` takes `If-Match` and returns `204`.

**`CreateShareLinkRequest`** — `POST /api/v1/share-links` (FR-F036-09)

| Field | Type | Required | Constraint |
|---|---|---|---|
| `target_kind` / `target_id` | `TargetRef` | yes | caller holds `owner` or `admin`, else `403 denied` |
| `role` | `"viewer" \| "commenter" \| "form_submitter"` | yes | any other member → `400 invalid` with `field_errors.role` |
| `expires_at` | timestamp | no | default now + 7 days; beyond now + 30 days → `400 invalid` with `field_errors.expires_at = "max_30_days"`; in the past → `400 invalid` |
| `max_uses` | integer? | no | 1–10,000; `null` means unlimited within the expiry |
| `label` | string? | no | ≤ 120 chars, shown in the admin sharing tab |

**`ShareLinkResponse`**

| Field | Type | Notes |
|---|---|---|
| `id` | uuid | |
| `target` | `TargetRef` | |
| `role` | `"viewer" \| "commenter" \| "form_submitter"` | |
| `url` | string? | the full URL with the 43-character token; present **only** in the `201` create body and never again — the token is stored as a SHA-256 hash |
| `label` | string? | |
| `expires_at` | timestamp | |
| `max_uses` | integer? | |
| `use_count` | integer | |
| `revoked_at` | timestamp? | set by `DELETE /api/v1/share-links/{id}`, which returns `204` |
| `version` | integer | |

**`ResolveLinkResponse`** — `GET /public/share/{token}`, no session (FR-F036-11)

| Field | Type | Notes |
|---|---|---|
| `target_kind` / `target_id` | enum / uuid | what the landing page renders |
| `role` | `"viewer" \| "commenter" \| "form_submitter"` | |
| `expires_at` | timestamp | drives the `Expires in N days` banner |
| `scoped_token` | string | the bearer described below; valid 15 minutes and not refreshable |

An expired, revoked, unknown, or use-exhausted token returns `404 not_found` — the four cases are
indistinguishable to the caller, so a token cannot be probed. The route is limited to 60 requests
per minute per IP and 600 per hour per token; over either is `429 rate_limited`.

**`ScopedContext`** — the gateway context a `scoped_token` resolves to, and the type that must never
widen. It is the same struct shape the authenticated gateway hands every service
(`{ tenant_id, actor_id, roles, scopes, correlation_id }`), with these values and no others.

| Field | Type | Notes |
|---|---|---|
| `tenant_id` | uuid | the link's tenant, taken from the link row and never from the request |
| `actor_id` | uuid | the link principal — the link's own id, not the creator's user id; the creator is never impersonated |
| `roles` | string array | **always empty.** A scoped actor holds no role and no role binding is consulted, so nothing a role grants can reach it |
| `scopes` | string array | **exactly one entry**, `share-link:<target_kind>:<target_id>:<role>` |
| `correlation_id` | uuid | per request, as everywhere else |
| `expires_at` | timestamp | mint time plus 15 minutes; there is no refresh and no renewal route |
| `link_id` | uuid | so a revoked link invalidates a live token: every request re-checks the link is unrevoked, unexpired, and within `max_uses` |

What the single scope permits, and nothing beyond it (FR-F036-12): read of that one target and of
the rows, views, comments, and files reachable *below* it under the named role. It grants nothing on
an ancestor, nothing on a sibling, and no listing route — `GET /api/v1/workspaces`, search, and any
other collection return `403 denied`. Every write returns `403 denied` with two exceptions, both
scoped to the same target: a `form_submitter` submission to a published form (F014) and an edit
inside an explicitly scoped view (F013, F050). A scoped context never resolves a second scope, never
gains one from a role, and never inherits a grant, so the guarantee "a scoped actor's authority is
the intersection of the minting user's permissions and the token's stored scope" cannot be widened
by any later feature: widening it means minting a different token, not adding to this one. The
target's owner is never revealed beyond display name.

**`InviteGuestRequest`** — `POST /api/v1/guests/invite` (FR-F036-06)

| Field | Type | Required | Constraint |
|---|---|---|---|
| `email` | string | yes | RFC 5322, ≤ 254 chars, case-insensitive; matched against `guest_users(tenant_id, email)` on acceptance |
| `target_kind` / `target_id` | `TargetRef` | yes | caller holds `owner` or `admin` |
| `role` | `"editor" \| "commenter" \| "viewer" \| "form_submitter"` | yes | `owner` or `admin` → `400 invalid` with `field_errors.role = "guest_role_not_allowed"` |
| `message` | string? | no | ≤ 1,000 chars, carried into the invitation email |
| `expires_in_days` | integer | no | 1–14, default 7 |

**`InviteGuestResponse`** — returned to the inviter only

| Field | Type | Notes |
|---|---|---|
| `invitation_id` | uuid | |
| `accept_url` | string | contains the raw token, returned once here and once in `guest.invited.v1` for F037 to mail; only the SHA-256 hash is stored |
| `expires_at` | timestamp | |

**`AcceptInvitationRequest`** / **`AcceptInvitationResponse`** — `POST /public/guests/accept/{token}`

| Field | Type | Required | Constraint |
|---|---|---|---|
| `display_name` | string | yes | 1–120 chars after trim; the name shown on the guest's grants and comments |

`AcceptInvitationResponse` is `{ redirect_to: string }`, a relative path to the granted target, and
the response sets the F038 session cookie. An expired, already-accepted, or unknown token returns
`404 not_found`.

**Status codes**

| Status | `code` | Produced by |
|---|---|---|
| `400` | `invalid` | any constraint above: unknown `target_kind`, guest or link role restriction, link expiry beyond 30 days, past `expires_at`, malformed email, `display_name` bounds |
| `403` | `denied` | the caller can see the target but lacks `share` on it — an `editor` calling any share, link, or invite route; a scoped actor calling anything outside its one scope |
| `404` | `not_found` | a share, link, invitation, or target id that does not exist or belongs to another tenant; an expired, revoked, exhausted, or unknown public token; a target the caller cannot see, which is why an unauthorized read is never `denied` |
| `409` | `conflict` | a second grant for the same `(target, principal)`; revoking or downgrading the last `owner`; a stale `If-Match`; an `Idempotency-Key` replayed with a different body |
| `429` | `rate_limited` | the per-IP and per-token limits on `GET /public/share/{token}` and the same limits on `POST /public/guests/accept/{token}` |
| `503` | `unavailable` | the database or outbox is unreachable; grant evaluation itself never returns this — it fails closed as `denied` (NFR-F036-04) |

### Use case signatures

In `crates/domain/src/sharing/`, with the token and context types in `crates/auth/src/sharing/`.
`ctx` carries tenant, actor, and correlation id; a use case takes a `UnitOfWork` or repository
traits, never a pool or connection, and returns the shared `DomainError` mapped above.

```rust
fn grant_share(ctx: &Ctx, uow: &mut UnitOfWork, req: CreateShare) -> Result<Share, DomainError>;
fn update_share(ctx: &Ctx, uow: &mut UnitOfWork, id: ShareId, expected: Version, req: UpdateShare) -> Result<Share, DomainError>;
fn revoke_share(ctx: &Ctx, uow: &mut UnitOfWork, id: ShareId, expected: Version) -> Result<(), DomainError>;
fn list_shares(ctx: &Ctx, repo: &dyn ShareRepository, target: TargetRef, filter: ShareFilter, cursor: Option<Cursor>, limit: u16) -> Result<Page<Share>, DomainError>;
fn evaluate_access(ctx: &Ctx, repo: &dyn ShareRepository, actor: &ActorRef, target: TargetRef, ancestors: &AncestorChain) -> Result<EffectiveAccess, DomainError>;
fn invite_guest(ctx: &Ctx, uow: &mut UnitOfWork, req: InviteGuest) -> Result<(GuestInvitation, RawToken), DomainError>;
fn accept_invitation(ctx: &Ctx, uow: &mut UnitOfWork, token: &RawToken, display_name: String) -> Result<AcceptedInvitation, DomainError>;
fn create_link(ctx: &Ctx, uow: &mut UnitOfWork, req: CreateShareLink) -> Result<(ShareLink, RawToken), DomainError>;
fn revoke_link(ctx: &Ctx, uow: &mut UnitOfWork, id: ShareLinkId, expected: Version) -> Result<(), DomainError>;
fn resolve_link(ctx: &Ctx, uow: &mut UnitOfWork, token: &RawToken, now: DateTime<Utc>) -> Result<ResolvedLink, DomainError>;
fn sweep_expired(ctx: &Ctx, uow: &mut UnitOfWork, cutoff: DateTime<Utc>, limit: u32) -> Result<SweepSummary, DomainError>;
```

In `crates/auth/src/sharing/`. `ShareGrantSource` is this feature's implementation of the F003
`GrantSource` trait — F003 owns that trait and calls it during evaluation; F036 supplies the grants:

```rust
impl GrantSource for ShareGrantSource {
    fn grants_for(&self, ctx: &Ctx, actor: &ActorRef, chain: &AncestorChain) -> Result<Vec<Grant>, DomainError>;
}

fn mint_scoped_token(ctx: &Ctx, link: &ShareLink, now: DateTime<Utc>) -> Result<ScopedToken, DomainError>;
fn verify_scoped_token(token: &str, repo: &dyn ShareLinkRepository, now: DateTime<Utc>) -> Result<ScopedContext, DomainError>;
```

`mint_scoped_token` is the only constructor of a `ScopedContext`; its `roles` is empty and its
`scopes` holds exactly the one entry above by construction, so no caller can assemble a wider one.
`verify_scoped_token` re-reads the link row on every request and returns `DomainError::NotFound`
when it is revoked, expired, or exhausted.

Transaction boundaries. `grant_share`, `update_share`, and `revoke_share` each write the `shares`
row, the audit row, and the outbox entry in one `UnitOfWork`; `revoke_share` and a downgrade also
take `lock_owner_grants` and `count_owners` inside that same transaction, which is what makes the
last-owner rule hold under two concurrent revokes rather than letting both see one remaining owner.
`accept_invitation` runs the invitation's `accepted_at`, the `guest_users` row, the `shares` grant,
the audit row, and `guest.accepted.v1` in one `UnitOfWork`, so a guest identity never exists without
its grant and a consumed token never leaves an unusable half-state. `resolve_link` holds one
`UnitOfWork` over the `use_count` increment, the `max_uses` check, and the resolve audit row, so the
use limit cannot be exceeded by concurrent resolutions; the token is minted after that transaction
commits. `sweep_expired` batches per `claim_expired` page, one `UnitOfWork` per batch.

### PostgreSQL/SQLx

- Migration `*_sharing_*.sql` creates `shares(id uuid pk, tenant_id uuid not null references tenants(id) on delete restrict, target_kind text not null, target_id uuid not null, principal_kind text not null, principal_id uuid not null, role text not null, effect text not null default 'allow', expires_at timestamptz, version bigint not null default 1, created_by uuid not null references users(id) on delete restrict, created_at timestamptz not null default now(), updated_by uuid references users(id) on delete restrict, updated_at timestamptz)`, `share_links(id uuid pk, tenant_id uuid not null references tenants(id) on delete restrict, target_kind text not null, target_id uuid not null, role text not null, token_hash bytea not null, label text, expires_at timestamptz not null, max_uses int, use_count int not null default 0, revoked_at timestamptz, version bigint not null default 1, created_by uuid not null references users(id) on delete restrict, created_at timestamptz not null default now(), updated_by uuid references users(id) on delete restrict, updated_at timestamptz)`, `guest_invitations(id uuid pk, tenant_id uuid not null references tenants(id) on delete restrict, email citext not null, target_kind text not null, target_id uuid not null, role text not null, message text, token_hash bytea not null, expires_at timestamptz not null, accepted_at timestamptz, invited_by uuid not null references users(id) on delete restrict, created_at timestamptz not null default now())`, `guest_users(id uuid pk, tenant_id uuid not null references tenants(id) on delete restrict, user_id uuid not null references users(id) on delete restrict, email citext not null, display_name text not null, invited_by uuid references users(id) on delete restrict, created_at timestamptz not null default now(), deactivated_at timestamptz)`.
- Column shapes per decision section 2: this feature's schema carries no array column and no `jsonb` column — every enumerable set it needs is already a row (one `shares` row per grant, one `share_links` row per link) rather than a repeating group. `shares.role`, `shares.effect`, `share_links.role`, `guest_invitations.role`, `shares.target_kind`, `share_links.target_kind`, `guest_invitations.target_kind`, and `shares.principal_kind` are closed enums whose members carry no data and that a tenant cannot extend, so decision section 2's enum rule keeps them as `text` with the `check` constraints below; they are deliberately not lookup tables and must not be converted into any.
- Polymorphic references: `target_id` addresses one of seven target tables selected by `target_kind` (`workspace`, `folder`, `sheet`, `view`, `report`, `dashboard`, `document`), and `shares.principal_id` addresses `users` when `principal_kind` is `user` or `guest` and `groups` when it is `group`, so neither column can carry a single declared foreign key. Integrity is enforced instead by the `target_kind`/`principal_kind` `check` constraints, by `ShareRepository::insert` and `ShareLinkRepository::insert` resolving the referent in the same `UnitOfWork` transaction before the row is written and returning `ShareError::NotFound` when it is absent or in another tenant, by each target feature publishing its delete so the `sharing.sweep_expired` job's `claim_expired` pass also revokes grants whose target no longer resolves, and by the migration test `sharing_polymorphic_refs_have_no_orphans` asserting the reconciliation leaves no orphan grant. Every non-polymorphic reference above is declared, with `on delete restrict` so a tenant, inviter, or guest identity cannot be removed while a grant references it.
- Invariants: unique `shares(tenant_id, target_kind, target_id, principal_kind, principal_id)`; `check (target_kind in ('workspace','folder','sheet','view','report','dashboard','document','dynamic-view'))` on `shares` and `guest_invitations`, and the same list without `dynamic-view` on `share_links`, which is the enum line 314 promised and the reason a kind cannot enter the product by being written to a row; `check (role in ('owner','admin','editor','commenter','viewer','form_submitter'))`; `check (effect in ('allow','deny'))`; `check (principal_kind <> 'guest' or role in ('editor','commenter','viewer','form_submitter'))`; `check (share_links.role in ('viewer','commenter','form_submitter'))`; `check (share_links.expires_at <= created_at + interval '30 days')`; unique `share_links(token_hash)`; unique `guest_invitations(token_hash)`; unique `guest_users(tenant_id, email)`; the last-owner rule is unchanged and still enforced by a row lock on the target's owner grants inside the revoke transaction, taken by `ShareRepository::lock_owner_grants` and counted by `count_owners` within the same `UnitOfWork`.
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

## 7.1 Amendments

Every change made to this ticket after it was first accepted, newest first.

| Date | Caused by | What changed | Why |
|---|---|---|---|
| 2026-09-04 | F050 FR-F050-05 | `dynamic-view` added to `TargetRef.target_kind` for shares and invitations but not links; the `target_kind` check constraint that line 314 promised is now actually written in the invariants | F050 granted audiences through a share on a kind this ticket's enum did not contain, and no constraint would have caught it because the enum existed only in prose |

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
