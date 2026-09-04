---
id: F051
type: feature
status: planned
priority: P1
owner: platform
estimate: 8
target_milestone: M7
parent_epic: E008
depends_on: [F013, F014, F023, F048]
blocks: []
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/workapps/**, crates/persistence/src/workapps/**, services/api/src/workapps/**, apps/web/src/features/workapps/**, services/api/migrations/*_workapps_*.sql, testing/features/F051/**]
feature_flag: F051_FEATURE
flag_default: off
branch: f051-workapps
started_at: null
finished_at: null
---

# F051 — WorkApps

## 1. Identity and dates

- Branch: `f051-workapps`
- Capability area: advanced modules (spec 5.11 WorkApps "no-code app shell with navigation, role-specific pages, embedded sheets/forms/reports, and app permissions"; 1.1 "an external or role-specific experience is a filtered presentation/editing surface, not a second source of truth"; 5.1 WORK-05 permission-aware views; 5.4b COLLAB-03 granular roles)
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 6, 10; `docs/capability-contracts.md` row F051
- Module slug: `workapps`

## 2. Requirement specification

### Problem and user outcome

Teams assemble a process from several sheets, forms, reports, and dashboards, but each participant sees a different subset and must navigate the raw workspace tree to find them. A WorkApp is a named shell with a slug, an ordered set of pages that embed existing surfaces, and roles that decide which pages each member sees and where they land. The app never grants data access on its own: every embedded surface loads through its own endpoint under the viewer's real permissions.

As an app admin, I want to compose an app from existing sheets, forms, reports, dashboards, and dynamic views, assign pages to roles, and publish a versioned app at a stable URL, so that each role gets a focused experience without new permissions or duplicated data.

### Functional requirements

- **FR-F051-01:** An actor with `app-admin` on the workspace can create an app via `POST /api/v1/workapps` with `{ name (1–120), slug (^[a-z0-9-]{3,40}$, unique per tenant), workspace_id, icon? (Lucide name), description? (≤ 2,000) }`; the response returns a UUIDv7 `id`, `version` 1, `status: draft`, and `published_version: null`; a duplicate slug returns `409 conflict` with `field_errors.slug`.
- **FR-F051-02:** `PUT /api/v1/workapps/{id}/pages` replaces the draft page list with up to 50 entries `{ id?, title (1–80), kind (sheet|form|report|dashboard|dynamic-view|text), source_id? (required unless kind is text), body? (markdown ≤ 20,000 chars for text), position, visible_to_roles[] }`; the request and response keep `visible_to_roles` as a JSON array of role IDs while storage writes one `workapp_page_roles(page_id, role_id)` row per entry, so the API shape is unchanged; each `source_id` must exist in the same tenant and workspace and match the kind (sheet → F006 sheet or F013 view, form → F014 published form, report → F021 report, dashboard → F023 dashboard, dynamic-view → F050 view) or the request returns `400 invalid` with `field_errors.pages[n].source_id`; a 51st page returns `400 invalid` with `field_errors.pages = "max_50"`.
- **FR-F051-03:** `PUT /api/v1/workapps/{id}/roles` replaces the draft role list (1–20 roles) with `{ id?, name (1–60, unique in app), members: [{ kind: user|group, id }], default_landing_page_id }`; the request and response keep `members` as a JSON array while storage writes one `workapp_role_members` row per member with a real `user_id` or `group_id` foreign key, so the API shape is unchanged; `default_landing_page_id` must reference a page visible to that role, otherwise `400 invalid` with `field_errors.roles[n].default_landing_page_id`; a role with zero members is allowed for drafts but publishing warns in the response.
- **FR-F051-04:** `POST /api/v1/workapps/{id}/publish` snapshots the draft manifest into an immutable `workapp_versions` row with `version_number` n+1 plus its `workapp_version_pages`, `workapp_version_roles`, `workapp_version_page_roles`, and `workapp_version_role_members` rows written in the same transaction, sets `published_version` to it, and emits `workapp.published.v1`; the snapshot is relational, not a document, because the viewer route filters and permission-checks it on every request; publishing an app with zero pages or zero roles returns `400 invalid`; `{ version_number: k }` in the body copies an earlier snapshot's rows into a new version (rollback) without editing the draft.
- **FR-F051-05:** `GET /apps/{slug}` serves the latest published manifest filtered to the caller: the server joins `workapp_version_page_roles` to the roles the caller holds (resolved from `workapp_version_role_members` through direct user membership or F002 group membership) and returns only the matching pages, the caller's landing page, and app metadata; a caller holding no role receives `404 not_found`; an app with no published version returns `404 not_found` to everyone except admins, who receive the draft with `status: draft`.
- **FR-F051-06:** Embedded surfaces are never proxied by the app: the web shell fetches sheet rows, form definitions, report rows, dashboard widget data, and dynamic view rows through their own F006/F013/F014/F021/F023/F050 endpoints under the viewer's own session, so a page whose source the viewer cannot read renders the denied state and the app never widens access.
- **FR-F051-07:** `GET /api/v1/workapps` lists apps in a workspace with cursor paging, filter by `status` (`draft`, `published`) and `name` prefix; `GET /api/v1/workapps/{id}` returns the draft manifest plus `published_version` and the last five version summaries; `PATCH /api/v1/workapps/{id}` updates `name`, `icon`, `description`, and `status: archived` (archived apps return `404` from `/apps/{slug}` and keep their history).
- **FR-F051-08:** Draft edits to pages or roles never change what `GET /apps/{slug}` serves until the next publish; the draft carries `draft_dirty: true` when it differs from the published snapshot.
- **FR-F051-09:** Every mutation requires `Idempotency-Key` and `If-Match`, writes an `audit_events` row with a diff (page and role diffs list IDs and titles), and publishes `workapp.updated.v1` (create, patch, pages, roles) or `workapp.published.v1` through the outbox.
- **FR-F051-10:** Every route is behind `RequireModule(ModuleSlug::Workapps)`; a tenant that is not entitled receives `403 denied` with `field_errors.module`; exceeding tenant limits `max_apps` or `max_pages_per_app` returns `409 conflict` with `field_errors.limit`.
- **FR-F051-11:** Cross-tenant access to an app by ID or slug returns `404 not_found`; a workspace member without `app-admin` receives `403 denied` on mutations and `404 not_found` on draft reads.
- **FR-F051-12:** The web app renders the published app at `/apps/:slug` and `/apps/:slug/:pageId` with role-filtered navigation, the landing page for the caller's first role, embedded surfaces in their native components, and denied/empty/error states per page; the builder at `/w/:workspaceId/workapps/:id` lets an admin edit pages, roles, preview as a role, and publish with a version note.
- **FR-F051-13:** A published app version is retrievable and diffable: the builder shows the version list with author, time, note, and a page/role diff computed by joining the two versions' `workapp_version_pages`, `workapp_version_roles`, and `workapp_version_page_roles` rows, and offers `Restore this version` which calls publish with `version_number`.

### Non-functional requirements

- **NFR-F051-01 Performance:** `GET /apps/{slug}` responds in under 300 ms p95 for an app with 50 pages and 20 roles; the app shell renders navigation within 500 ms p95 after the manifest arrives; embedded surfaces keep their own feature budgets (spec section 6).
- **NFR-F051-02 Security/privacy:** the manifest returned to a viewer contains only pages they may see and never lists other roles' members; slugs are tenant-scoped and the public path leaks no tenant ID; every embedded fetch carries the viewer's own session and is authorized by the source feature.
- **NFR-F051-03 Accessibility:** app navigation is a labelled `nav` with current-page state; builder drag-and-drop page ordering has keyboard equivalents; role preview switch is announced; axe reports zero serious violations on shell and builder.
- **NFR-F051-04 Reliability/observability:** spans carry `tenant_id`, `workapp_id`, `version_number`, `page_id`, `correlation_id`; metrics `workapp_opened_total{slug}`, `workapp_page_denied_total{kind}`, `workapp_publish_total`; publish is transactional so a failed snapshot never advances `published_version`.

### Scope

Included: app CRUD, page and role manifests, validation against source features, publish and versioned rollback, role-filtered manifest at `/apps/{slug}`, app shell and builder UI, preview as role, audit, outbox, module guard and limits.

Excluded: new data surfaces (every page embeds an existing F006/F013/F014/F021/F023/F050 resource), custom code or scripting in pages, per-page permission overrides that widen access, external or anonymous app access (F059 publishing covers anonymous embeds), mobile-specific shell (F058).

## 3. UX specification

- Entry points: workspace tree node `Apps` → `New app`; builder route `/w/{workspace_id}/workapps/{id}` with tabs `Pages`, `Roles`, `Versions`; published app at `/apps/{slug}`; app switcher in the global header lists apps the user holds a role in.
- Primary flow: admin creates `Vendor onboarding` with slug `vendor-onboarding`, adds pages `Intake form` (form), `My vendors` (dynamic view), `Status board` (sheet in board mode), `KPIs` (dashboard), creates roles `Procurement` (all pages, landing `Status board`) and `Vendor` (`Intake form`, `My vendors`, landing `Intake form`), previews as `Vendor`, publishes with note `Initial release`; a vendor-role user opens `/apps/vendor-onboarding`, lands on `Intake form`, and sees only two navigation items.
- Loading: shell skeleton with navigation placeholders; Empty: `This app has no pages for your role` when the role filter yields nothing (admins see a link to the builder); Error: inline banner with `correlation_id` and retry; Success: toast `Published version 3`; Stale/conflict: builder banner `This app changed` with `Reload`; Offline: builder mutations disabled with badge; per-page denied: `You do not have access to this content` inside the page frame with the source name hidden.
- Permission-denied: non-members get the not-found page for the slug; workspace members without `app-admin` cannot open the builder; not-entitled tenants see the shared `ModuleNotEntitled` panel.
- Responsive: navigation collapses to a drawer under 960 px; embedded surfaces inherit their own responsive rules; builder page list stacks above the editor under 768 px.
- Keyboard: `Alt+ArrowUp/Down` reorders the focused page in the builder, `Enter` opens a page, navigation is a `nav` with arrow-key roving focus, `Escape` closes the drawer; motion respects `prefers-reduced-motion`.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062), Lucide icons `LayoutGrid`, `Layers`, `Users`, `Rocket`, `History`, `EyeOff`; tokens from `apps/web/src/design/tokens.css`.

## 4. Technical specification

Canonical contract: `docs/capability-contracts.md` row F051 (aggregate `work-app`, module `workapps`, role `app-admin`).

### Rust backend

- Data access (decision section 2.1): `crates/persistence/src/workapps/` holds `WorkAppRepository` (owns `workapps`), `WorkAppPageRepository` (owns `workapp_pages` and its visibility child `workapp_page_roles`), `WorkAppRoleRepository` (owns `workapp_roles` and its membership child `workapp_role_members`), and `WorkAppVersionRepository` (owns `workapp_versions`, `workapp_version_pages`, `workapp_version_roles`, `workapp_version_page_roles`, `workapp_version_role_members`); every child table is written only by the repository of its parent object type, so no two classes write the same table. Named queries: `find_app_by_slug`, `list_apps_in_workspace`, `count_apps_for_tenant`, `set_published_version`, `archive_app`; `list_pages_for_app`, `replace_pages`, `replace_page_role_visibility`, `list_role_ids_for_page`; `list_roles_for_app`, `replace_roles`, `replace_role_members`, `list_draft_roles_for_actor`; `insert_version_snapshot`, `copy_version_as_new_number`, `load_version_manifest`, `list_version_summaries`, `list_roles_held_in_version`, `list_visible_pages_for_roles`. There is no generic query entry point. Every use case below depends on these repository traits and contains no SQL; the handlers, the `SourceResolver` adapters, and the harness fixtures call repositories only. Publishing writes `workapps`, `workapp_versions`, the four version child tables, the audit row, and the outbox row inside one `UnitOfWork`, as do `PUT /pages` (pages plus visibility rows) and `PUT /roles` (roles plus member rows), so a partial manifest is never visible.
- Domain entities in `crates/domain/src/workapps/`: `WorkApp { id, tenant_id, workspace_id, name, slug: Slug, icon, description, status: AppStatus (Draft, Published, Archived), published_version: Option<u32>, version, created/updated actor+time, deleted_at }`, `Page { id, app_id, title, kind: PageKind, source_id: Option<Uuid>, body: Option<String>, position: u16, visible_to_roles: Vec<RoleId> }`, `AppRole { id, app_id, name, members: Vec<Member>, default_landing_page_id: PageId }`, `Member { kind: MemberKind (User, Group), id }`, `Manifest { app, pages, roles }`, `AppVersion { id, app_id, version_number, manifest: Manifest, note, created_by, created_at }`, `ViewerManifest { app, pages (filtered), landing_page_id, roles_held }`. `Page.visible_to_roles`, `AppRole.members`, and `AppVersion.manifest` are in-memory aggregates assembled by the repositories from `workapp_page_roles`, `workapp_role_members`, and the `workapp_version_*` tables; no domain type is persisted as an array or a document.
- Use cases: `create_app`, `update_app`, `list_apps`, `get_app`, `set_pages`, `set_roles`, `publish`, `resolve_viewer_manifest(slug, actor)`, `list_versions`; pure functions `validate_manifest(manifest, sources) -> Result<Warnings, FieldErrors>` and `filter_for_viewer(manifest, roles_held) -> ViewerManifest` are unit tested with role and page tables; `SourceResolver` trait checks source existence and kind through F006/F013/F014/F021/F023/F050 read services.
- API endpoints (`services/api/src/workapps/`): `GET /api/v1/workapps`, `POST /api/v1/workapps`, `GET /api/v1/workapps/{id}`, `PATCH /api/v1/workapps/{id}`, `PUT /api/v1/workapps/{id}/pages`, `PUT /api/v1/workapps/{id}/roles`, `POST /api/v1/workapps/{id}/publish`, `GET /apps/{slug}`. DTOs: `CreateWorkAppRequest`, `UpdateWorkAppRequest { name?, icon?, description?, status? }`, `SetPagesRequest { pages }`, `SetRolesRequest { roles }`, `PublishRequest { note?, version_number? }`, `WorkAppResponse` (draft manifest + `published_version` + `draft_dirty` + `versions[0..5]`), `PublishResponse { version_number, warnings }`, `ViewerManifestResponse`.
- Events: `workapp.updated.v1` (payload adds `slug`, `changed_fields` among `name`, `icon`, `description`, `status`, `pages`, `roles`), `workapp.published.v1` (payload adds `slug`, `version_number`, `page_count`, `role_count`).
- Authorization: `app-admin` on the workspace for every mutation and draft read; `GET /apps/{slug}` for any authenticated tenant user holding at least one role in the published manifest; `RequireModule(ModuleSlug::Workapps)` layer on both routers; group membership resolved through F002 `group_members`.
- Permission matrix (rows are actors, columns are operations; `admin` = `app-admin` on the workspace, `role-holder` = tenant user with at least one published app role, `member` = workspace member without a role, `foreign` = other tenant):

| Actor | create/patch/pages/roles/publish | read draft and versions | `GET /apps/{slug}` | embedded surface data |
|---|---|---|---|---|
| admin | allowed | allowed | full manifest, or draft when unpublished | own permissions via source feature |
| role-holder | `denied` | `not_found` | pages for held roles only | own permissions via source feature |
| member | `denied` | `not_found` | `not_found` | not reachable through the app |
| foreign | `not_found` | `not_found` | `not_found` | not reachable |

- Validation: slug regex and tenant uniqueness; pages ≤ 50 and ≤ `max_pages_per_app`; roles 1–20; `visible_to_roles` must reference role IDs in the same manifest; `position` unique per app; text pages ≤ 20,000 chars; `note` ≤ 500 chars.
- Error mapping: `WorkAppError::SlugTaken → 409 conflict`, `WorkAppError::SourceMissing → 400 invalid`, `WorkAppError::EmptyManifest → 400 invalid`, `WorkAppError::LimitReached → 409 conflict`, `WorkAppError::StaleVersion → 409 conflict`, `WorkAppError::NotFound → 404 not_found`, `WorkAppError::NoRole → 404 not_found`, `AuthzError::Denied → 403 denied`, validation → `400 invalid` with `field_errors`.

### PostgreSQL/SQLx

- Migration `*_workapps_*.sql` creates the four catalog tables `workapps`, `workapp_pages`, `workapp_roles`, `workapp_versions` and five child tables for the sets they used to hold in arrays and documents:
  - `workapps(id uuid pk, tenant_id uuid not null, workspace_id uuid not null references workspaces(id) on delete restrict, name text not null, slug text not null, icon text, description text, status text not null check (status in ('draft','published','archived')), published_version int null, version bigint not null default 1, created_by uuid not null references users(id) on delete restrict, created_at, updated_by uuid not null references users(id) on delete restrict, updated_at, deleted_at)`.
  - `workapp_pages(id uuid pk, tenant_id uuid not null, app_id uuid not null references workapps(id) on delete cascade, title text not null, kind text not null check (kind in ('sheet','form','report','dashboard','dynamic-view','text')), source_id uuid null, body text null, position smallint not null, unique (id, app_id))`; the `visible_to_roles uuid[]` column is gone.
  - `workapp_page_roles(tenant_id uuid not null, page_id uuid not null references workapp_pages(id) on delete cascade, role_id uuid not null references workapp_roles(id) on delete cascade, primary key (page_id, role_id))` replaces `workapp_pages.visible_to_roles`; a visibility row cannot outlive either the page or the role, so both foreign keys cascade.
  - `workapp_roles(id uuid pk, tenant_id uuid not null, app_id uuid not null references workapps(id) on delete cascade, name text not null, default_landing_page_id uuid not null, foreign key (default_landing_page_id, app_id) references workapp_pages(id, app_id) on delete restrict deferrable initially deferred, unique (id, app_id))`; the `members jsonb` column is gone and the landing page is now a declared reference that must belong to the same app, deferred so `replace_pages` and `replace_roles` can run in either order inside one `UnitOfWork`.
  - `workapp_role_members(tenant_id uuid not null, role_id uuid not null references workapp_roles(id) on delete cascade, member_kind text not null check (member_kind in ('user','group')), user_id uuid null references users(id) on delete cascade, group_id uuid null references groups(id) on delete cascade, added_at timestamptz not null default now(), check ((member_kind = 'user') = (user_id is not null)), check ((member_kind = 'group') = (group_id is not null)), unique nulls not distinct (role_id, user_id, group_id))` replaces `workapp_roles.members jsonb`; a membership row cannot outlive its role, its user, or its group.
  - `workapp_versions(id uuid pk, tenant_id uuid not null, app_id uuid not null references workapps(id) on delete restrict, version_number int not null, name text not null, slug text not null, icon text, description text, note text, created_by uuid not null references users(id) on delete restrict, created_at, unique (id, version_number))`; the `manifest jsonb` column is replaced by the four snapshot child tables below, and the app metadata the snapshot must replay verbatim (`name`, `slug`, `icon`, `description` as they stood at publish time) moves into typed columns.
  - `workapp_version_pages(version_id uuid not null references workapp_versions(id) on delete cascade, page_id uuid not null, title text not null, kind text not null check (kind in ('sheet','form','report','dashboard','dynamic-view','text')), source_id uuid null, body text null, position smallint not null, primary key (version_id, page_id), unique (version_id, position))`; `page_id` and `source_id` are historical identifiers copied at publish time, deliberately carrying no foreign key so an immutable snapshot survives deletion of the draft page or of the embedded source — `filter_for_viewer` resolves them live and marks a missing source `unavailable`, which is the FR-F051-05 and section 7 behaviour.
  - `workapp_version_roles(version_id uuid not null references workapp_versions(id) on delete cascade, role_id uuid not null, name text not null, default_landing_page_id uuid not null, primary key (version_id, role_id), unique (version_id, lower(name)), foreign key (version_id, default_landing_page_id) references workapp_version_pages(version_id, page_id) on delete restrict)`.
  - `workapp_version_page_roles(version_id uuid not null, page_id uuid not null, role_id uuid not null, primary key (version_id, page_id, role_id), foreign key (version_id, page_id) references workapp_version_pages(version_id, page_id) on delete cascade, foreign key (version_id, role_id) references workapp_version_roles(version_id, role_id) on delete cascade)` is the table `GET /apps/{slug}` joins to filter pages.
  - `workapp_version_role_members(version_id uuid not null, role_id uuid not null, member_kind text not null check (member_kind in ('user','group')), user_id uuid null references users(id) on delete cascade, group_id uuid null references groups(id) on delete cascade, foreign key (version_id, role_id) references workapp_version_roles(version_id, role_id) on delete cascade, check ((member_kind = 'user') = (user_id is not null)), check ((member_kind = 'group') = (group_id is not null)), unique nulls not distinct (version_id, role_id, user_id, group_id))` is the table the viewer route joins to decide which roles a caller holds.
- `jsonb` audit (decision section 2): the module keeps no `jsonb` column. `workapp_roles.members` was queried by member ID on every `/apps/{slug}` request (the former GIN index proves it) and is now `workapp_role_members` with real user and group foreign keys. `workapp_versions.manifest` was not a replay-only blob: the viewer route filters its pages by role and enforces permissions on it, and the builder diffs two of them, so it becomes `workapp_version_pages`, `workapp_version_roles`, `workapp_version_page_roles`, and `workapp_version_role_members`. Per-widget display settings stay `jsonb` where they belong, on the F023 dashboard the page embeds; this feature stores no settings payload of its own. Audit diffs remain in the F003 `audit_events` table, unchanged.
- Behaviour preserved across the normalization: `SetPagesRequest`, `SetRolesRequest`, `WorkAppResponse`, `PublishResponse`, and `ViewerManifestResponse` keep `visible_to_roles` as an array, `members` as an array of `{ kind, id }`, and the version snapshot as a nested `manifest` object; the repositories fan those sets out to rows on write (`delete` of removed rows plus `insert ... on conflict do nothing`, in the enclosing `UnitOfWork`) and reassemble them on read, so OpenAPI, the generated client, and every stored version replay byte-identically.
- Invariants: unique `workapps(tenant_id, lower(slug)) where deleted_at is null`; unique `workapp_pages(app_id, position)`; unique `workapp_roles(app_id, lower(name))`; unique `workapp_versions(app_id, version_number)`; check `(kind = 'text' and body is not null and source_id is null) or (kind <> 'text' and source_id is not null)` on `workapp_pages` and on `workapp_version_pages`; `published_version` must exist in `workapp_versions` (deferred foreign key on `(app_id, version_number)`); page visibility is exactly the `workapp_page_roles` rows, whose primary key blocks a duplicate grant and whose role foreign key replaces the old application-level check that a `visible_to_roles` element referenced a role of the same app; role membership is exactly the `workapp_role_members` rows, whose `unique nulls not distinct (role_id, user_id, group_id)` blocks a repeated member and whose paired checks force exactly one of `user_id`/`group_id` to match `member_kind`; `workapp_roles.default_landing_page_id` must be a page of the same app, and `workapp_version_roles.default_landing_page_id` must be a page of the same snapshot; a snapshot row set is immutable — repositories insert it once at publish and never update it.
- Indexes: `workapps(tenant_id, workspace_id, status)`, `workapps(tenant_id, slug)`, `workapp_pages(app_id, position)`, `workapp_page_roles(role_id, page_id)` for the "which pages does this role see" lookup that the former array scan served, `workapp_role_members(user_id) where user_id is not null` and `workapp_role_members(group_id) where group_id is not null` for the draft-side member lookup that replaces the GIN index on `workapp_roles(members)`, `workapp_versions(app_id, version_number desc)`, `workapp_version_pages(version_id, position)`, `workapp_version_page_roles(version_id, role_id)` for the viewer filter, and `workapp_version_role_members(version_id, user_id)` plus `workapp_version_role_members(version_id, group_id)` for resolving roles held on `GET /apps/{slug}`.
- Audit events: `workapp.create`, `workapp.update`, `workapp.pages.set`, `workapp.roles.set`, `workapp.publish`, `workapp.archive` with diffs listing page and role IDs and titles.
- Retention/deletion: soft delete on `workapps`; versions and their snapshot rows are immutable and retained for the app's life; purge via F027 job, which deletes snapshot children before their version and page/role children before their parents; rollback drops the ten tables in that same child-before-parent order.

### React/TypeScript

- Routes: `/apps/:slug`, `/apps/:slug/:pageId`, `/w/:workspaceId/workapps`, `/w/:workspaceId/workapps/new`, `/w/:workspaceId/workapps/:id` (tabs `pages`, `roles`, `versions`) in `apps/web/src/features/workapps/`; components `AppShell`, `AppNav`, `AppPage`, `PageFrame` (dispatches to `SheetEmbed`, `FormEmbed`, `ReportEmbed`, `DashboardEmbed`, `DynamicViewEmbed`, `TextPage`), `AppSwitcher`, `AppBuilderPage`, `PageListEditor`, `PageSourcePicker`, `RoleEditor`, `MemberPicker`, `PreviewAsRole`, `PublishDialog`, `VersionList`, `VersionDiff`, `NewAppDialog`.
- State: TanStack Query keys `['workapp', id]`, `['workapps', workspaceId, cursor]`, `['app-manifest', slug]`, `['workapp-versions', id]`; publish invalidates `['app-manifest', slug]`; embeds reuse the source features' own query keys and components so permissions and caching stay theirs.
- API client: generated `WorkAppsApi` with `listApps`, `createApp`, `getApp`, `updateApp`, `setPages`, `setRoles`, `publish`, `getViewerManifest`; module gate through `useModuleAllowed('workapps')`.
- Optimistic updates: page reorder applies locally and rolls back on `conflict` with the stale banner; publish is never optimistic.
- Telemetry: `workapp_created`, `workapp_pages_saved`, `workapp_roles_saved`, `workapp_published`, `workapp_restored_version`, `workapp_opened`, `workapp_page_viewed`, `workapp_page_denied` with `app_id`, `slug`, `version_number`, `page_kind`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F051-01 through FR-F051-13 in `testing/features/F051/requirements/cases.md`
- [ ] Failure/edge-case tests: duplicate slug, 51 pages, source of wrong kind, landing page not visible to role, publish with zero roles, restore unknown version, archived app slug
- [ ] Permission-negative and tenant-isolation tests: no-role viewer `not_found`, non-admin mutation `denied`, cross-tenant slug `not_found`, page source the viewer cannot read renders denied, not-entitled tenant `denied`
- [ ] Rust unit tests: `validate_manifest` and `filter_for_viewer` tables, slug parsing, version numbering
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: slug uniqueness, position uniqueness, text/source check, version uniqueness, cascade, rollback; child tables `workapp_page_roles` duplicate grant rejected and cascade on page and role delete, `workapp_role_members` duplicate member rejected and `member_kind` mismatched with `user_id`/`group_id` rejected, `workapp_roles.default_landing_page_id` from another app rejected, `workapp_version_roles.default_landing_page_id` outside the snapshot rejected, `workapp_version_page_roles` orphan rejected, and no `jsonb` column present in the module
- [ ] React component tests: `AppShell`, `AppNav`, `PageFrame`, `PageListEditor`, `RoleEditor`, `PublishDialog` states
- [ ] Browser E2E tests: build app, publish, vendor role sees two pages, restore version
- [ ] Accessibility tests: axe on shell and builder, keyboard reorder, nav current state
- [ ] Performance/load tests: manifest p95 < 300 ms at 50 pages/20 roles, shell render < 500 ms

### Fast fanout configuration

- Test harness path: `testing/features/F051/`
- Feature flag: `F051_FEATURE`
- Fixture/seed factory: `testing/fixtures/workapps.rs` builds tenant A (app admin, procurement user, vendor user, member with no role), tenant B, one sheet, one published form, one report, one dashboard, one dynamic view, group `Vendors`, and a draft app with four pages and two roles; entitlement `workapps` active with `max_apps 5`, `max_pages_per_app 50`
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC
- Mock/stub contracts: outbox publisher recorded in memory; `SourceResolver` real against fixture rows; F048 evaluator real with fixture entitlement; source feature endpoints real for embed permission tests
- Parallel isolation: one schema per test worker, tenant ID per test
- Targeted command: `cargo xtask test-feature F051`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F051/`

## 6. Acceptance criteria

```gherkin
Feature: WorkApps composition and role experiences

Scenario: Publish an app and serve a role-filtered manifest
  Given a draft app "Vendor onboarding" with four pages and roles Procurement (all pages) and Vendor (Intake form, My vendors)
  When the app admin publishes it with note "Initial release"
  Then workapp_versions has version 1 with four workapp_version_pages and two workapp_version_roles rows, published_version is 1, and workapp.published.v1 is in the outbox
  And a Vendor-role user requesting GET /apps/vendor-onboarding receives the two pages joined through workapp_version_page_roles with landing page Intake form

Scenario: Embedded surface does not widen access
  Given the Vendor role can see page "Status board" whose sheet the vendor user cannot read
  When the vendor opens that page
  Then the sheet rows request returns 404 from the sheets API and the page frame shows the denied state

Scenario: Member without a role cannot open the app
  Given a workspace member who holds no app role
  When they request GET /apps/vendor-onboarding
  Then the response is 404 not_found

Scenario: Draft edits do not change the published app
  Given version 1 is published
  When the admin replaces the pages in the draft without publishing
  Then GET /apps/vendor-onboarding still returns the version 1 pages and the draft shows draft_dirty true
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F013 (views and sheet embeds), F014 (published forms), F023 (dashboards; reports via F021 through F023's dependency), F048 (`RequireModule`, limits, `useModuleAllowed`); decisions sections 2–4, 6, 10; contracts row F051
- Blocks: none
- Conflicts with: none (disjoint owned paths)
- External dependencies: none
- Risks and mitigations: a manifest could reference a source deleted later, so `filter_for_viewer` marks pages whose source is soft-deleted as `unavailable` and the shell shows an empty state instead of an error; proxying source data through the app would create a second permission path, so the shell embeds native components and the harness asserts every embed request hits the source endpoint with the viewer's session; slug collisions across workspaces in a tenant are prevented by the tenant-wide unique index.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F013, F014, F023, and F048 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F051/`
- [ ] Migration file name and owned paths claimed
- [ ] `workapps` module registered in F048 `ModuleSlug` with limits `max_apps`, `max_pages_per_app`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F051_FEATURE` (routes unmounted, `/apps/{slug}` not-found), run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- App admins can compose WorkApps from sheets, forms, reports, dashboards, and dynamic views, assign pages to roles, and publish versioned apps at `/apps/{slug}`; viewers see only their role's pages under their own permissions.
- Migration adds `workapps`, `workapp_pages`, `workapp_page_roles`, `workapp_roles`, `workapp_role_members`, `workapp_versions`, `workapp_version_pages`, `workapp_version_roles`, `workapp_version_page_roles`, and `workapp_version_role_members`; rollback drops them children first. Feature is off by default behind `F051_FEATURE` and requires the `workapps` entitlement.
