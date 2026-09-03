---
id: F003
type: feature
status: planned
priority: P0
owner: platform
estimate: 8
target_milestone: M1
parent_epic: E001
depends_on: [F002, F038]
blocks: [F005, F016, F036, F021, F027, F028, F048]
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/authz/**, services/api/src/authz/**, apps/web/src/features/authz/**, services/api/migrations/*_authz_*.sql, testing/features/F003/**]
feature_flag: F003_FEATURE
flag_default: off
branch: f003-authorization-and-audit
started_at: null
finished_at: null
---

# F003 — Authorization and audit

## 1. Identity and dates

- Branch: `f003-authorization-and-audit`
- Capability area: enterprise security and administration (spec 5.8 SEC-01, SEC-03; low-level bullets on tenant isolation testing and append-only audit; 5.4b roles bullet and external-user bullet; section 4 AuditEvent entity)
- Aggregate: `authorization`
- Module slug: `authz`

### Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 9
- Canonical contract: `docs/capability-contracts.md` row F003

## 2. Requirement specification

### Problem and user outcome

Every later feature must answer "may this actor do this to that resource" and "who changed what, when" without inventing its own rules. This feature provides the deny-by-default policy engine over roles, role bindings, and resource ACLs with downward inheritance and explicit denies, the `RequirePermission` middleware every handler uses, and the append-only `audit_events` table with its query API.

As a tenant administrator, I want to define roles, bind them to users and groups at tenant, workspace, folder, or resource scope, restrict a resource with an explicit deny, and read a complete audit trail with correlation ids, so that access is least-privilege and every change is attributable. As a resource owner, I want to manage the ACL of my own resource and see its history.

### Functional requirements

- **FR-F003-01:** The migration seeds system roles `tenant-admin`, `owner`, `admin`, `editor`, `commenter`, `viewer`, and `form-submitter` per tenant with fixed permission sets (for example `viewer = [*:read]`, `commenter = viewer + [comment:create]`, `editor = commenter + [*:edit, *:create]`, `admin = editor + [acl:manage, *:delete]`, `owner = admin + [*:transfer]`, `tenant-admin = [*]`); system roles have `is_system = true` and cannot be deleted or have their slug changed.
- **FR-F003-02:** `GET /api/v1/roles` lists roles with cursor paging; `POST /api/v1/roles` (tenant-admin) creates a custom role with `slug` (3–40 chars, kebab, unique per tenant), `name`, and `permissions` drawn from the `Permission` catalogue; `PATCH /api/v1/roles/{id}` with `If-Match` changes `name` and `permissions` and emits `role.updated.v1`; unknown permission strings return `400 invalid` with `field_errors.permissions`.
- **FR-F003-03:** A role binding attaches a role to a `user` or `group` principal at a scope of kind `tenant|workspace|folder|sheet|report|dashboard|document` and is managed through the ACL routes (bindings are ACL entries with `effect = allow` referencing a role); at most 500 entries per resource.
- **FR-F003-04:** `GET /api/v1/resources/{kind}/{id}/acl` returns the effective ACL for a resource: direct entries, inherited entries with `inherited_from { kind, id }`, and the resolved permission set for the caller; `PUT /api/v1/resources/{kind}/{id}/acl` (resource-owner or tenant-admin) replaces the direct entries atomically with `If-Match` and emits `acl.updated.v1` with `added`, `removed`, and `changed` entries.
- **FR-F003-05:** Evaluation order for `check(principal, permission, resource)` is: tenant suspended → `denied`; explicit `deny` entry on the resource or any ancestor matching the principal or one of its groups → `denied`; `allow` entry (direct or inherited) or role binding at the resource scope or any ancestor granting the permission → `allowed`; otherwise `denied`; the result carries `decision`, `reason` (`suspended|explicit_deny|allow_entry|role_binding|no_match`), and `matched_rule { entry_id, scope }`.
- **FR-F003-06:** Guest principals (users whose `auth_kind` context marks them as guests, defined by F036) never match tenant-scoped bindings; only entries naming the guest directly or a group the guest belongs to apply.
- **FR-F003-07:** `POST /api/v1/authz/check` with `{ permission, resource: { kind, id }, principal? }` returns the evaluation result for the caller, or for another principal when the caller is tenant-admin; a non-admin passing `principal` receives `403 denied`.
- **FR-F003-08:** `authz::require(&ctx, Permission, ResourceRef) -> Result<(), AuthzError>` and the Axum extractor `RequirePermission<P>` are the only entry points for handlers; a missing `*:read` on the resource maps to `404 not_found`, a present read but missing mutate permission maps to `403 denied`, and the decision is cached per request and for 30 seconds across requests keyed by `(principal, resource, permission)`, invalidated by `acl.updated.v1` and `role.updated.v1`.
- **FR-F003-09:** `record_audit(tx, AuditEvent)` inserts an `audit_events` row inside the caller's transaction with `actor_id`, `actor_kind` (`user|api_token|system`), `action`, `resource_kind`, `resource_id`, `before`, `after`, `diff`, `ip`, `user_agent`, `correlation_id`, `occurred_at`, and enqueues `audit.recorded.v1`; the F038 `AuthAuditSink` gains a database implementation that calls it.
- **FR-F003-10:** `audit_events` is append-only: a trigger raises `audit_immutable` on `UPDATE` or `DELETE`, the table is partitioned monthly by `occurred_at`, and partitions for the next three months are created by the migration and by a monthly worker job.
- **FR-F003-11:** `GET /api/v1/audit-events` pages by cursor (newest first, `limit` ≤ 200) with filters `actor_id`, `resource_kind`, `resource_id`, `action` prefix, `correlation_id`, `occurred_from`, `occurred_to`; tenant-admin reads everything in the tenant, a resource-owner reads rows for resources they own, everyone else receives `403 denied`.
- **FR-F003-12:** Every role and ACL mutation writes an audit row with the entry-level diff and requires `Idempotency-Key` and `If-Match` per the contract conventions; replays return the stored response.
- **FR-F003-13:** Any role, resource, or audit row id from another tenant returns `404 not_found`, and an audit query for another tenant's `resource_id` returns an empty page.
- **FR-F003-14:** The web app provides `/admin/roles` with a permission matrix editor, a reusable `AclEditor` drawer that later features mount on their resources, and `/admin/audit` with filters, a before/after diff viewer, and a copy-correlation-id action; members see the denied state on `/admin/*`, and a resource owner sees the audit tab scoped to their resource.

### Non-functional requirements

- **NFR-F003-01 Performance:** a cached `check` completes in under 5 ms p95 and an uncached check over a 4-level ancestry in under 30 ms p95; `record_audit` adds under 10 ms p95 to a mutation; `GET /api/v1/audit-events` over 10,000,000 rows responds in under 500 ms p95 through partition pruning and the `(tenant_id, occurred_at desc)` index.
- **NFR-F003-02 Security/privacy:** deny by default with explicit deny winning; the negative matrix covers cross-tenant, role, guest, and field-level cases for every route; `before`/`after` payloads redact fields tagged `#[audit(redact)]` (secrets, tokens, emails of third parties) before insert.
- **NFR-F003-03 Accessibility:** the permission matrix is a real `<table>` with row and column headers, checkboxes carry `aria-label` `{role} can {permission}`, the diff viewer exposes additions and removals as text, and all admin pages pass axe with zero serious violations.
- **NFR-F003-04 Reliability/observability:** metrics `authz_checks_total{decision,reason}`, `authz_cache_hit_ratio`, `audit_events_written_total`, `audit_write_failures_total`; a failed audit insert fails the whole mutation (no silent loss); every span carries `tenant_id`, `actor_id`, `correlation_id`, `resource_kind`.

### Scope

Included: system and custom roles, role bindings as ACL entries, resource ACL read and replace with inheritance and explicit deny, the policy engine and its caches, the `require` function and `RequirePermission` extractor, the check endpoint, the append-only partitioned audit table, the audit writer and query API, the database `AuthAuditSink`, the roles, ACL, and audit UI, and the reusable negative matrix.

Excluded: workspace and folder records themselves (F005), sharing grants, guests, and links (F036), audit export and retention (F027), entitlement checks (F048), field-level visibility rules for dynamic views (F050).

## 3. UX specification

- Entry points: admin menu `Roles` → `/admin/roles`, `Audit log` → `/admin/audit`; the `Share` or `Permissions` button on any resource opens `AclEditor`; a resource's `History` tab opens `/admin/audit?resource_kind=sheet&resource_id={id}`.
- Primary flow: tenant-admin opens `/admin/roles`, clicks `New role`, names it `Reviewer`, ticks `sheet:read`, `comment:create`, `approval:decide`, saves; opens a sheet, clicks `Permissions`, adds group `QA` with role `Reviewer` and adds an explicit deny for guest `ext@partner.test`, saves; opens `/admin/audit`, filters by the sheet, sees `acl.update` with the entry diff and copies the correlation id.
- Loading: skeleton matrix and table; Empty: `No custom roles yet`, `No audit events match`; Error: banner with `correlation_id` and retry; Success: toast on save; Stale/conflict: banner `Permissions changed` with `Reload` and the entry diff; Offline: save disabled with the offline badge.
- Permission-denied: members see the denied state on `/admin/roles` and `/admin/audit`; a resource `AclEditor` opened without `acl:manage` is read-only with an explanation; system roles show a lock icon and disabled slug field.
- Destructive actions: removing an ACL entry or adding a deny shows a confirm that names the principal; deleting a custom role that still has bindings is blocked with the count of bindings.
- Responsive: the matrix scrolls horizontally with the role column frozen under 768 px; `AclEditor` becomes a full-screen sheet under 640 px.
- Keyboard: arrow keys move through matrix cells, `Space` toggles, `Enter` saves, `Escape` closes the drawer and returns focus; the diff viewer is navigable with `Tab` between changed fields.
- Font/icon/design tokens: Inter variable; Lucide icons `ShieldCheck`, `Lock`, `UserCheck`, `Ban`, `History`, `Copy`; tokens from `apps/web/src/design/tokens.css`.

## 4. Technical specification

### Rust backend

- Domain entities in `crates/domain/src/authz/`: `Role { id, tenant_id, slug, name, permissions: Vec<Permission>, is_system, version, audit fields }`, `RoleBinding { id, tenant_id, role_id, principal: Principal, scope: ResourceRef, created_by, created_at }`, `AclEntry { id, tenant_id, resource: ResourceRef, principal: Principal, effect: Effect, permissions: Vec<Permission>, role_id: Option<RoleId>, inherited_from: Option<ResourceRef>, version }`, `Principal { kind: User|Group, id }`, `ResourceRef { kind: ResourceKind, id }`, `Permission` (`<resource>:<verb>` with wildcard resource), `Decision { decision, reason, matched_rule }`, `AuditEvent { actor_id, actor_kind, action, resource, before, after, diff, ip, user_agent, correlation_id, occurred_at }`.
- Use cases: `list_roles`, `create_role`, `update_role`, `get_effective_acl`, `replace_acl`, `check`, `require`, `record_audit`, `list_audit_events`; `AncestryResolver` trait (F005 and later features register resolvers per `ResourceKind`; the tenant resolver is built in) and `GroupMembershipSource` reading `group_members`.
- API endpoints (`services/api/src/authz/`): `GET /api/v1/roles`, `POST /api/v1/roles`, `PATCH /api/v1/roles/{id}`, `GET /api/v1/resources/{kind}/{id}/acl`, `PUT /api/v1/resources/{kind}/{id}/acl`, `POST /api/v1/authz/check`, `GET /api/v1/audit-events`. DTOs `RoleResponse`, `CreateRoleRequest`, `UpdateRoleRequest`, `AclEntryDto`, `EffectiveAclResponse { entries, inherited, caller_permissions, version }`, `ReplaceAclRequest { entries }`, `CheckRequest`, `CheckResponse`, `AuditEventResponse`, `Page<AuditEventResponse>`.
- Events: `role.updated.v1`, `acl.updated.v1`, `audit.recorded.v1` through the outbox; the API keeps a subscriber that invalidates the decision cache on the first two.
- Authorization: `tenant-admin` for roles and cross-principal checks; `acl:manage` on the resource (owner or admin roles) for ACL replace; `audit:read` at tenant scope or ownership of the resource for audit reads; `RequirePermission` is applied to every F003 route itself.
- Validation: slug regex, `permissions` ≤ 64 entries from the catalogue, ACL ≤ 500 entries, no duplicate `(principal, effect)` pairs, `limit` ≤ 200, `occurred_from ≤ occurred_to`.
- Error mapping: `AuthzError::Denied → 403 denied`, `AuthzError::Hidden → 404 not_found`, `RoleError::SlugTaken | StaleVersion → 409 conflict`, `UnknownPermission | TooManyEntries | SystemRoleImmutable | RoleInUse → 400 invalid`, `NotFound → 404 not_found`.

### PostgreSQL/SQLx

- Migration `*_authz_*.sql` creates `roles(id uuid pk, tenant_id uuid not null references tenants(id), slug text not null, name text not null, permissions text[] not null, is_system bool not null default false, version bigint not null default 1, created_by, created_at, updated_by, updated_at, deleted_at)`; `role_bindings(id uuid pk, tenant_id, role_id references roles(id), principal_kind text check (principal_kind in ('user','group')), principal_id uuid not null, scope_kind text not null, scope_id uuid not null, created_by, created_at)`; `resource_acls(id uuid pk, tenant_id, resource_kind text not null, resource_id uuid not null, principal_kind, principal_id, effect text check (effect in ('allow','deny')), permissions text[] not null, role_id uuid, version bigint not null default 1, created_by, created_at, updated_by, updated_at)`; `audit_events(id uuid, tenant_id uuid not null, actor_id uuid, actor_kind text not null, action text not null, resource_kind text, resource_id uuid, before jsonb, after jsonb, diff jsonb, ip inet, user_agent text, correlation_id uuid not null, occurred_at timestamptz not null, primary key (id, occurred_at)) partition by range (occurred_at)` with partitions for the current and next three months.
- Invariants: unique `roles_tenant_slug_idx on (tenant_id, slug) where deleted_at is null`; unique `resource_acls_entry_idx on (tenant_id, resource_kind, resource_id, principal_kind, principal_id, effect)`; unique `role_bindings_idx on (tenant_id, role_id, principal_kind, principal_id, scope_kind, scope_id)`; trigger `audit_immutable` raising on `UPDATE`/`DELETE` of `audit_events`; a seed function `seed_system_roles(tenant_id)` invoked by a trigger on `tenants` insert.
- Indexes: `resource_acls(tenant_id, resource_kind, resource_id)`, `resource_acls(tenant_id, principal_kind, principal_id)`, `role_bindings(tenant_id, principal_kind, principal_id)`, `role_bindings(tenant_id, scope_kind, scope_id)`, `audit_events(tenant_id, occurred_at desc)`, `audit_events(tenant_id, resource_kind, resource_id, occurred_at desc)`, `audit_events(tenant_id, actor_id, occurred_at desc)`, `audit_events(tenant_id, correlation_id)`.
- Audit actions: `role.create`, `role.update`, `acl.replace` with entry diffs; `authz.check` is not audited (read) except when `principal` differs from the caller (`authz.check.delegated`).
- Retention/deletion: audit partitions are detached, not deleted, by the F027 retention job; roles soft-delete via `deleted_at` only when no bindings reference them; rollback drops the four tables, the trigger, the seed function, and the partitions.

### React/TypeScript

- Routes in `apps/web/src/features/authz/`: `/admin/roles`, `/admin/roles/$roleId`, `/admin/audit`; components `RolesPage`, `RoleEditor`, `PermissionMatrix`, `AclEditor` (exported drawer with props `{ resourceKind, resourceId }`), `AclEntryRow`, `PrincipalPicker`, `AuditLogPage`, `AuditFilters`, `AuditEventRow`, `DiffViewer`, `CopyCorrelationButton`.
- State: TanStack Query keys `['roles', cursor]`, `['role', id]`, `['acl', kind, id]`, `['audit-events', filters, cursor]`, `['permissions-catalogue']`; ACL mutations invalidate `['acl', kind, id]` and store the returned `version`; a `usePermission(kind, id, permission)` hook calls the check endpoint and caches 30 seconds for UI affordances (the API remains the authority).
- API client: generated `AuthzApi` with `listRoles`, `createRole`, `updateRole`, `getAcl`, `replaceAcl`, `check`, `listAuditEvents`.
- Optimistic updates: ACL entry toggles apply locally and roll back on `conflict` with the stale banner showing the entry diff.
- Telemetry: `role_created`, `role_updated`, `acl_replaced{entries}`, `acl_deny_added`, `audit_viewed{filters}`, `correlation_id_copied`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F003-01 through FR-F003-14 in `testing/features/F003/requirements/cases.md`
- [ ] Failure/edge-case tests: unknown permission, slug taken, editing a system role slug, 501 ACL entries, duplicate entries, stale version, deny on ancestor versus allow on resource, guest with tenant binding, role with bindings deleted, cache invalidation after ACL change
- [ ] Permission-negative and tenant-isolation tests: member creating a role, commenter replacing an ACL, non-admin delegated check, member reading audit, tenant-B admin on every route, field-level redaction
- [ ] Rust unit tests: `crates/domain/src/authz/` permission parsing and wildcard matching, evaluation order, cache key and invalidation, diff computation, redaction
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: seed roles trigger, unique indexes, append-only trigger, partition creation and pruning, rollback
- [ ] React component tests: `PermissionMatrix`, `AclEditor`, `AuditLogPage`, `DiffViewer` states
- [ ] Browser E2E tests: create role, set ACL with deny, verify denied access, read audit trail
- [ ] Accessibility tests: axe on admin pages, matrix keyboard navigation, diff viewer text exposure
- [ ] Performance/load tests: cached and uncached check p95, audit write overhead, audit list over 10M rows

### Fast fanout configuration

- Test harness path: `testing/features/F003/`
- Feature flag: `F003_FEATURE`
- Fixture/seed factory: `testing/fixtures/authz.rs` builds on `testing/fixtures/tenants.rs` and `auth.rs`, adding a custom role `Reviewer`, a synthetic 4-level ancestry (`tenant → workspace → folder → sheet` registered through a test `AncestryResolver`), bindings for admin, editor, commenter, viewer, a guest principal, and 1,000 audit rows across two partitions
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC
- Mock/stub contracts: in-memory outbox recorder; test `AncestryResolver`; real F038 extractor with fixture sessions
- Parallel isolation: one schema per test worker, tenant ids per test, cache namespaced per test
- Targeted command: `cargo xtask test-feature F003`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F003/`

## 6. Acceptance criteria

```gherkin
Feature: Roles, ACLs, policy evaluation, and audit

Scenario: Explicit deny on an ancestor wins
  Given editor Pat has an allow binding on workspace "Ops"
  And folder "Restricted" inside "Ops" has a deny entry for Pat
  When Pat reads a sheet inside "Restricted"
  Then the response is 404 not_found
  And POST /api/v1/authz/check returns decision denied with reason explicit_deny and the folder as matched_rule.scope

Scenario: Replace an ACL and audit it
  Given sheet "Budget" owned by Sam
  When Sam PUTs an ACL adding group "QA" with role "Reviewer" and a deny for guest "ext@partner.test"
  Then the effective ACL lists both entries with version 2
  And acl.updated.v1 and one audit row with action acl.replace and the entry diff exist under the same correlation_id

Scenario: Commenter cannot manage permissions
  Given a commenter on sheet "Budget"
  When they PUT /api/v1/resources/sheet/{id}/acl
  Then the response is 403 denied and the ACL version is unchanged

Scenario: Audit log is tenant-scoped and immutable
  Given 1,000 audit rows in tenant "acme"
  When a tenant-admin of "globex" lists audit events filtered by an "acme" resource id
  Then the page is empty
  And any UPDATE or DELETE on audit_events raises audit_immutable

Scenario: Guest never inherits tenant bindings
  Given a guest principal and a tenant-scoped viewer binding for group "Everyone"
  When the guest reads a sheet with no direct entry
  Then the response is 404 not_found
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F002 (tenants, users, groups, fixture), F038 (`ActorContext`, `AuthAuditSink`); decisions sections 2–4, 9; contracts row F003
- Blocks: F005, F016, F036, F021, F027, F028, F048
- Conflicts with: none (disjoint owned paths)
- External dependencies: none
- Risks and mitigations: ancestry for workspaces and folders does not exist until F005, so the engine resolves ancestry through the `AncestryResolver` trait and the harness registers a synthetic resolver; the 30-second cross-request cache can serve a stale allow for up to 30 seconds after a deny is added, so ACL replace also invalidates the local cache synchronously and the outbox event invalidates other instances; monthly partitions require the F004 worker job, so the migration pre-creates three months to cover the gap.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F002 and F038 accepted and archived; `testing/fixtures/{tenants.rs, auth.rs}` available
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F003/`
- [ ] Migration file name and owned paths claimed
- [ ] `Permission` catalogue agreed with F005–F010 owners and recorded in `crates/domain/src/authz/permissions.rs`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit rows and outbox events verified for every mutation; append-only trigger verified
- [ ] F002 and F038 routes switched to `RequirePermission` and the database `AuthAuditSink` without handler changes
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F003_FEATURE`, run down migration on an empty database
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Administrators can define roles, manage resource permissions with inheritance and explicit denies, test access decisions, and read an immutable audit log with correlation ids.
- Migration adds `roles`, `role_bindings`, `resource_acls`, and partitioned `audit_events`; rollback drops them. Feature is off by default behind `F003_FEATURE`.
