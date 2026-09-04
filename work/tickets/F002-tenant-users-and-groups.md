---
id: F002
type: feature
status: planned
priority: P0
owner: platform
estimate: 5
target_milestone: M1
parent_epic: E001
depends_on: [F001]
blocks: [F038, F003, F037, F026, F033, F048]
conflicts_with: []
parallel_safe: true
owned_paths: [crates/persistence/src/tenants/**, crates/persistence/src/users/**, crates/domain/src/tenants/**, services/api/src/tenants/**, apps/web/src/features/tenants/**, services/api/migrations/*_tenants_*.sql, testing/features/F002/**]
feature_flag: F002_FEATURE
flag_default: off
branch: f002-tenant-users-and-groups
started_at: null
finished_at: null
---

# F002 — Tenant, users, and groups

## 1. Identity and dates

- Branch: `f002-tenant-users-and-groups`
- Capability area: enterprise security and administration (spec 5.8 SEC-01, SEC-02 tenant-isolation bullet, section 4 Tenant and User/Group entities, section 6 scale targets)
- Aggregate: `tenant`
- Module slug: `tenants`

### Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 9
- Canonical contract: `docs/capability-contracts.md` row F002

## 2. Requirement specification

### Problem and user outcome

Nothing in OpsHub can exist without a tenant that owns it and users who act inside it. Before login (F038) or authorization (F003) can be built, the platform needs the canonical `tenants`, `users`, `groups`, and `group_members` records, the admin routes that manage them, and the two-tenant fixture that every later feature uses to prove isolation.

As a tenant administrator, I want to manage my tenant's profile, invite and deactivate users, and organize them into groups, so that roles (F003) and identity providers (F026) have stable principals to bind to and no data can ever be read across tenant boundaries.

### Functional requirements

- **FR-F002-01:** A platform operator (bootstrap context with role `platform-operator`) can `POST /api/v1/tenants` with `{ name, slug, plan, region, admin_email, admin_display_name }`; the response is `201` with `TenantResponse` at `version` 1 and the initial user (status `active`, role binding `tenant-admin` written through the F003 seed hook) created in the same transaction.
- **FR-F002-02:** `slug` is 3–63 lowercase characters matching `^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$` and unique across all tenants; `plan` is one of `free|team|enterprise`; `region` accepts only `us-east` in this release (reserved field per spec section 10); violations return `400 invalid` with `field_errors.slug`, `field_errors.plan`, or `field_errors.region`, and a taken slug returns `409 conflict`.
- **FR-F002-03:** A `tenant-admin` can `GET /api/v1/tenants/{id}` for their own tenant and `PATCH /api/v1/tenants/{id}` with `If-Match` to change `name`, `plan` (operator only), and settings; settings are the columns of the tenant's one `tenant_settings` row (`default_locale`, `default_timezone`, `allow_guest_invites`, `operator_contact`) written in the same transaction and covered by the tenant `version`; a stale `If-Match` returns `409 conflict` with `current_version`; any other tenant id returns `404 not_found`.
- **FR-F002-04:** `POST /api/v1/tenants/{id}/suspend` (operator or tenant-admin) sets `status = suspended`, emits `tenant.suspended.v1`, and from that moment every `/api/v1` request for that tenant except `GET /api/v1/tenants/{id}` and `POST /auth/logout` returns `403 denied` with `code = denied` and `reason = tenant_suspended`; a repeated suspend is idempotent and returns the current version.
- **FR-F002-05:** `POST /api/v1/users` with `{ email, display_name, external_id? }` creates a user in status `invited` with `email` stored as `citext`, unique per tenant; duplicates return `409 conflict` with `field_errors.email = "taken"`; `display_name` is 1–120 characters; the user emits `user.created.v1`.
- **FR-F002-06:** `GET /api/v1/users` pages by opaque cursor with `limit` 1–200 (default 50), filters `status`, `email` prefix, `group_id`, and sorts by `display_name`, `email`, or `created_at`; deactivated users are included only when `filter=status:deactivated` is given.
- **FR-F002-07:** `PATCH /api/v1/users/{id}` with `If-Match` changes `display_name`, `external_id`, and `status` along the state machine `invited → active → suspended → active` and `* → deactivated` only through the deactivate route; an illegal transition returns `400 invalid` with `field_errors.status`; self-edits by a member are limited to `display_name`.
- **FR-F002-08:** `POST /api/v1/users/{id}/deactivate` (tenant-admin) sets `status = deactivated`, removes the user from all groups in the same transaction, calls the F038 `SessionRevoker` hook so every session and API token of the user is revoked, emits `user.deactivated.v1`, and is rejected with `409 conflict` reason `last_admin` when the target is the only active `tenant-admin`.
- **FR-F002-09:** `POST /api/v1/groups` with `{ name, description? }` creates a group with `name` unique per tenant (case-insensitive, 1–120 chars); `PATCH /api/v1/groups/{id}` renames or describes it with `If-Match`; both emit `group.updated.v1`.
- **FR-F002-10:** `PUT /api/v1/groups/{id}/members` with `{ user_ids: [...] }` replaces the full member set atomically; the set is capped at 5,000 ids, ids from another tenant or deactivated users return `400 invalid` with `field_errors.user_ids` listing the offending ids, and the emitted `group.updated.v1` carries `changed_fields = ["members"]` plus `added_user_ids` and `removed_user_ids`.
- **FR-F002-11:** Every mutation requires `Idempotency-Key`; the same key with the same body returns the stored response with no second write; the same key with a different body returns `409 conflict` with `reason = idempotency_mismatch`.
- **FR-F002-12:** Every mutation writes an audit row through `record_audit` (F003 writer, in-memory sink until F003 lands) and enqueues exactly one of `tenant.created.v1`, `tenant.updated.v1`, `tenant.suspended.v1`, `user.created.v1`, `user.updated.v1`, `user.deactivated.v1`, `group.updated.v1` in the same transaction.
- **FR-F002-13:** Any tenant, user, or group id from another tenant returns `404 not_found` on every route, including `PUT /groups/{id}/members`, so ids never reveal existence.
- **FR-F002-15:** `POST /api/v1/users/bulk` applies one action — `deactivate`, `reactivate`, `set_role`, `add_to_group`, `remove_from_group` — to at most 500 users in one audited transaction, returning a per-user result so a partial failure names which users and why rather than failing the whole request opaquely. It requires `tenant-admin`, `Idempotency-Key`, and a confirmation count that must equal the selection size, so a mis-click cannot deactivate a department. The last remaining tenant-admin can never be deactivated, in bulk or singly, and an attempt returns `409 conflict` with `reason: last_admin`, matching the single-user route, which FR-F002-08 also returns. Each affected user produces its own audit row and `user.updated.v1`, because an administrator later asking why someone lost access needs the individual record rather than a batch id.
- **FR-F002-14:** The web admin pages `/admin/tenant`, `/admin/users`, and `/admin/groups` let a tenant-admin edit tenant settings, invite, suspend, and deactivate users, and edit group membership; a member without `tenant-admin` sees the denied state on `/admin/*` and can only open their own profile card.

### Non-functional requirements

- **NFR-F002-01 Performance:** `GET /api/v1/users` with `limit=200` on a tenant of 100,000 users responds in under 500 ms p95; `PUT /groups/{id}/members` with 5,000 ids completes in under 800 ms p95; the design target is 10,000 tenants and 1,000,000 users (spec section 6).
- **NFR-F002-02 Security/privacy:** every query carries a `tenant_id` predicate bound from `ActorContext`, never from the request body; emails are stored as `citext` and never logged in full (logs show `a***@domain`); the cross-tenant negative suite in `testing/features/F002/api/` is reused by every later feature.
- **NFR-F002-03 Accessibility:** admin tables and dialogs pass axe with zero serious or critical violations, every row action is keyboard reachable, status changes are announced through a live region, and `prefers-reduced-motion` disables row transitions.
- **NFR-F002-04 Reliability/observability:** every request span carries `tenant_id`, `actor_id`, `correlation_id`; the metric `tenant_mutations_total{action}` counts each mutation; an outbox insert failure rolls back the whole write, so no user or group exists without its event.

### Scope

Included: tenant bootstrap, read, update, suspend; user invite, list, update, deactivate with the last-admin guard; group create, update, atomic membership replace; idempotency, optimistic concurrency, audit and outbox events; the admin UI pages; the shared two-tenant fixture and the cross-tenant negative suite.

Excluded: login and sessions (F038), roles and ACLs (F003), SAML/SCIM provisioning and ownership transfer (F026), locale preferences (F049), notification of invited users (F037), tenant export and purge (F027), entitlements (F048).

## 3. UX specification

- Entry points: avatar menu `Administration`; routes `/admin/tenant`, `/admin/users`, `/admin/groups`, `/admin/groups/{group_id}`; `Invite user` button on the users page; `Edit members` button on a group.
- Primary flow: tenant-admin opens `/admin/users`, clicks `Invite user`, enters email and display name, submits, the row appears with the `Invited` badge and version 1; opens `/admin/groups`, creates `Finance`, opens it, clicks `Edit members`, searches users by email prefix, toggles five users, saves; the member list refreshes and the toast shows `5 members added`.
- Loading: skeleton table rows; Empty: `No users yet` with the invite call to action; Error: inline banner with `correlation_id` and retry; Success: toast on invite, save, deactivate; Stale/conflict: banner `This record changed` with `Reload`; Offline: submit buttons disabled with an offline badge.
- Permission-denied: `/admin/*` renders the denied state with the reason text for members; a suspended tenant shows a full-page `Tenant suspended` notice with `tenant_settings.operator_contact`.
- Destructive actions: `Deactivate user` opens a confirm dialog that names the user and states that sessions and tokens are revoked; the last active admin sees the disabled button with the `last_admin` explanation.
- Responsive: tables collapse to cards under 768 px; the members editor becomes a full-screen sheet under 640 px.
- Keyboard: `Tab` order follows table order, `Enter` opens a row, `Space` toggles a member checkbox, `Escape` closes dialogs and returns focus to the trigger; focus ring uses the shared token.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide icons `Building2`, `Users`, `UserPlus`, `UserX`, `ShieldAlert`; tokens from `apps/web/src/design/tokens.css`.

- Design: `design/artboards/Admin.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

### Rust backend

- Domain entities in `crates/domain/src/tenants/`: `Tenant { id, name, slug: TenantSlug, plan: Plan, region: Region, status: TenantStatus, version, created_by, created_at, updated_by, updated_at, deleted_at }`, `TenantSettings { tenant_id, default_locale, default_timezone, allow_guest_invites, operator_contact, updated_by, updated_at }` loaded and saved with its tenant, `User { id, tenant_id, email: Email, display_name, status: UserStatus, external_id, last_login_at, version, audit fields, deleted_at }`, `Group { id, tenant_id, name, description, version, audit fields, deleted_at }`, `GroupMember { group_id, user_id, added_by, added_at }`.
- Data access (decision 2.1): `TenantRepository` (`tenants`, `tenant_settings`) and `GroupRepository` (`groups`, `group_members`) in `crates/persistence/src/tenants/`, and `UserRepository` (`users`) in `crates/persistence/src/users/`, the reference implementation F068 ships; each table is written by exactly one of them. The use cases below depend on those repository traits and the shared `UnitOfWork`; no handler, use case, or job in `crates/domain` or `services/api/src/tenants/` contains SQL, and the tenant predicate, soft-delete filter, version check, audit row, and outbox enqueue come from the base contract.
- Use cases: `create_tenant`, `get_tenant`, `update_tenant`, `suspend_tenant`, `create_user`, `list_users`, `update_user`, `deactivate_user`, `create_group`, `update_group`, `replace_group_members`, `list_groups`; state machine `UserStatus::transition(from, to) -> Result<(), TenantError>`.
- API endpoints (`services/api/src/tenants/`): `POST /api/v1/tenants`, `GET /api/v1/tenants/{id}`, `PATCH /api/v1/tenants/{id}`, `POST /api/v1/tenants/{id}/suspend`, `GET /api/v1/users`, `GET /api/v1/users/{id}`, `POST /api/v1/users`, `PATCH /api/v1/users/{id}`, `POST /api/v1/users/{id}/deactivate`, `GET /api/v1/groups`, `GET /api/v1/groups/{id}`, `POST /api/v1/groups`, `PATCH /api/v1/groups/{id}`, `PUT /api/v1/groups/{id}/members`. DTOs `CreateTenantRequest`, `UpdateTenantRequest`, `TenantResponse`, `CreateUserRequest`, `UpdateUserRequest`, `UserResponse`, `CreateGroupRequest`, `UpdateGroupRequest`, `ReplaceMembersRequest`, `GroupResponse`, `Page<UserResponse>`, `Page<GroupResponse>`.
- Events: `tenant.created.v1`, `tenant.updated.v1`, `tenant.suspended.v1`, `user.created.v1`, `user.updated.v1`, `user.deactivated.v1`, `group.updated.v1`, enqueued with `crates/events` `enqueue(tx, OutboxEvent)` carrying `changed_fields`.
- Authorization: `tenant-admin` for all mutations except tenant creation (`platform-operator`); `self` may `PATCH /users/{id}` `display_name`; reads of users and groups require an active membership in the tenant; a suspended tenant is checked by the `TenantGate` layer before routing.
- Hooks consumed: `SessionRevoker` trait (F038) with a no-op default; `record_audit` (F003) with an in-memory sink default; both are injected through `TenantsState`.
- Validation: slug regex and length, email RFC 5322 addr-spec ≤ 254 chars, display_name 1–120, group name 1–120, `user_ids` ≤ 5,000 and deduplicated, `limit` 1–200. Idempotency rows live in `idempotency_keys(tenant_id, key, request_hash, response, expires_at)` for 24 hours and are written by the shared `IdempotencyKeyRepository` of the base contract, not by this feature's repositories.
- Error mapping: `TenantError::SlugTaken | EmailTaken | NameTaken → 409 conflict`, `StaleVersion → 409 conflict`, `IllegalTransition | LastAdmin | ForeignMember → 400 invalid`, `NotFound → 404 not_found`, `AuthzError::Denied → 403 denied`, `Suspended → 403 denied reason tenant_suspended`.

### Interface

Exact shapes. Every field lists its JSON name, type, whether it is required, and the constraint that
makes it invalid. `T?` is nullable, and a missing optional field and an explicit `null` mean the same
thing. Timestamps are RFC 3339 UTC, ids are UUIDv7 strings, and `version` increments by one per
write. Unlisted fields are rejected with `400 invalid` and `field_errors.<name>` naming them. These
three response types — `TenantResponse`, `UserResponse`, `GroupResponse` — are the principal shapes
every later feature embeds; they are defined here once and referenced elsewhere by name and owner.

**`CreateTenantRequest`** — `POST /api/v1/tenants`, `platform-operator` only

| Field | Type | Required | Constraint |
|---|---|---|---|
| `name` | string | yes | 1–200 chars after trim |
| `slug` | string | yes | 3–63 chars, `^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$`, unique across all tenants; taken → `409 conflict` (FR-F002-02) |
| `plan` | string | yes | `free` \| `team` \| `enterprise` |
| `region` | string | no | `us-east` only in this release; anything else → `400 invalid` with `field_errors.region`. Defaults to `us-east` |
| `admin_email` | string | yes | RFC 5322 addr-spec, ≤ 254 chars; becomes the first user |
| `admin_display_name` | string | yes | 1–120 chars |

**`UpdateTenantRequest`** — `PATCH /api/v1/tenants/{id}`, all fields optional, at least one present, `If-Match` required

| Field | Type | Required | Constraint |
|---|---|---|---|
| `name` | string | no | as above |
| `plan` | string | no | `platform-operator` only; a `tenant-admin` sending it gets `403 denied` (FR-F002-03) |
| `settings` | TenantSettings | no | replaced whole, not merged; written in the tenant's transaction under the tenant `version` |

**`TenantSettings`** — the tenant's one `tenant_settings` row, never a free-form object

| Field | Type | Required | Default | Constraint |
|---|---|---|---|---|
| `default_locale` | string | no | `en-US` | `^[a-z]{2}(-[A-Z]{2})?$` |
| `default_timezone` | string | no | `UTC` | IANA zone name |
| `allow_guest_invites` | bool | no | `false` | |
| `operator_contact` | string? | no | null | ≤ 320 chars; shown on the suspended-tenant notice |

**`TenantResponse`**

| Field | Type | Notes |
|---|---|---|
| `id` | uuid | |
| `name` | string | |
| `slug` | string | |
| `plan` | string | administrative field; present only for `tenant-admin` and `platform-operator` |
| `region` | string | administrative field; same condition as `plan` |
| `status` | string | `active` \| `suspended`; always present, because FR-F002-04 keeps this route readable while suspended |
| `settings` | TenantSettings | always present, defaults materialised. For a caller who is neither `tenant-admin` nor `platform-operator` it carries only `default_locale`, `default_timezone` and `operator_contact`; `allow_guest_invites` is omitted |
| `version` | integer | pass as `If-Match` on the next write |
| `created_at` / `updated_at` | timestamp | administrative fields; omitted for a non-admin caller |
| `created_by` / `updated_by` | uuid | administrative fields; omitted for a non-admin caller |
| `deleted_at` | timestamp? | tenants are not deletable in this release; the field exists and is always null |

`POST /api/v1/tenants/{id}/suspend` takes no body, requires `Idempotency-Key`, and returns
`TenantResponse` with `status = "suspended"`; a repeat returns the current version unchanged.

**`CreateUserRequest`** — `POST /api/v1/users`

| Field | Type | Required | Constraint |
|---|---|---|---|
| `email` | string | yes | RFC 5322 addr-spec ≤ 254 chars, unique per tenant case-insensitively; taken → `409 conflict` with `field_errors.email = "taken"` |
| `display_name` | string | yes | 1–120 chars after trim |
| `external_id` | string? | no | ≤ 255 chars; the identity provider's subject, set by F026 later |

**`UpdateUserRequest`** — `PATCH /api/v1/users/{id}`, all optional, at least one present, `If-Match` required

| Field | Type | Required | Constraint |
|---|---|---|---|
| `display_name` | string | no | 1–120 chars; the only field a member may change on their own record |
| `external_id` | string? | no | `tenant-admin` only; explicit null clears it |
| `status` | string | no | `tenant-admin` only; `invited` → `active` → `suspended` → `active` only. `deactivated` is never reachable here (FR-F002-07); an illegal pair → `400 invalid` with `field_errors.status` |

**`UserResponse`** — the principal shape every feature that names a user embeds

| Field | Type | Notes |
|---|---|---|
| `id` | uuid | |
| `display_name` | string | |
| `status` | string | `invited` \| `active` \| `suspended` \| `deactivated` |
| `email` | string | present for `tenant-admin` and for the user's own record only; other members reading the tenant directory receive the record without it (FR-F002-14) |
| `external_id` | string? | same condition as `email` |
| `last_login_at` | timestamp? | same condition as `email`; null until F038 records a login |
| `version` | integer | |
| `created_at` / `updated_at` | timestamp | |
| `created_by` / `updated_by` | uuid | |
| `deleted_at` | timestamp? | present only when a soft-deleted user is read |

`POST /api/v1/users/{id}/deactivate` takes no body and returns `UserResponse` with
`status = "deactivated"`. `POST /api/v1/users/bulk` takes
`{ action: "deactivate" | "reactivate" | "set_role" | "add_to_group" | "remove_from_group",
user_ids: uuid[], confirm_count: integer, role?: string, group_id?: uuid }` — `user_ids` 1–500 and
deduplicated, `confirm_count` must equal `user_ids.length` or the request is `400 invalid`, `role` is
required for `set_role` and must be defined in `docs/authorization-model.md`, `group_id` is required
for the two group actions — and returns
`{ results: [{ user_id, outcome: "applied" | "skipped" | "failed", code? }] }` where `code` is one of
the six shared error codes and identifies why that one user was not changed (FR-F002-15).

**`CreateGroupRequest`** `{ name, description? }` — `name` 1–120 chars, unique per tenant
case-insensitively (`409 conflict` with `field_errors.name = "taken"`), `description` ≤ 2,000 chars.
**`UpdateGroupRequest`** carries the same two fields, both optional, at least one present.
**`ReplaceMembersRequest`** — `PUT /api/v1/groups/{id}/members` — `{ user_ids: uuid[] }`, the complete
set: 0–5,000 ids, deduplicated, every id an existing non-`deactivated` user of the same tenant; any
offender returns `400 invalid` with `field_errors.user_ids` listing the offending ids, and 5,001 ids
returns `400 invalid` before any row is touched. F005's `ReplaceMembersRequest` is a different type
in a different module (workspace membership, with roles); these two never mix.

**`GroupResponse`**

| Field | Type | Notes |
|---|---|---|
| `id` | uuid | |
| `name` | string | |
| `description` | string? | |
| `member_count` | integer | live members; the member list itself is read through `GET /api/v1/users` filtered by `group_id`, since a group has no member-read route |
| `version` | integer | |
| `created_at` / `updated_at` | timestamp | |
| `created_by` / `updated_by` | uuid | |
| `deleted_at` | timestamp? | present only when a soft-deleted group is read |

`PUT /api/v1/groups/{id}/members` returns the group's `GroupResponse` at its new `version` together
with `{ added_user_ids, removed_user_ids }`, the same two lists the `group.updated.v1` payload
carries, so the client can render the toast without a second read.

**List routes.** `GET /api/v1/users` and `GET /api/v1/groups` return `Page<T>`, the envelope F028
owns: `{ items: T[], next_cursor: string?, has_more: bool, total: integer? }`, with `total` present
only when the caller passes `include_total=true`. Query parameters are F028's `ListQuery`: `cursor`
(opaque, signed), `limit` (1–200, default 50), `filter`, `sort`, `fields`. For users the filterable
fields are `status` (one of the four values), `email` (prefix match), and `group_id` (equality), and
the sort keys are `display_name`, `email` and `created_at`, default `display_name` ascending;
`deactivated` users appear only when `status` is filtered to them (FR-F002-06). For groups the
filterable field is `name` (prefix) and the sort keys are `name` and `updated_at`, default `name`.

**Status codes.** Errors are the shared six with the body decision 3 fixes:
`{ code, message, field_errors, correlation_id }`.

| Status | Code | Produced by |
|---|---|---|
| 400 | `invalid` | field validation, illegal status transition, foreign or deactivated member id, over-length member set, `last_admin` on the single-user deactivate route, `confirm_count` mismatch |
| 401 | `denied` | no session or bearer token on an `/api/v1` route (F038 extractor) |
| 403 | `denied` | member calling an administrative route; `tenant-admin` sending `plan`; any write while the tenant is `suspended`, with `reason = tenant_suspended` |
| 404 | `not_found` | unknown id, and every id belonging to another tenant, on every route including `PUT /api/v1/groups/{id}/members` (FR-F002-13) |
| 409 | `conflict` | taken `slug`, `email` or group `name`; stale `If-Match` with `current_version` in the body; `Idempotency-Key` replayed with a different body (`reason = idempotency_mismatch`); `last_admin` on the bulk route |
| 429 | `rate_limited` | F038 rate-limit buckets; this feature declares no bucket of its own |
| 503 | `unavailable` | database or outbox unreachable; no partial write is ever visible |

### Use case signatures

In `crates/domain/src/tenants/`. `ctx` is the `ActorContext` F038 defines and the `crates/auth`
extractor builds; until F038 lands the harness constructs it directly, which is why the tenant
predicate is read from `ctx` and never from a request body (NFR-F002-02). `DomainError` is the shared
error whose mapping to the six codes is the table above.

```rust
fn create_tenant(ctx: &ActorContext, uow: &mut UnitOfWork, req: CreateTenant) -> Result<Tenant, DomainError>;
fn get_tenant(ctx: &ActorContext, repo: &dyn TenantRepository, id: TenantId) -> Result<Tenant, DomainError>;
fn update_tenant(ctx: &ActorContext, uow: &mut UnitOfWork, id: TenantId, expected: Version, req: UpdateTenant) -> Result<Tenant, DomainError>;
fn suspend_tenant(ctx: &ActorContext, uow: &mut UnitOfWork, id: TenantId) -> Result<Tenant, DomainError>;
fn create_user(ctx: &ActorContext, uow: &mut UnitOfWork, req: CreateUser) -> Result<User, DomainError>;
fn list_users(ctx: &ActorContext, repo: &dyn UserRepository, filter: UserFilter, page: Cursor) -> Result<Page<User>, DomainError>;
fn update_user(ctx: &ActorContext, uow: &mut UnitOfWork, id: UserId, expected: Version, req: UpdateUser) -> Result<User, DomainError>;
fn deactivate_user(ctx: &ActorContext, uow: &mut UnitOfWork, id: UserId, expected: Version) -> Result<User, DomainError>;
fn bulk_user_action(ctx: &ActorContext, uow: &mut UnitOfWork, req: BulkUserAction) -> Result<Vec<BulkUserOutcome>, DomainError>;
fn create_group(ctx: &ActorContext, uow: &mut UnitOfWork, req: CreateGroup) -> Result<Group, DomainError>;
fn update_group(ctx: &ActorContext, uow: &mut UnitOfWork, id: GroupId, expected: Version, req: UpdateGroup) -> Result<Group, DomainError>;
fn list_groups(ctx: &ActorContext, repo: &dyn GroupRepository, filter: GroupFilter, page: Cursor) -> Result<Page<Group>, DomainError>;
fn replace_group_members(ctx: &ActorContext, uow: &mut UnitOfWork, id: GroupId, expected: Version, req: ReplaceMembers) -> Result<MemberDiff, DomainError>;
impl UserStatus { fn transition(from: UserStatus, to: UserStatus) -> Result<(), TenantError>; }
```

A use case never takes a pool or a connection and never returns a database row type. The request
structs are the DTOs above after deserialization and validation; the returned types are the domain
entities of the Rust backend section.

**Transaction boundaries.** Each of these runs inside exactly one `UnitOfWork`, and the audit row and
the outbox row are written by that same unit, so no event can exist without its write:

- `create_tenant`: `tenants` + its trigger-created `tenant_settings` row + the first `users` row + the
  F003 seed hook's role binding. The boundary protects the invariant that a tenant is never
  reachable without an administrator who can unsuspend or repair it.
- `update_tenant`: `tenants` and `tenant_settings` under one `If-Match` on the tenant `version`, so a
  settings change and a rename cannot interleave into a half-applied record (FR-F002-03).
- `deactivate_user`: the `users` status change, the removal from every `group_members` row, and the
  F038 `SessionRevoker` call. The boundary protects the invariant that a deactivated user never
  retains group-derived access; the last-admin guard takes `SELECT ... FOR UPDATE` on the tenant row
  inside the same unit so two concurrent deactivations cannot remove both administrators.
- `replace_group_members`: one `DELETE` plus one bulk `INSERT` on `group_members`. The set is
  replaced atomically, so no reader ever sees a partially applied membership.
- `bulk_user_action`: all ≤ 500 users in one unit with one audit row per user, so a partial failure
  reports per user and commits nothing (FR-F002-15).

### PostgreSQL/SQLx

- Migration `*_tenants_*.sql` creates extension `citext` and tables: `tenants(id uuid pk, name text not null, slug text not null, plan text not null, region text not null default 'us-east', status text not null default 'active', version bigint not null default 1, created_by uuid, created_at timestamptz, updated_by uuid, updated_at timestamptz, deleted_at timestamptz)`; `tenant_settings(tenant_id uuid primary key references tenants(id) on delete cascade, default_locale text not null default 'en-US', default_timezone text not null default 'UTC', allow_guest_invites bool not null default false, operator_contact text, updated_by uuid, updated_at timestamptz not null)` — one typed row per tenant instead of a `jsonb` blob, because every setting is read and constrained by the product (F049 locale, F062 brand surface, the suspended-tenant notice); `users(id uuid pk, tenant_id uuid not null references tenants(id), email citext not null, display_name text not null, status text not null default 'invited', external_id text, last_login_at timestamptz, version bigint not null default 1, audit columns, deleted_at)`; `groups(id uuid pk, tenant_id uuid not null, name text not null, description text, version, audit columns, deleted_at)`; `group_members(tenant_id uuid not null, group_id uuid references groups(id) on delete cascade, user_id uuid references users(id) on delete restrict, added_by uuid, added_at timestamptz, primary key (group_id, user_id))`.
- Invariants: unique index `tenants_slug_idx on (slug) where deleted_at is null`; `users_tenant_email_idx on (tenant_id, email) where deleted_at is null`; `groups_tenant_lower_name_idx on (tenant_id, lower(name)) where deleted_at is null`; check constraints on `plan in ('free','team','enterprise')`, `status` enums, `region = 'us-east'`, and `tenant_settings.default_locale ~ '^[a-z]{2}(-[A-Z]{2})?$'`; a trigger on `tenants` insert creates the tenant's `tenant_settings` row with defaults, so a tenant always has exactly one; trigger `group_members_same_tenant` rejects a member whose `users.tenant_id` differs from `groups.tenant_id`.
- Indexes: `users(tenant_id, status, display_name)`, `users(tenant_id, created_at desc)`, `group_members(tenant_id, user_id)`, `groups(tenant_id, updated_at desc)`; `tenant_settings` needs none beyond its primary key because it is only ever read by `tenant_id`.
- Audit actions: `tenant.create`, `tenant.update`, `tenant.suspend`, `user.create`, `user.update`, `user.deactivate`, `group.create`, `group.update`, `group.members.replace` with field-level diffs (membership diff lists added and removed ids).
- Retention/deletion: users and groups soft-delete through `deleted_at` only via the F027 purge job; tenants are never hard-deleted in this release; rollback drops the five tables and the `citext` extension if no other table uses it.

### React/TypeScript

- Routes in `apps/web/src/features/tenants/`: `/admin/tenant`, `/admin/users`, `/admin/groups`, `/admin/groups/$groupId`; components `TenantSettingsPage`, `TenantSettingsForm`, `SuspendTenantDialog`, `UsersPage`, `UsersTable`, `InviteUserDialog`, `DeactivateUserDialog`, `GroupsPage`, `GroupDetailPage`, `GroupMembersEditor`, `UserStatusBadge`.
- State: TanStack Query keys `['tenant', id]`, `['users', filter, cursor]`, `['groups', cursor]`, `['group', id]`, `['group-members', id]`; mutations invalidate by key and store the returned `version`.
- API client: generated `TenantsApi` with `getTenant`, `updateTenant`, `suspendTenant`, `listUsers`, `createUser`, `updateUser`, `deactivateUser`, `listGroups`, `createGroup`, `updateGroup`, `replaceGroupMembers`.
- Optimistic updates: membership toggles apply locally and roll back on `invalid` or `conflict` with the stale banner naming the changed field.
- Telemetry: `tenant_settings_saved`, `user_invited`, `user_deactivated`, `group_created`, `group_members_replaced` with `tenant_id` and counts.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F002-01 through FR-F002-14 in `testing/features/F002/requirements/cases.md`
- [ ] Failure/edge-case tests: taken slug, invalid region, illegal status transition, last-admin deactivation, 5,001 member ids, foreign member id, idempotency mismatch
- [ ] Permission-negative and tenant-isolation tests: member creating a user, member suspending the tenant, tenant-B admin reading tenant-A user and group, suspended tenant calling a write route
- [ ] Rust unit tests: `crates/domain/src/tenants/` slug parsing, status machine, member diff computation, error mapping
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: slug and email unique indexes, same-tenant member trigger, cascade and restrict behaviour, rollback
- [ ] React component tests: `UsersTable`, `InviteUserDialog`, `GroupMembersEditor`, `TenantSettingsForm` states
- [ ] Browser E2E tests: invite user, create group, edit members, deactivate user, suspended-tenant notice
- [ ] Accessibility tests: axe on the three admin pages, keyboard member toggling, live-region announcements
- [ ] Performance/load tests: 100,000-user list p95 under 500 ms, 5,000-member replace p95 under 800 ms

### Fast fanout configuration

- Test harness path: `testing/features/F002/`
- Feature flag: `F002_FEATURE`
- Fixture/seed factory: `testing/fixtures/tenants.rs` builds tenants A and B, one tenant-admin, two members, one invited and one deactivated user, and three groups per tenant
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC, emails under `example.test`
- Mock/stub contracts: in-memory outbox recorder; `SessionRevoker` and audit sink recorded in memory
- Parallel isolation: one schema per test worker, tenant ids per test
- Targeted command: `cargo xtask test-feature F002`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F002/`

## 6. Acceptance criteria

```gherkin
Feature: Tenants, users, and groups

Scenario: Bootstrap a tenant with its first admin
  Given a platform operator context
  When they create tenant "Acme" with slug "acme" and admin_email "ops@acme.test"
  Then the tenant has version 1 and status active
  And the user "ops@acme.test" is active with a tenant-admin binding
  And tenant.created.v1 and user.created.v1 are in the outbox

Scenario: Replace group members atomically
  Given group "Finance" in tenant "acme" with 3 members
  When the tenant-admin PUTs a member set containing 2 existing and 4 new user ids
  Then the group has exactly 6 members
  And group.updated.v1 lists 4 added_user_ids and 1 removed_user_ids

Scenario: Member cannot administer the tenant
  Given a member without the tenant-admin role
  When they POST /api/v1/users or POST /api/v1/tenants/{id}/suspend
  Then the response is 403 denied and no row or event is written

Scenario: Cross-tenant read does not leak
  Given a user in tenant "acme"
  When a tenant-admin of tenant "globex" requests that user by id
  Then the response is 404 not_found

Scenario: Deactivation revokes access
  Given an active member with two sessions
  When the tenant-admin deactivates the member
  Then the member is removed from every group, both sessions are revoked, and user.deactivated.v1 is published
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F001 (workspace, CI, migrations runner); decisions sections 2–4; contracts row F002
- Blocks: F038, F003, F037, F026, F033, F048
- Conflicts with: none (disjoint owned paths)
- External dependencies: PostgreSQL `citext` extension available in the CI image
- Risks and mitigations: `record_audit` and `SessionRevoker` are implemented by F003 and F038, which depend on this feature, so both are consumed through traits with in-memory defaults and replaced by real implementations behind their own flags; the atomic 5,000-member replace is a single `DELETE` plus bulk `INSERT` inside one transaction to avoid lock escalation; the `last_admin` guard uses `SELECT ... FOR UPDATE` on the tenant row to prevent two concurrent deactivations removing both admins.
- Open questions: none

## 7.1 Amendments

Every change made to this ticket after it was first accepted, newest first.

| Date | Caused by | What changed | Why |
|---|---|---|---|
| 2026-09-04 | F002 interface work | `GET /api/v1/groups/{id}` and `POST /api/v1/users/bulk` declared in the catalog and reproduced here | The group detail page and FR-F002-15 both required routes no row declared; the catalog moves first |
| 2026-09-04 | F002 interface work | FR-F002-08 last-admin changed from `400 invalid` to `409 conflict` | One invariant returned two status codes; FR-F002-15 already used 409 and conflict is the correct class |

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F001 accepted and archived; `sqlx migrate run` works in CI
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F002/`
- [ ] Migration file name and owned paths claimed
- [ ] `testing/harness/db.rs` schema-per-worker helper available

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit rows and outbox events verified for every mutation
- [ ] `testing/fixtures/tenants.rs` published and consumed by the F038 harness
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F002_FEATURE`, run down migration on an empty database
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Platform operators can bootstrap tenants; tenant administrators can manage users and groups from `/admin`.
- Migration adds `citext`, `tenants`, `tenant_settings`, `users`, `groups`, and `group_members`; rollback drops them. Feature is off by default behind `F002_FEATURE`.
