---
id: F050
type: feature
status: planned
priority: P1
owner: platform
estimate: 5
target_milestone: M7
parent_epic: E008
depends_on: [F013, F036, F048]
blocks: []
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/dynamic-views/**, crates/persistence/src/dynamic-views/**, services/api/src/dynamic-views/**, apps/web/src/features/dynamic-views/**, services/api/migrations/*_dynamic-views_*.sql, testing/features/F050/**]
feature_flag: F050_FEATURE
flag_default: off
branch: f050-dynamic-view
started_at: null
finished_at: null
---

# F050 — Dynamic View

## 1. Identity and dates

- Branch: `f050-dynamic-view`
- Capability area: advanced modules (spec 5.11 Dynamic View; 5.1 WORK-05 "views are saved, shareable, permission-aware" and "published and embedded views use scoped, revocable access tokens, preserve permission filtering"; 5.4b COLLAB-03 "external users never inherit tenant-wide access"; section 10 external sharing decision)
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 10; `docs/capability-contracts.md` row F050
- Module slug: `dynamic-views`

## 2. Requirement specification

### Problem and user outcome

A sheet owner needs to let vendors, contractors, or another department see and update only the rows and fields that concern them without sharing the whole sheet. Saved views (F013) filter presentation but do not enforce field-level hiding or restrict edits, and share links (F036) grant a whole resource. A dynamic view is a policy-enforced projection over one sheet: the server decides which rows and fields the audience sees and which fields they may edit, and every edit is recorded and applied under the owner's authority.

As a sheet owner, I want to publish a restricted view of my sheet to named users, groups, or an external token with row and field policies and controlled editing, so that outsiders can update their own rows without ever seeing or touching anything else.

### Functional requirements

- **FR-F050-01:** An actor holding `view-owner` (sheet owner or editor with share rights) can create a dynamic view with `{ name, sheet_id, base_view_id?, description? }` via `POST /api/v1/dynamic-views`; the response returns a UUIDv7 `id`, `version` 1, and an empty policy (`edit_mode: none`, no visible fields) so nothing is exposed until a policy is set.
- **FR-F050-02:** `PUT /api/v1/dynamic-views/{id}/policy` replaces the policy with `{ row_filter, visible_fields[], editable_fields[], edit_mode, allow_new_rows }` where `row_filter` is a typed predicate tree (`and`/`or` groups of `{ column_id, op, value }` with ops `eq`, `neq`, `in`, `contains`, `gt`, `lt`, `is_empty`) or the special predicate `{ assigned_to: "current_user" }`; `editable_fields` must be a subset of `visible_fields` and reference existing column IDs, otherwise `400 invalid` with `field_errors.editable_fields`. The request and response keep the arrays and the nested filter object; the server stores one `dynamic_view_visible_fields` row per visible column, one `dynamic_view_editable_fields` row per editable column (whose composite foreign key to the visible row is what makes the subset rule unbreakable), and one `dynamic_view_filter_nodes` row per predicate node with `dynamic_view_filter_values` rows for `in` operands, replacing the whole set in one transaction.
- **FR-F050-03:** `edit_mode` is one of `none` (read only), `assigned_rows` (edit only rows where a person column named in `assignment_column_id` equals the current user), or `all_visible`; `allow_new_rows: true` requires `edit_mode` other than `none` and creates rows that satisfy the row filter by pre-filling filter equality values, otherwise `400 invalid`.
- **FR-F050-04:** `GET /api/v1/dynamic-views/{id}/rows` returns only rows passing the stored filter nodes for the caller and only cells whose column has a `dynamic_view_visible_fields` row; a `fields` query naming a column without such a row is silently dropped, never returned, and never used for `filter` or `sort`; pages by cursor with `limit` ≤ 500. The response keeps its array-of-cells shape.
- **FR-F050-05:** Audiences are granted through F036 shares on `target_kind = dynamic-view` for tenant users and groups, or through a public token created with `PATCH /api/v1/dynamic-views/{id}` `{ public_token: { enable: true, expires_at, allow_edit } }`; `expires_at` is required, at most 30 days out, each issue writes one `dynamic_view_tokens` row and a partial unique index keeps at most one live row per view, the token is revocable via `{ public_token: { enable: false } }` which sets `revoked_at` on that row, and `GET /public/dynamic-views/{token}` serves the view without any tenant discovery (no workspace, sheet name, or other resource IDs in the response).
- **FR-F050-06:** `PATCH /api/v1/dynamic-views/{id}/rows/{row_id}` with `{ cells: { column_id: value }, version }` re-evaluates the row filter and edit mode server-side, rejects any key without a `dynamic_view_editable_fields` row with `403 denied` and `field_errors.cells.<column_id> = "not_editable"`, applies the change through the F008 cell service as the view owner with `on_behalf_of` the caller, and emits `dynamic-view.row-edited.v1`.
- **FR-F050-07:** Every accepted edit writes a `dynamic_view_edits` row with `actor_user_id` or `actor_token_id` (a real foreign key to `dynamic_view_tokens`), `row_id`, the before/after cell diff, `correlation_id`, and `applied_version`; the sheet's cell history (F008) records the same change with the dynamic view ID as origin.
- **FR-F050-08:** Public-token edits require `Idempotency-Key`, are rate-limited to 60 writes per token per minute (`429 rate_limited` above), and are refused with `403 denied` when the token row has `allow_edit: false`, is past `expires_at`, or has `revoked_at` set; revocation takes effect on the next request.
- **FR-F050-09:** Deleting a dynamic view is a soft delete that immediately sets `revoked_at` on its live `dynamic_view_tokens` row and invalidates its shares; listing with `deleted=true` shows it for the owner; edits already applied to the sheet are never rolled back by deletion.
- **FR-F050-10:** Every mutation requires `Idempotency-Key` and `If-Match`, writes an `audit_events` row with a diff, and publishes `dynamic-view.updated.v1` (create, patch, policy, delete) or `dynamic-view.row-edited.v1` through the outbox.
- **FR-F050-11:** Every route is behind `RequireModule(ModuleSlug::DynamicViews)`; a tenant that is not entitled receives `403 denied` with `field_errors.module`; creating a view beyond the tenant limit `max_views` or holding more live `dynamic_view_tokens` rows with `allow_edit` than `max_external_editors` returns `409 conflict` with `field_errors.limit`.
- **FR-F050-12:** Cross-tenant access to a dynamic view, its rows, or its token by ID returns `404 not_found`; a user without a share on the view (even a sheet viewer) also receives `404 not_found`.
- **FR-F050-13:** The web app renders the restricted grid at `/w/:workspaceId/dynamic-views/:id` for shared users and at `/dv/:token` for token holders, shows only visible fields, marks editable cells, blocks editing of others, and surfaces the stale, denied, expired-token, and offline states.
- **FR-F050-14:** The owner's policy editor lets the owner build the row filter, pick visible and editable fields, choose the edit mode, preview the view as a chosen user or as the token, and copy or revoke the public link; the preview uses the real rows endpoint impersonating nothing (it passes `preview_as`, honoured only for the owner).

### Non-functional requirements

- **NFR-F050-01 Performance:** rows for a 100,000-row sheet with a three-predicate filter respond in under 500 ms p95 with a warm cache; a single row edit completes in under 800 ms p95; public token lookup adds under 20 ms (spec section 6).
- **NFR-F050-02 Security/privacy:** hidden fields never appear in any response, log, or event payload; tokens are 32-byte random values stored as SHA-256 hashes; token responses contain no tenant, workspace, or sheet identifiers; policy re-check happens inside the edit transaction; all negatives are in the harness.
- **NFR-F050-03 Accessibility:** restricted grid, policy editor, and token dialog pass axe with zero serious violations; editable versus read-only cells are announced by screen readers; every action is keyboard reachable.
- **NFR-F050-04 Reliability/observability:** spans carry `tenant_id`, `dynamic_view_id`, `token_id` (hashed prefix), and `correlation_id`; metrics `dynamic_view_rows_total`, `dynamic_view_edit_denied_total{reason}`, `dynamic_view_token_expired_total`; edit application failure never leaves a `dynamic_view_edits` row without a matching cell change.

### Scope

Included: dynamic view CRUD, policy model and evaluation, filtered rows endpoint, controlled row edits with edit records, public tokens with expiry and revocation, F036 share integration, restricted grid, policy editor, preview, audit, outbox, module guard and limits.

Excluded: multi-sheet dynamic views (reports are F021), publishing dashboards or reports (F059), form-based intake (F014), update requests (F061), WorkApps embedding of dynamic views (F051 consumes this feature's rows endpoint), offline edits (F058).

## 3. UX specification

- Entry points: sheet toolbar `Share` menu → `Create dynamic view`; workspace tree node `Dynamic views`; owner route `/w/{workspace_id}/dynamic-views/{id}` with tabs `View`, `Policy`, `Audience`, `Edits`; public route `/dv/{token}`.
- Primary flow: owner opens a sheet, chooses `Create dynamic view`, names it `Vendor updates`, lands on the `Policy` tab, adds row filter `Vendor = current user`, picks visible fields `Task`, `Due`, `Vendor status`, marks `Vendor status` editable with `edit_mode: assigned_rows`, saves; opens `Audience`, enables a public link with 14-day expiry and editing on, copies it; the vendor opens `/dv/{token}`, sees three columns and only their rows, edits `Vendor status`, and the owner sees the edit in the `Edits` tab and the sheet cell history.
- Loading: skeleton grid; Empty: `No rows match this view for you`; Error: inline banner with `correlation_id` and retry; Success: cell save tick and toast; Stale/conflict: cell reverts with `This row changed` banner and reload; Offline: editing disabled with offline badge; Expired or revoked token: full-page `This link is no longer active` with no tenant details.
- Permission-denied: non-shared users see the not-found page; a shared user with `edit_mode: none` sees read-only cells with a lock icon; not-entitled tenants see the shared `ModuleNotEntitled` panel from F048.
- Responsive: restricted grid freezes the first visible column under 768 px; the policy editor stacks its three columns under 960 px.
- Keyboard: arrow keys move between cells, `Enter` edits an editable cell, `Escape` cancels, `Tab` moves through policy editor controls; focus ring token; motion respects `prefers-reduced-motion`.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062), Lucide icons `EyeOff`, `Lock`, `Link`, `Filter`, `UserCheck`, `Ban`; tokens from `apps/web/src/design/tokens.css`.

- Design: `design/artboards/DynamicView.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

Canonical contract: `docs/capability-contracts.md` row F050 (aggregate `dynamic-view`, module `dynamic-views`, role `view-owner`).

### Rust backend

- Data access (decision section 2.1): `crates/persistence/src/dynamic-views/` holds `DynamicViewRepository` (owns `dynamic_views`), `DynamicViewTokenRepository` (owns `dynamic_view_tokens`), `DynamicViewPolicyRepository` (owns `dynamic_view_policies` and its child tables `dynamic_view_visible_fields`, `dynamic_view_editable_fields`, `dynamic_view_filter_nodes`, `dynamic_view_filter_values`), and `DynamicViewEditRepository` (owns `dynamic_view_edits`); no other class writes these tables, and this feature owns no F006/F007/F013 table. Named queries: `DynamicViewRepository::{list_for_owner, find_for_audience, count_live_for_tenant, soft_delete_with_token_revocation}`, `DynamicViewTokenRepository::{issue_token, find_live_by_hash, revoke_live_token, count_live_edit_tokens}`, `DynamicViewPolicyRepository::{load_policy, replace_policy, list_visible_columns, list_editable_columns, is_column_editable, load_compiled_filter}`, `DynamicViewEditRepository::{append_edit, list_edits_for_view, list_edits_for_row}`. The use cases below depend on those repository traits and contain no SQL; `services/api/src/dynamic-views/` handlers, the public router, and the rate-limit layer call repositories only. The restricted row fetch never builds a SQL string in a handler: `load_compiled_filter` returns the typed predicate and the visible column ID set, and the F006 `RowRepository::list_rows_for_policy(sheet_id, compiled_policy, audience, cursor)` named query composes them into the `rows`/`cells` read, so `rows` and `cells` stay owned by their own repository. A policy save, a token issue or revoke, and an accepted row edit each run as one `UnitOfWork`: the policy replacement spans five tables, and an edit spans the F008 cell write, `dynamic_view_edits`, the audit row, and the outbox enqueue.
- Domain entities in `crates/domain/src/dynamic-views/`: `DynamicView { id, tenant_id, sheet_id, base_view_id, name, description, public_token: Option<PublicToken>, version, created/updated actor+time, deleted_at }`, `PublicToken { id, view_id, token_hash, expires_at, allow_edit, revoked_at }`, `ViewPolicy { view_id, row_filter: Predicate, visible_fields: Vec<ColumnId>, editable_fields: Vec<ColumnId>, edit_mode: EditMode, assignment_column_id: Option<ColumnId>, allow_new_rows: bool, version }` — the in-memory vectors and predicate tree are assembled by `DynamicViewPolicyRepository` from the child tables and fanned back out on save, `Predicate` (enum `And`, `Or`, `Cmp { column_id, op, value }`, `AssignedToCurrentUser`), `EditMode { None, AssignedRows, AllVisible }`, `DynamicViewEdit { id, view_id, row_id, actor: EditActor, before: Cells, after: Cells, correlation_id, applied_version, created_at }`, `EditActor { User(UserId), Token(TokenId) }`, `Audience { User(UserId) | Group(GroupId) | Token(TokenId) }`.
- Use cases: `create_view`, `update_view`, `delete_view`, `list_views`, `set_policy`, `list_rows(view, audience, cursor)`, `edit_row(view, audience, row_id, cells)`, `create_row(view, audience, cells)`, `enable_token`, `revoke_token`, `resolve_token(raw) -> (DynamicView, Audience)`; pure functions `project_rows(policy, rows, audience)` and `check_edit(policy, row, audience, cells) -> Result<(), EditDenied>` are unit tested with a predicate table.
- API endpoints (`services/api/src/dynamic-views/`): `GET /api/v1/dynamic-views`, `POST /api/v1/dynamic-views`, `PATCH /api/v1/dynamic-views/{id}`, `DELETE /api/v1/dynamic-views/{id}`, `PUT /api/v1/dynamic-views/{id}/policy`, `GET /api/v1/dynamic-views/{id}/rows`, `PATCH /api/v1/dynamic-views/{id}/rows/{row_id}`, `GET /public/dynamic-views/{token}`. DTOs: `CreateDynamicViewRequest`, `UpdateDynamicViewRequest { name?, description?, public_token? }`, `PolicyRequest`, `DynamicViewResponse`, `PolicyResponse`, `Page<ProjectedRow>`, `EditRowRequest { cells, version }`, `PublicViewResponse { name, columns, rows_cursor_url, allow_edit, expires_at }`.
- Events: `dynamic-view.updated.v1` (payload adds `sheet_id`, `changed_fields` including `policy` and `public_token`), `dynamic-view.row-edited.v1` (payload adds `view_id`, `row_id`, `actor_kind`, `changed_columns`; never cell values).
- Authorization: `view-owner` for create, patch, policy, delete, token; rows and edits for shared users via F036 share lookup on `(dynamic-view, id)` or a valid token; `RequireModule(ModuleSlug::DynamicViews)` layer on the whole router; the public router applies the module guard using the view's tenant after token resolution.
- Permission matrix (rows are actors, columns are operations; `owner` = `view-owner`, `shared` = user or group with an F036 share, `token` = valid public token, `viewer` = sheet reader without a share, `foreign` = other tenant):

| Actor | create/policy/delete/token | list own views | rows | edit row | public GET |
|---|---|---|---|---|---|
| owner | allowed | allowed | allowed (unfiltered preview only with `preview_as`) | allowed | allowed |
| shared | `denied` | own shares only | filtered | per `edit_mode` | allowed |
| token | `not_found` | `not_found` | filtered | per `allow_edit` and `edit_mode` | allowed until expiry/revoke |
| viewer | `not_found` | empty | `not_found` | `not_found` | allowed |
| foreign | `not_found` | empty | `not_found` | `not_found` | `denied` under the view tenant's guard |

- Validation: name 1–200 chars; predicate depth ≤ 4 and ≤ 20 leaves; `visible_fields` 1–500 column IDs of the sheet; `expires_at` > now and ≤ now + 30 days; `limit` 1–500; token writes 60 per minute via the F038 rate-limit buckets keyed by `token_id`.
- Error mapping: `DynamicViewError::NotEditable → 403 denied`, `DynamicViewError::RowNotInView → 404 not_found`, `DynamicViewError::TokenInactive → 403 denied`, `DynamicViewError::LimitReached → 409 conflict`, `DynamicViewError::StaleVersion → 409 conflict`, `DynamicViewError::NotFound → 404 not_found`, `RateLimit → 429 rate_limited`, validation → `400 invalid` with `field_errors`.

### PostgreSQL/SQLx

- Migration `*_dynamic-views_*.sql` creates `dynamic_views(id uuid pk, tenant_id uuid not null, sheet_id uuid not null references sheets(id) on delete cascade, base_view_id uuid null references views(id) on delete restrict, name text not null, description text, version bigint not null default 1, created_by uuid not null references users(id) on delete restrict, created_at, updated_by uuid not null references users(id) on delete restrict, updated_at, deleted_at)`, `dynamic_view_policies(view_id uuid pk references dynamic_views(id) on delete cascade, tenant_id uuid not null, edit_mode text not null check (edit_mode in ('none','assigned_rows','all_visible')), assignment_column_id uuid null references columns(id) on delete restrict, allow_new_rows bool not null default false, version bigint not null default 1, updated_by uuid not null references users(id) on delete restrict, updated_at)`, and `dynamic_view_edits(id uuid pk, tenant_id uuid not null, view_id uuid not null references dynamic_views(id) on delete restrict, row_id uuid not null references rows(id) on delete restrict, actor_user_id uuid null references users(id) on delete restrict, actor_token_id uuid null references dynamic_view_tokens(id) on delete restrict, before jsonb not null, after jsonb not null, correlation_id uuid not null, applied_version bigint not null, created_at timestamptz not null)`.
- Normalized sets (decision section 2, no array columns): `dynamic_view_visible_fields(view_id uuid not null references dynamic_view_policies(view_id) on delete cascade, tenant_id uuid not null, column_id uuid not null references columns(id) on delete cascade, ordinal smallint not null, primary key (view_id, column_id), unique (view_id, ordinal))` replaces `visible_fields uuid[]`; `dynamic_view_editable_fields(view_id uuid not null, tenant_id uuid not null, column_id uuid not null, primary key (view_id, column_id), foreign key (view_id, column_id) references dynamic_view_visible_fields(view_id, column_id) on delete cascade)` replaces `editable_fields uuid[]` and turns the former `editable_fields <@ visible_fields` check into a referential constraint that cannot be bypassed by a partial update; `dynamic_view_tokens(id uuid pk, tenant_id uuid not null, view_id uuid not null references dynamic_views(id) on delete cascade, token_hash bytea not null, expires_at timestamptz not null, allow_edit bool not null default false, revoked_at timestamptz null, created_by uuid not null references users(id) on delete restrict, created_at timestamptz not null)` replaces the repeated `token_*` columns on `dynamic_views` and is created before `dynamic_view_edits` in the migration, so re-issuing a link keeps the revoked row for the edit records that point at it. `PolicyRequest`, `DynamicViewResponse`, and `PolicyResponse` keep `visible_fields` and `editable_fields` as JSON arrays and `public_token` as an object, so no externally visible behaviour changes; `DynamicViewPolicyRepository::replace_policy` and `DynamicViewTokenRepository::issue_token` fan them out to rows and reassemble them on read.
- Row filter as tables (decision section 2, the product evaluates and enforces this structure, so it is not a schema-less payload): `dynamic_view_filter_nodes(id uuid pk, tenant_id uuid not null, view_id uuid not null references dynamic_view_policies(view_id) on delete cascade, parent_id uuid null references dynamic_view_filter_nodes(id) on delete cascade, ordinal smallint not null, node_kind text not null check (node_kind in ('and','or','cmp','assigned_to_current_user')), column_id uuid null references columns(id) on delete cascade, op text null check (op in ('eq','neq','in','contains','gt','lt','is_empty')), value text null, check ((node_kind in ('and','or') and column_id is null and op is null) or (node_kind = 'cmp' and column_id is not null and op is not null) or (node_kind = 'assigned_to_current_user' and op is null)), unique (view_id, parent_id, ordinal))` and `dynamic_view_filter_values(node_id uuid not null references dynamic_view_filter_nodes(id) on delete cascade, tenant_id uuid not null, ordinal smallint not null, value text not null, primary key (node_id, ordinal))` hold the `in` operand list. Together they replace `row_filter jsonb`; the API keeps the nested predicate object in `PolicyRequest`/`PolicyResponse` and the tree is rebuilt from the node rows by `load_policy`.
- `jsonb` audit: `dynamic_view_policies.row_filter` was a queried structure — `project_rows` reads it by key on every rows request and the policy editor validates depth and leaf counts against it — so it becomes `dynamic_view_filter_nodes` and `dynamic_view_filter_values` per decision section 2. `dynamic_view_edits.before` and `dynamic_view_edits.after` stay `jsonb`: they are the before/after diff of typed cell values from F007, never filtered, joined, sorted, or constrained; the queried facts (`view_id`, `row_id`, actor, `applied_version`, `created_at`) are columns. This module stores no view- or widget-settings blob, so no other `jsonb` column exists in it.
- Invariants: unique `dynamic_views(tenant_id, sheet_id, lower(name)) where deleted_at is null`; unique `dynamic_view_tokens(token_hash)` and partial unique `dynamic_view_tokens(view_id) where revoked_at is null` giving at most one live link per view; `dynamic_view_editable_fields` is a strict subset of `dynamic_view_visible_fields` by composite foreign key, and its primary key blocks a duplicate editable column; `dynamic_view_visible_fields` primary key blocks a duplicate visible column and its `(view_id, ordinal)` unique index keeps column order deterministic; check `(edit_mode <> 'assigned_rows') or (assignment_column_id is not null)`; check `(allow_new_rows = false) or (edit_mode <> 'none')`; `dynamic_view_filter_nodes` node-kind check keeps comparison operands off group nodes, its `(view_id, parent_id, ordinal)` unique index keeps sibling order stable, and depth ≤ 4 and ≤ 20 leaves are enforced by `replace_policy` before insert; check exactly one of `actor_user_id`, `actor_token_id` is non-null on edits.
- Indexes: `dynamic_views(tenant_id, sheet_id) where deleted_at is null`, `dynamic_view_tokens(token_hash)` for public resolution and `dynamic_view_tokens(tenant_id, allow_edit) where revoked_at is null` for the `max_external_editors` count, `dynamic_view_visible_fields(view_id)` and `dynamic_view_visible_fields(column_id)` for the "which views expose this column" reverse lookup, `dynamic_view_editable_fields(view_id)` for the per-edit editability check, `dynamic_view_filter_nodes(view_id, parent_id, ordinal)` for tree load and `dynamic_view_filter_nodes(column_id)` for the reverse "which policies filter on this column" query used when a column is deleted, `dynamic_view_filter_values(node_id)`, `dynamic_view_edits(view_id, created_at desc)`, `dynamic_view_edits(row_id)`, `dynamic_view_edits(actor_token_id)`.
- Audit events: `dynamic-view.create`, `dynamic-view.update`, `dynamic-view.policy.set`, `dynamic-view.token.enable`, `dynamic-view.token.revoke`, `dynamic-view.delete`, `dynamic-view.row.edit` with diffs (policy diff lists column IDs, not values).
- Retention/deletion: soft delete on the view; revoked `dynamic_view_tokens` rows are kept while any `dynamic_view_edits` row references them; `dynamic_view_edits` retained per tenant audit retention (F027); rollback drops the eight tables children before parents (`dynamic_view_filter_values`, `dynamic_view_filter_nodes`, `dynamic_view_editable_fields`, `dynamic_view_visible_fields`, `dynamic_view_edits`, `dynamic_view_tokens`, `dynamic_view_policies`, `dynamic_views`).

### React/TypeScript

- Routes: `/w/:workspaceId/dynamic-views/:id` (tabs `view`, `policy`, `audience`, `edits`) and `/dv/:token` in `apps/web/src/features/dynamic-views/`; components `DynamicViewPage`, `RestrictedGrid`, `RestrictedCell`, `PolicyEditor`, `PredicateBuilder`, `FieldPicker`, `EditModeSelect`, `AudiencePanel`, `PublicLinkDialog`, `PreviewAsSelector`, `EditsLog`, `PublicViewPage`, `LinkInactivePage`.
- State: TanStack Query keys `['dynamic-view', id]`, `['dynamic-view-policy', id]`, `['dynamic-view-rows', id, audienceKey, cursor]`, `['dynamic-view-edits', id, cursor]`, `['public-dynamic-view', token]`; edit mutations update the cached row version and invalidate the edits log.
- API client: generated `DynamicViewsApi` with `listViews`, `createView`, `updateView`, `deleteView`, `setPolicy`, `listRows`, `editRow`, `getPublicView`; module gate through `useModuleAllowed('dynamic-views')` from F048.
- Optimistic updates: cell edit applies locally, rolls back on `conflict` or `denied` with the reason banner.
- Telemetry: `dynamic_view_created`, `dynamic_view_policy_saved`, `dynamic_view_token_enabled`, `dynamic_view_token_revoked`, `dynamic_view_row_edited`, `dynamic_view_public_opened` with `view_id`, `edit_mode`, `actor_kind`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F050-01 through FR-F050-14 in `testing/features/F050/requirements/cases.md`
- [ ] Failure/edge-case tests: editable field not visible, `allow_new_rows` with `edit_mode: none`, token expiry over 30 days, revoked token, edit outside filter, hidden field requested via `fields`, limit reached
- [ ] Permission-negative and tenant-isolation tests: sheet viewer without share gets `not_found`, token cannot list other views, cross-tenant `not_found`, non-editable cell `denied`, not-entitled tenant `denied`
- [ ] Rust unit tests: `project_rows` predicate table, `check_edit` for each edit mode, token hashing and expiry
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: editable-field row without a matching visible-field row rejected by the composite foreign key, duplicate visible or editable column rejected, filter node with a comparison operand on an `and` group rejected, orphan `dynamic_view_filter_values` rejected, second live `dynamic_view_tokens` row for a view rejected, token hash uniqueness, edit-mode checks, single-actor check, cascade from view delete to policy, fields, and filter rows, rollback ordering
- [ ] React component tests: `RestrictedGrid`, `PolicyEditor`, `PublicLinkDialog`, `PublicViewPage` states
- [ ] Browser E2E tests: owner builds policy, vendor edits through token, revoke blocks link
- [ ] Accessibility tests: axe on grid, editor, dialog; editable cell announcements
- [ ] Performance/load tests: 100k-row filtered list p95 < 500 ms, edit p95 < 800 ms, token resolve < 20 ms

### Fast fanout configuration

- Test harness path: `testing/features/F050/`
- Feature flag: `F050_FEATURE`
- Fixture/seed factory: `testing/fixtures/dynamic_views.rs` builds tenant A (owner, shared user, unshared sheet viewer), tenant B, a 200-row sheet with `Vendor` person column and `Vendor status` select column, a dynamic view with `assigned_rows` policy, a live token and a revoked token; `data-shuttle` style entitlement rows for `dynamic-views` active with `max_views 3`
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC, fixed token bytes
- Mock/stub contracts: outbox publisher recorded in memory; F036 shares and F048 evaluator real with fixture rows; F008 cell service real
- Parallel isolation: one schema per test worker, tenant ID per test
- Targeted command: `cargo xtask test-feature F050`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F050/`

## 6. Acceptance criteria

```gherkin
Feature: Dynamic View restricted access and controlled editing

Scenario: Vendor sees and edits only assigned rows
  Given a dynamic view with row filter Vendor = current user, visible fields Task, Due, Vendor status and edit_mode assigned_rows
  When vendor user opens the rows endpoint and patches Vendor status on one of their rows
  Then only their rows and the three fields are returned
  And the edit is applied, a dynamic_view_edits row exists, and dynamic-view.row-edited.v1 is in the outbox

Scenario: Hidden field is never returned
  Given the same view where Budget has no dynamic_view_visible_fields row
  When the vendor requests fields=Task,Budget
  Then the response contains Task and no Budget cell, and filter on Budget is ignored

Scenario: Editable field cannot escape the visible set
  Given a policy whose visible fields are Task, Due and Vendor status
  When the owner marks Budget editable
  Then the response is 400 invalid with field_errors.editable_fields
  And no dynamic_view_editable_fields row exists for Budget

Scenario: Unshared sheet viewer cannot open the view
  Given a tenant user who can read the sheet but has no share on the dynamic view
  When they request the view or its rows by id
  Then the response is 404 not_found

Scenario: Revoked public token
  Given a public token with editing enabled
  When the owner revokes it and the vendor retries an edit
  Then the response is 403 denied and no edit row is written
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F013 (saved views as optional base, view rows query), F036 (shares on `dynamic-view` target kind, guest identity), F048 (`RequireModule`, limits, `useModuleAllowed`), F006 `RowRepository::list_rows_for_policy` for the restricted read; decisions sections 2, 2.1, 3, 4, 10; contracts row F050
- Blocks: none directly (F051 embeds dynamic views but depends only on F013, F014, F023, F048 by plan)
- Conflicts with: none (disjoint owned paths)
- External dependencies: none
- Risks and mitigations: policy evaluation on the client would leak data, so projection runs only in the service and the harness asserts hidden columns are absent from raw HTTP bodies; predicate evaluation over 100k rows could be slow, so `load_compiled_filter` turns equality and `in` nodes into bound parameters of the `RowRepository::list_rows_for_policy` named query, which narrows on the indexed `cells` lookup before the remaining predicate runs, and no handler concatenates SQL; token leakage through logs is prevented by logging only the first 6 hex chars of the hash.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F013, F036, and F048 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F050/`
- [ ] Migration file name and owned paths claimed
- [ ] `dynamic-views` module registered in F048 `ModuleSlug` with limits `max_views`, `max_external_editors`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F050_FEATURE` (routes unmounted, tokens inert), run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Sheet owners can publish dynamic views with row and field policies, controlled editing, and expiring public links; every external edit is recorded and traceable.
- Migration adds `dynamic_views`, `dynamic_view_policies`, `dynamic_view_visible_fields`, `dynamic_view_editable_fields`, `dynamic_view_filter_nodes`, `dynamic_view_filter_values`, `dynamic_view_tokens`, and `dynamic_view_edits`; rollback drops them children first. Feature is off by default behind `F050_FEATURE` and requires the `dynamic-views` entitlement.
