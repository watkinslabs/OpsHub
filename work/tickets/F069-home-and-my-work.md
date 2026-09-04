---
id: F069
type: feature
status: planned
priority: P1
owner: platform
estimate: 5
target_milestone: M2
parent_epic: E003
depends_on: [F005, F006, F013]
blocks: []
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/home/**, crates/persistence/src/home/**, services/api/src/home/**, services/worker/src/home/**, apps/web/src/features/home/**, services/api/migrations/*_home_*.sql, testing/features/F069/**]
feature_flag: F069_FEATURE
flag_default: off
branch: f069-home-and-my-work
started_at: null
finished_at: null
---

# F069 — Home and my work

## 1. Identity and dates

- Branch: `f069-home-and-my-work`
- Capability area: work management and views (spec 5.1 WORK-05 permission-aware surfaces; 5.4b sharing and follow-up; design principle "the product opens on the user's own work")
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 6; `docs/capability-contracts.md` row F069; `docs/authorization-model.md` sections 2 and 3.1
- Aggregate: `home`
- Module slug: `home`

## 2. Requirement specification

### Problem and user outcome

OpsHub has sixty screens and no front door. Every route is `/w/...` or `/admin/...`, so a user who signs in lands on whatever their browser remembered, or on nothing. There is no answer to "what is mine, what is late, where was I yesterday", and there is nowhere to pin the four sheets a person actually lives in. A new user sees an empty shell with no instruction at all.

As a member, I want one landing surface that shows what is assigned to me and due soon, what is waiting on my decision, where I was last, what I pinned, and who mentioned me, all filtered to what I may see and all in a single request, so that signing in puts me one click from my own work instead of leaving me to navigate a tree.

### Functional requirements

- **FR-F069-01:** `GET /api/v1/home` answers with one envelope `{ generated_at, budget_ms, onboarding, sections }` in one round trip. `sections` is a fixed, ordered list of five keys — `assigned`, `approvals`, `mentions`, `recents`, `favorites` — each carrying `title`, `state`, `empty_reason`, `cap`, `truncated`, and `items`. Caps are `assigned` 10, `approvals` 10, `mentions` 10, `recents` 12, `favorites` 20, so a response holds at most 62 items and `truncated` says whether the underlying set was larger. The route takes no `cursor`, `filter`, or `sort`: paging a section means opening that section's own route.
- **FR-F069-02:** Sections come from a registry of `HomeSectionProvider` implementations keyed by section key, built once at start-up. `favorites` and `recents` are provided by this feature. `assigned`, `approvals`, and `mentions` are slots that the feature owning the source aggregate registers — F020 for approvals, F016 for mentions, F010 for assigned rows — and a slot with no registered provider returns `state: "unavailable"` with no items so the client renders nothing rather than an error. The aggregator runs every registered provider concurrently under a 150 ms per-provider timeout; a provider that times out or fails returns `state: "degraded"` with the request `correlation_id` and never fails the whole response.
- **FR-F069-03:** Every item is permission-filtered before it leaves the server. After the providers return, the aggregator groups the candidate targets by `target_kind` and calls `TargetResolver::resolve_readable(kind, ids, actor)` once per kind — at most eight statements for the whole response regardless of item count, and never one statement per item, per sheet, or per row. A target the caller may not read is dropped silently; the response never distinguishes "does not exist", "was deleted", and "you may not see it", and never returns a count of what was dropped.
- **FR-F069-04:** `GET /api/v1/favorites` returns the caller's own favourites, newest first, with cursor pagination and `limit` 1–100 (default 20). `filter=available` (default) returns only entries whose target resolves and is readable now; `filter=unavailable` returns entries whose target does not, each carrying `state: "unavailable"`, the stored `label_cache`, and no `path`, so the user can remove a dead pin. `fields` selects a projection per the catalog conventions.
- **FR-F069-05:** `POST /api/v1/favorites` with `{ target_kind, target_id }` pins a target for the caller. `target_kind` is one of `workspace`, `folder`, `sheet`, `row`, `view`, `dashboard`, `report`, `document`. The caller must be able to read the target now, and a caller who cannot gets `not_found`. A second pin of the same target returns `conflict` with the existing `id`; the 201st favourite returns `conflict` with `field_errors.limit`. Mutations carry `Idempotency-Key`, return `version`, and publish `favorite.added.v1`.
- **FR-F069-06:** `DELETE /api/v1/favorites/{id}` removes the caller's own favourite under `If-Match: <version>`, publishes `favorite.removed.v1`, and returns `not_found` for an id belonging to another user or another tenant. Removing a favourite whose target is unavailable succeeds, because that is the only way to clear one.
- **FR-F069-07:** Recents are implicit. A tower layer records a visit when a request for `GET /api/v1/sheets/{id}`, `GET /api/v1/rows/{id}`, `GET /api/v1/views/{id}`, or `GET /api/v1/workspaces/{id}/tree` returns `2xx`. The layer pushes `(tenant_id, user_id, target_kind, target_id)` onto a bounded in-process channel of 4,096 entries and returns; a flusher drains every 5 s and upserts one batch. Recording never blocks, never fails, and never changes the status of the request it observed; a full channel drops the visit and increments `home_visits_dropped_total`. A repeat visit to the same target within 60 s is coalesced into the existing row rather than counted again.
- **FR-F069-08:** `GET /api/v1/recents` returns the caller's own recent targets, most recently visited first, with `last_visited_at`, `visit_count`, cursor pagination and `limit` 1–100 (default 12), permission-filtered by FR-F069-03. Each user keeps at most 100 recent rows; the flusher trims the oldest beyond that in the same transaction as the upsert.
- **FR-F069-09:** A favourited or recent target that is soft-deleted, archived, moved into a folder the caller cannot read, or unshared disappears from `GET /api/v1/home`, from `GET /api/v1/recents`, and from the default favourites list on the next read, because resolution happens per request and is never cached across requests. The stored rows behave differently by kind: a recent row is deleted by the prune job once its target no longer resolves for anyone, and a favourite row is kept and hidden, so restoring the target or regaining access brings the pin back exactly as it was.
- **FR-F069-10:** The hourly worker job `home.prune` deletes `recent_items` rows older than 90 days, deletes `favorites` and `recent_items` rows whose target has been purged, resolving in batches of 500 ids per `target_kind`, and refreshes `label_cache` for rows whose resolved label has changed. It is idempotent, resumable, and bounded to 10,000 rows per run.
- **FR-F069-11:** Both surfaces are private to one person. Every named query in this module takes `user_id` from the request context and none omits it, so no role — `tenant-admin` included — can read or write another user's favourites or recents through any route here. The `self` principal kind of `docs/authorization-model.md` section 2 governs the rows; `viewer` on the target is the entitlement a pin implies and the only one it grants.
- **FR-F069-12:** A brand-new user gets a real first screen. `onboarding.state` is `new` when the caller has no favourites, no recents, and every registered section is empty, otherwise `returning`. When it is `new`, `onboarding.suggestions` carries up to three readable workspaces from `GET /api/v1/workspaces`, plus `create_sheet` when the caller may create a sheet in one of them, plus `request_access` when the caller can read no workspace at all. A section that is empty says why through `empty_reason`: `none_yet`, `all_clear`, or `no_access`, so a viewer with no access reads "ask an administrator for access" rather than "create your first sheet".
- **FR-F069-13:** Home is the application's index route. Signing in lands on `/`, the rail's product mark links to it, and the previous behaviour of restoring the last visited route is replaced by home plus the recents section.
- **FR-F069-14:** Errors map to the six-code vocabulary only: an unknown `target_kind` or a malformed body is `invalid`; a target the caller cannot read, a favourite of another user, and a cross-tenant id are all `not_found`; a duplicate pin or the 200-favourite limit is `conflict`; more than 60 favourite mutations per user per minute is `rate_limited`; a registry with no providers at all is still a `200` with five `unavailable` sections, never `unavailable` as a status.

### Non-functional requirements

- **NFR-F069-01 Performance:** `GET /api/v1/home` is under 400 ms p95 and 800 ms p99 server time for a user with 200 favourites, 100 recents, and five registered providers, measured with a warm pool and a cold cache. The response costs at most 13 statements — one per registered provider plus one `resolve_readable` per distinct `target_kind` — and that count does not grow with the number of items, sheets, or rows involved. `GET /api/v1/favorites` and `GET /api/v1/recents` are under 150 ms p95. Visit recording adds under 1 ms to the observed request at p99.
- **NFR-F069-02 Security/privacy:** every query carries a `tenant_id` and a `user_id` predicate; the response body, the error bodies, and the telemetry events never name a target the caller cannot read; an unavailable favourite exposes only the label the caller already saw when pinning it, never a fresh read of the target; cross-tenant and cross-user negatives are part of the harness, and the prune job runs under a job context that has no tenant data access beyond the two tables this feature owns.
- **NFR-F069-03 Accessibility:** the home route passes axe with zero serious or critical violations in both themes and both densities; each section is a labelled region reachable by heading navigation; the favourite control is a toggle button with an accessible name that states the target and the resulting action, and its state is never conveyed by colour or icon fill alone; the empty state is announced once on load, not per section.
- **NFR-F069-04 Reliability/observability:** the flusher survives restart with at most one 5 s window of dropped visits, which is acceptable because a recent is advisory; metrics `home_request_duration_seconds`, `home_section_duration_seconds{section}`, `home_section_state_total{section,state}`, `home_visits_recorded_total`, `home_visits_dropped_total`, `home_prune_rows_total{table,reason}`; every request and job runs in a tracing span carrying `tenant_id`, `actor_id`, `correlation_id`, and the section key.

### Scope

Included: the home aggregation route and its envelope, the section provider registry with per-provider timeout and degradation, batched permission-filtered target resolution, explicit per-user favourites with their two tables' repository classes, implicit per-user recents with the recording layer and flusher, target lifecycle handling for deleted, archived, moved, and unshared targets, the prune job, the onboarding and per-section empty states, the home screen and the reusable favourite toggle.

Excluded: the approvals, mentions, and assigned-rows providers themselves, which belong to F020, F016, and F010 and register against the trait defined here; notification inbox and digests (F037); global search (F010); the workspace tree and folder navigation (F005); saved views and their sharing (F013); trash and restore (F070); dashboards as a configurable surface (F023); per-user dashboards or widget layout of any kind.

## 3. UX specification

- Entry points: route `/` is home and is the post-sign-in landing route; the OpsHub mark in the top bar returns to it; the favourite toggle appears in the header of every sheet, view, dashboard, report, and document surface through the shared component this feature exports.
- Primary flow: Priya signs in and lands on home. `Assigned to me` lists six rows with due dates, two of them overdue and marked with text plus an icon; `Waiting on you` lists two approvals; `Recently visited` lists the seven records she touched yesterday; `Favourites` lists the four sheets she pinned. She clicks `Cutover plan`, works, returns to home, and it is now first under `Recently visited`. She clicks the star in the sheet header of `Vendor reviews`; it becomes filled and the sheet appears under `Favourites` without a page reload.
- Empty state: a brand-new user sees one centred panel, not five empty cards — a heading, one line explaining that home fills in as work is assigned and visited, and up to three workspace buttons plus `Create a sheet`. A user who can read no workspace sees `Ask an administrator for access` and no create action.
- Loading: one skeleton per section, laid out at the final height so nothing shifts when data arrives. Error: a section that returned `degraded` renders in place with a retry action and the `correlation_id`; the rest of the page still renders. Denied: no denied page exists for home, because home is readable by any authenticated user and simply shows less. Stale: pinning against a removed target shows `That item is no longer available` and removes the row. Offline: pin and unpin are disabled with an offline badge; the last home payload is rendered from cache with an offline banner. Success: pinning shows a toast with an undo action for 5 s.
- Unavailable favourites: shown only under `Favourites → Show unavailable`, greyed, with the cached label, no link, and a `Remove` action.
- Responsive: three columns above 1,280 px, two between 900 and 1,280 px, one below; sections keep their order in every layout so the tab order matches the reading order.
- Keyboard: sections are `section` landmarks with `h2` headings; `g h` returns to home from anywhere; the favourite toggle is reachable in the header tab sequence and announces `Added to favourites` through a polite live region.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for dates and counts (F062); icons `Star`, `Clock`, `Check`, `Warn`, `User`, `Grid` from the shared registry at 16 and 20 px; every colour, space, and radius from `apps/web/src/design/tokens.css`.
- Design: `design/artboards/Home.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

### Rust backend

- Data access (decision 2.1): `crates/persistence/src/home/` holds `FavoriteRepository` (owns `favorites`) and `RecentItemRepository` (owns `recent_items`); each table is written by exactly one of them and by no other feature. Both implement the shared `Repository` contract (`get`, `list` with cursor pagination, `insert`, `update` under an expected version, `soft_delete`, `restore`, `purge`), so the tenant predicate, soft-delete filter, version check, audit row, and outbox enqueue come from the base contract. Named queries: `FavoriteRepository::list_for_user(user_id, cursor, limit)`, `find_for_user(user_id, target_kind, target_id)`, `count_for_user(user_id)`, `delete_own(user_id, id, version)`, `refresh_label(id, label)`, `list_by_target(target_kind, ids)`; `RecentItemRepository::list_for_user(user_id, cursor, limit)`, `record_visits(batch)`, `trim_to_newest(user_id, 100)`, `delete_older_than(cutoff)`, `list_by_target(target_kind, ids)`, `refresh_label(user_id, target_kind, target_id, label)`. No generic query escape hatch exists. The aggregator, the providers, the handlers, the visit layer, and the prune job depend on these traits and contain no SQL; the flusher's upsert and trim run in one `UnitOfWork` that owns the transaction, as do the pin and unpin paths with their audit and outbox rows.
- Reads of other aggregates go through the repository class that already owns the table — `WorkspaceRepository::list_visible_to` for the onboarding suggestions, `SheetRepository`, `RowRepository`, and `ViewRepository::list_visible_to` behind their `TargetResolver` implementations — so this module opens no connection to a table it does not own and adds no second writer to one.
- Domain entities in `crates/domain/src/home/`: `Favorite { id, tenant_id, user_id, target: TargetRef, label_cache, version, created_by, created_at, updated_by, updated_at, deleted_at }`, `RecentItem { tenant_id, user_id, target: TargetRef, label_cache, visit_count, last_visited_at }`, `TargetRef { kind: TargetKind, id }` with `TargetKind` a closed enum of the eight kinds, `TargetSummary { label, path, state: Live | Unavailable }`, `HomeItem { target, label, path, badge, due_at, actor, occurred_at, favorite_id }`, `HomeSection { key: SectionKey, title, state: Ready | Empty | Degraded | Unavailable, empty_reason, cap, truncated, items }`, `Onboarding { state, suggestions }`.
- Traits in `crates/domain/src/home/registry.rs`: `HomeSectionProvider { fn key(&self) -> SectionKey; fn cap(&self) -> usize; async fn load(&self, ctx: &HomeContext) -> Result<Vec<HomeItem>, HomeError>; }` and `TargetResolver { fn kind(&self) -> TargetKind; async fn resolve_readable(&self, ids: &[Uuid], actor: &ActorContext) -> Result<HashMap<Uuid, TargetSummary>, HomeError>; }`. `HomeRegistry` is built at start-up from the providers and resolvers each feature registers; a missing provider is a state, never a panic, and a missing resolver for a kind drops every item of that kind.
- Use cases in `crates/domain/src/home/service.rs`: `load_home`, `list_favorites`, `add_favorite`, `remove_favorite`, `list_recents`, `record_visits`, `prune_home`. `load_home` runs registered providers concurrently under a 150 ms timeout each, unions their `TargetRef`s, calls one resolver per distinct kind, drops unresolved items, truncates to each cap, and computes `onboarding` from the result plus `WorkspaceRepository::list_visible_to`.
- API endpoints (`services/api/src/home/`): `GET /api/v1/home`, `GET /api/v1/favorites`, `POST /api/v1/favorites`, `DELETE /api/v1/favorites/{id}`, `GET /api/v1/recents`. DTOs `HomeResponse { generated_at, budget_ms, onboarding, sections }`, `HomeSectionDto`, `HomeItemDto`, `OnboardingDto { state, suggestions }`, `FavoriteResponse { id, target_kind, target_id, label, path, state, created_at, version }`, `CreateFavoriteRequest { target_kind, target_id }`, `RecentResponse { target_kind, target_id, label, path, visit_count, last_visited_at }`, `Page<FavoriteResponse>`, `Page<RecentResponse>`.
- Visit recording: `services/api/src/home/visit_layer.rs` defines `RecentVisitLayer`, a tower layer mounted on the versioned router beside the other feature routers. It matches the four observed routes, ignores every non-`2xx` response, and pushes onto a bounded channel; `services/worker/src/home/flusher.rs` drains it every 5 s and calls `record_visits` then `trim_to_newest`.
- Worker jobs (`services/worker/src/home/`): `flusher` (every 5 s) and `prune` (hourly), both registered in the worker registry behind the flag.
- Events: `favorite.added.v1` and `favorite.removed.v1` through the outbox, each carrying the standard payload `{ tenant_id, actor_id, aggregate_id, version, changed_fields, correlation_id, occurred_at }` with `aggregate_id` the favourite id. Recents publish nothing; a visit is not a domain change.
- Authorization: any authenticated principal may call `GET /api/v1/home` and read their own two lists; `viewer` on the target is required to pin it, checked through `authz::require(&ctx, Permission::Read, ResourceRef)`; `self` is the principal kind that owns the rows, so ownership is checked in the repository predicate and not left to the handler.
- Validation: `target_kind` in the eight-kind enum, `target_id` a UUID, `limit` 1–100, `filter` in `available` or `unavailable`, favourites per user ≤ 200, recents per user ≤ 100, `label_cache` ≤ 200 chars truncated on write.
- Error mapping: `HomeError::UnknownTargetKind` and `::InvalidCursor` map to `invalid`; `::TargetNotReadable`, `::NotOwned`, and `::Missing` map to `not_found`; `::AlreadyFavorited` and `::FavoriteLimit` map to `conflict`; `::RateLimited` maps to `rate_limited`; `::ProviderTimeout` maps to no status at all because it degrades one section inside a `200`.

### PostgreSQL/SQLx

- Migration `*_home_*.sql` creates `favorites(id uuid pk, tenant_id uuid not null references tenants(id) on delete restrict, user_id uuid not null references users(id) on delete cascade, target_kind text not null check (target_kind in ('workspace','folder','sheet','row','view','dashboard','report','document')), target_id uuid not null, label_cache text not null, version bigint not null default 1, created_by uuid not null, created_at timestamptz not null, updated_by uuid, updated_at timestamptz not null, deleted_at timestamptz)` and `recent_items(tenant_id uuid not null references tenants(id) on delete restrict, user_id uuid not null references users(id) on delete cascade, target_kind text not null check (target_kind in ('workspace','folder','sheet','row','view','dashboard','report','document')), target_id uuid not null, label_cache text not null, visit_count integer not null default 1 check (visit_count > 0), first_visited_at timestamptz not null, last_visited_at timestamptz not null, primary key (tenant_id, user_id, target_kind, target_id))`.
- Normalization (decision 2): both tables are already third normal form and hold no repeating group and no delimited list. `target_kind` is a closed enum whose members carry no data, so it stays a `text` column with a check constraint rather than a lookup table, exactly as decision 2 prescribes; adding a ninth kind is a migration and a resolver, in one change. There is no `jsonb` column in this module: everything home stores is filtered, sorted, or constrained on — kind, id, user, timestamps, counts — and none of it is a schema-less payload, so none of it qualifies.
- The reference to the target is deliberately polymorphic and therefore has no foreign key: the eight kinds live in six different features' tables and a favourite must not force a write dependency between them. Integrity is a read-time property instead, held by `TargetResolver` per FR-F069-03 and swept by `home.prune` per FR-F069-10, and `label_cache` is a derived, rebuildable cache — never a source of truth — that serves the unavailable-favourites list and is rebuilt by that same job.
- Invariants: partial unique index `favorites_user_target_idx on (tenant_id, user_id, target_kind, target_id) where deleted_at is null` so one person cannot pin one target twice; the `recent_items` primary key gives the same guarantee for visits and makes the upsert a single `insert ... on conflict do update`; `check (last_visited_at >= first_visited_at)`; the 200-favourite and 100-recent caps are enforced by `count_for_user` inside the pin transaction and by `trim_to_newest` inside the flush transaction respectively.
- Indexes: `favorites(tenant_id, user_id, created_at desc) where deleted_at is null` for the list and the home section, `favorites(tenant_id, target_kind, target_id)` for the prune sweep and for `list_by_target`, `recent_items(tenant_id, user_id, last_visited_at desc)` for the list and the home section, `recent_items(tenant_id, target_kind, target_id)` for the sweep, `recent_items(last_visited_at)` for the 90-day deletion.
- Audit events: `favorite.add` and `favorite.remove` with the target kind and id; visits are not audited, because auditing every read of every sheet would double the write volume of the product for a surface that is advisory.
- Retention/deletion: recents older than 90 days are deleted by `home.prune`; both tables cascade on user delete, so a departing user takes their private surfaces with them; a purged target removes matching rows in both tables; rollback drops the two tables and their five indexes.

### React/TypeScript

- Routes: `/` in `apps/web/src/features/home/`; components `HomePage`, `HomeSectionCard`, `HomeItemRow`, `HomeEmptyState`, `HomeSkeleton`, `RecentsList`, `FavoritesList`, `FavoriteStar`. `FavoriteStar` is exported for other features to mount in their headers, so no feature reimplements the toggle.
- State: TanStack Query keys `['home']`, `['favorites', filter, cursor]`, `['recents', cursor]`; pinning optimistically updates `['home']` and `['favorites']` and rolls back on `conflict` or `not_found`, showing the stale message; `['home']` is refetched on window focus with a 30 s stale time so returning to the tab does not re-request on every focus.
- API client: generated `HomeApi` with `getHome`, `listFavorites`, `addFavorite`, `removeFavorite`, `listRecents`; no hand-written duplicate of a server type.
- States: each section renders loading, ready, empty with its `empty_reason` copy, degraded with `correlation_id` and retry, and offline, composed from the F062 pattern components rather than hand-rolled.
- Telemetry: `home_viewed{sections,items}`, `home_item_opened{section,target_kind,position}`, `favorite_added{target_kind}`, `favorite_removed{target_kind}`, `home_empty_state_shown{reason}`, `home_section_degraded{section}`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F069-01 through FR-F069-14 and NFR-F069-01 through NFR-F069-04 in `testing/features/F069/requirements/cases.md`
- [ ] Failure/edge-case tests: provider timeout, provider error, no providers registered at all, missing resolver for a kind, duplicate pin, 201st pin, pin of an unreadable target, unpin of another user's favourite, target soft-deleted between pin and read, target moved into an unreadable folder, visit channel full, flusher restart mid-batch
- [ ] Permission-negative and tenant-isolation tests: tenant-admin cannot read another user's favourites or recents, a user in tenant B cannot delete a tenant A favourite, an item the caller lost access to is absent from home, recents, and favourites without any count or marker revealing it
- [ ] Rust unit tests: `crates/domain/src/home/` registry composition, cap and truncation logic, onboarding state computation, empty-reason selection, 60 s visit coalescing
- [ ] API contract/integration tests: every route above with success and each mapped error code, cursor paging, `filter=unavailable`, idempotent replay of a pin
- [ ] Database migration/constraint tests: the two tables and five indexes, the partial unique index, the recents primary key upsert, the visit-count check, cascade on user delete, rollback
- [ ] React component tests: `HomePage` section states, `HomeEmptyState` for each reason, `FavoriteStar` toggle and rollback, `RecentsList` ordering
- [ ] Browser E2E tests: sign in and land on home, open a sheet and see it appear under recents, pin and unpin from a sheet header, first-run empty state
- [ ] Accessibility tests: axe on home in both themes and densities, landmark and heading structure, favourite toggle name and state, live-region announcement
- [ ] Performance/load tests: home p95 under 400 ms at full caps, statement count fixed at 13 regardless of item count, visit recording overhead under 1 ms p99

### Fast fanout configuration

- Test harness path: `testing/features/F069/`
- Feature flag: `F069_FEATURE`
- Fixture/seed factory: `testing/fixtures/home.rs` builds tenants A and B, a member with 200 favourites and 100 recents, a brand-new member with none, a viewer with no workspace access, three workspaces, four sheets with 50 rows each, two saved views, and stub providers for the `assigned`, `approvals`, and `mentions` slots whose latency and failure mode are programmable
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC, fixed pin ordering by seeded `created_at`
- Mock/stub contracts: `StubSectionProvider` and `StubTargetResolver` in `testing/harness/home/` returning fixed items with controllable delay and error; no test reaches the network
- Parallel isolation: one schema per test worker, one tenant per test, one in-process visit channel per test
- Targeted command: `cargo xtask test-feature F069`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F069/`

## 6. Acceptance criteria

```gherkin
Feature: Home and my work

Scenario: One request returns every section under its cap
  Given a member with 200 favourites, 100 recents, and five registered providers
  When they GET /api/v1/home
  Then the response carries five sections capped at 10, 10, 10, 12, and 20 items with truncated true
  And the request issued thirteen statements and completed under 400 ms

Scenario: A section whose provider is slow degrades alone
  Given the approvals provider is stubbed to take 400 ms
  When a member GETs /api/v1/home
  Then the approvals section has state degraded with a correlation_id and no items
  And the other four sections return their items and the status is 200

Scenario: Losing access removes an item from both surfaces without revealing it
  Given a member has favourited and recently visited the sheet "Vendor reviews"
  When their read access to that sheet is revoked
  Then home, GET /api/v1/recents, and GET /api/v1/favorites omit it with no count or marker
  And GET /api/v1/favorites with filter unavailable shows only the cached label with no path

Scenario: A brand-new user gets a first screen rather than five empty cards
  Given a member who has never opened a record and can read two workspaces
  When they GET /api/v1/home
  Then onboarding state is new with the two workspaces and create_sheet as suggestions
  And every section is empty with empty_reason none_yet

Scenario: Nobody else can read my home
  Given a tenant-admin in the same tenant
  When they GET /api/v1/favorites and GET /api/v1/recents
  Then they see only their own rows and never another user's
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F005 (workspaces and folders as favourite targets, and the readable-workspace query the onboarding suggestions use); F006 (sheets and rows as targets, and the observed read routes recents are recorded from); F013 (saved views as targets); decisions sections 2, 2.1, 3, 4, 6; contracts row F069
- Blocks: none
- Conflicts with: none (disjoint owned paths; this feature owns only `favorites` and `recent_items`)
- External dependencies: none; every provider and resolver is in-process
- Risks and mitigations: three of the five sections have no provider until M3, so home would look thin at release — mitigated by the registry returning `unavailable` and the client rendering only registered sections, and by the harness proving the envelope, caps, ordering, permission filter, and empty state today through stub providers; a polymorphic target reference cannot be enforced by a foreign key, so a purged target could leave an orphan row — mitigated by read-time resolution and the hourly sweep, and by never letting a stored row be the reason something is shown; the visit layer could add latency to every read in the product — mitigated by a bounded channel, a fire-and-forget push, and a measured p99 budget of 1 ms with a drop counter; a home request that fanned out per item would become the slowest route in the product — mitigated by the one-statement-per-kind resolver contract and a performance test that asserts the statement count rather than only the duration.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F005, F006, and F013 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F069/`
- [ ] Migration file name and owned paths claimed
- [ ] `design/artboards/Home.dc.html` reviewed against section 3

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Statement-count assertion holds at full caps and the visit-overhead budget is met
- [ ] Audit and outbox events verified for pin and unpin
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets`, `check-contracts`, `check-persistence`, `check-roles`, and `check-design` pass
- [ ] Rollback verified: disable `F069_FEATURE`, run the down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- OpsHub now opens on Home. One request returns assigned work due soon, approvals waiting on you, recently visited records, favourites, and mentions, each permission-filtered and capped, with a real first screen for new users. Records can be pinned from any surface, and recently visited records are remembered automatically; both are private to you and disappear the moment you lose access to the item.
- Migration adds `favorites` and `recent_items` with five indexes; rollback drops them. Feature is off by default behind `F069_FEATURE`.
