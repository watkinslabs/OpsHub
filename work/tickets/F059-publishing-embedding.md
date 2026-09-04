---
id: F059
type: feature
status: planned
priority: P1
owner: platform
estimate: 5
target_milestone: M7
parent_epic: E008
depends_on: [F013, F023, F036]
blocks: []
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/publishing/**, services/api/src/publishing/**, apps/web/src/features/publishing/**, services/api/migrations/*_publishing_*.sql, services/worker/src/publishing/**, testing/features/F059/**]
feature_flag: F059_FEATURE
flag_default: off
branch: f059-publishing-embedding
started_at: null
finished_at: null
---

# F059 — Publishing/embedding

## 1. Identity and dates

- Branch: `f059-publishing-embedding`
- Capability area: published and embedded views, reports, and dashboards (spec 5.1 "Published and embedded views use scoped, revocable access tokens, preserve permission filtering, and expose stale/error state"; 5.6 REPORT-03 sharing; section 10 "links expire within 30 days, are revocable, never grant tenant discovery, and cannot perform writes except through published forms or explicitly scoped views")
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 6, 7; `docs/capability-contracts.md` row F059
- Module slug: `publishing`

## 2. Requirement specification

### Problem and user outcome

Teams want to show a dashboard on a lobby screen, embed a status view in an intranet page, or send a report link to a customer who has no OpsHub account. Sharing (F036) grants identities; it does not produce a read-only, embeddable, revocable surface with clear staleness.

As a publisher, I want to publish a view, report, or dashboard as a scoped read-only artifact with an expiring, revocable token and optional embedding on allowed origins, so that outsiders see exactly what I am allowed to see, never more, and always know how fresh it is.

### Functional requirements

- **FR-F059-01:** An actor with the `publisher` role on a `view`, `report`, or `dashboard` can create a publication with `target: { kind, id }`, `title`, `access: link|tenant`, `expires_at` (≤ 30 days from now, default 30 days), `embed: { enabled, allowed_origins: [origin] ≤ 10 }`, `refresh_interval_s` (60–3600), and `show_freshness: bool`; the response returns UUIDv7 `id`, `version` 1, and a one-time plaintext `token`.
- **FR-F059-02:** Tokens are 32 random bytes, stored only as SHA-256 hashes in `publication_tokens` with `scope: { tenant_id, publication_id, target, read_only: true }`, and are never returned again after creation or rotation; `POST /api/v1/publications/{id}/rotate-token` issues a new token, expires the old one after a 10-minute grace period, and publishes `publication.updated.v1` with `changed_fields: ["token"]`.
- **FR-F059-03:** `GET /public/publications/{token}` renders the target read-only as the publisher's permission scope at render time, filtered by the target's own filters; if the publisher has lost read access or the target is deleted, the page renders the `error` state with `reason: publisher_access_lost|target_deleted` and no data.
- **FR-F059-04:** Public and embed responses never include row IDs beyond those needed for rendering, hidden columns, comments, attachments, or links to the tenant; navigation, search, and any mutation affordance are absent, and every write route rejects publication tokens with `denied`.
- **FR-F059-05:** Rendering is served from a snapshot refreshed by the worker every `refresh_interval_s`; the response carries `generated_at`, `source_versions`, and `stale: true` when the last refresh failed or is older than `2 × refresh_interval_s`; the stale state is shown in the page when `show_freshness` is true and always exposed in the `X-OpsHub-Stale` header.
- **FR-F059-06:** `access: tenant` requires an authenticated session in the same tenant and the target's read ACL in addition to the token; `access: link` requires only the token; a token used from a different tenant's session for `tenant` access returns `not_found`.
- **FR-F059-07:** `GET /embed/{token}` returns the same rendering inside an iframe-safe document with `Content-Security-Policy: frame-ancestors <allowed_origins>` and `X-Frame-Options` omitted; a request whose `Origin`/`Referer` is not in `allowed_origins` renders the `denied` state; `embed.enabled: false` returns `not_found`.
- **FR-F059-08:** `DELETE /api/v1/publications/{id}` revokes every token immediately, publishes `publication.revoked.v1`, and public and embed requests return `404 not_found` within 5 s; expired publications behave the same and show `reason: expired` in the audit view.
- **FR-F059-09:** `PATCH /api/v1/publications/{id}` with `If-Match` updates `title`, `access`, `expires_at` (still ≤ 30 days from now), `embed`, `refresh_interval_s`, `show_freshness`; a stale version returns `conflict`; every change publishes `publication.updated.v1`.
- **FR-F059-10:** Each public or embed render records a `publication_views` row with `viewed_at`, `access`, hashed client address, referrer origin, and `stale`, sampled to at most one row per token per minute, and publishes `publication.viewed.v1` at most once per token per 5 minutes.
- **FR-F059-11:** `GET /api/v1/publications` lists publications with cursor paging, filters `target_kind`, `target_id`, `status: active|expired|revoked`, and per-row `view_count_7d`, `last_viewed_at`, `expires_at`; only publications the actor could read the target for are visible.
- **FR-F059-12:** Public and embed routes are rate-limited to 60 requests per minute per token and 600 per minute per client address, returning `rate_limited` with `Retry-After`.
- **FR-F059-13:** The web app offers a `Publish` dialog on views, reports, and dashboards showing the token once with copy, embed snippet (`<iframe src="/embed/{token}">`), expiry, origins, and a `Rotate` and `Revoke` action; the publications list shows status and view counts.
- **FR-F059-14:** A publication token never grants tenant discovery: `/api/v1/*` routes reject it with `denied`, and the public page has no links into the app except an optional `Open in OpsHub` for `tenant` access.

### Non-functional requirements

- **NFR-F059-01 Performance:** public and embed renders respond in under 500 ms p95 from snapshot for dashboards with 12 widgets; snapshot refresh for a 10,000-row view completes in under 10 s p95.
- **NFR-F059-02 Security/privacy:** tokens stored hashed; scope checked in the domain service; permission filtering evaluated at refresh time with the publisher's scope; client addresses stored as salted hashes; no tenant identifiers in public HTML beyond the publication ID.
- **NFR-F059-03 Accessibility:** public and embed pages pass axe with zero serious violations, carry a document title and landmark, expose freshness as text, and honor reduced motion; the publish dialog is keyboard operable with focus trap.
- **NFR-F059-04 Reliability/observability:** refresh jobs are idempotent per `(publication_id, scheduled_at)`, retried 3 times, and dead-lettered; metrics `publication_render_total{access,stale}`, `publication_refresh_failures_total`, and `publication_token_rejected_total{reason}` are emitted with `correlation_id` on every render.

### Scope

Included: publication CRUD, hashed scoped tokens with rotation and revocation, public and embed rendering from worker-refreshed snapshots, stale and error states, origin-restricted embedding with CSP, view analytics, rate limits, publish dialog and list UI.

Excluded: published forms (F014 owns `/public/forms`), share links to identities (F036), public write-back through scoped views (F050 Dynamic View), export of published artifacts (F025), custom domains.

## 3. UX specification

- Personas: publisher (owner of a dashboard or view), external viewer without an account, intranet author embedding a status view, tenant admin auditing publications.
- Entry points: `Share` menu item `Publish` on view, report, and dashboard pages; workspace settings `Publications` list at `/w/{workspace_id}/publications`; public route `/public/publications/{token}`; embed route `/embed/{token}`.
- Primary flow: open a dashboard, choose `Publish`, pick `Anyone with the link`, keep 30-day expiry, enable embed with origin `https://intranet.example.com`, click `Publish`, copy the token URL and iframe snippet from the one-time panel, paste into the intranet; later rotate the token from the list and confirm the old link stops within 10 minutes.
- Loading: skeleton widgets in public page; Empty: `Nothing to show` when the target has no rows; Error: full-page state with reason text and no data; Success: toast `Published` and `Token rotated`; Stale: banner `Data as of 09:42, refresh failed` when `show_freshness`; Denied: embed on an unlisted origin shows `This embed is not allowed here`; Expired/Revoked: `This link is no longer available`; Offline (app side): publish actions disabled.
- Permission-denied: non-publishers do not see `Publish`; a publisher who lost target access sees the publication with an `Access lost` badge.
- Responsive: public page renders dashboards as a single column under 768 px and views as a card list under 640 px; embed page fills the iframe and posts its height through `postMessage` to the parent origin.
- Keyboard: publish dialog traps focus, `Escape` closes, token copy button announces `Copied`; public page supports `Tab` across widgets and `Enter` on nothing (no interactive elements except pagination); reduced motion disables refresh spinner.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide `Globe`, `Link2`, `RotateCw`, `Ban`, `Clock`; tokens from `apps/web/src/design/tokens.css` with a neutral public theme.

## 4. Technical specification

### Rust backend

- Canonical contract: aggregate `publication`; module `publishing`; routes `GET /api/v1/publications`, `POST /api/v1/publications`, `PATCH /api/v1/publications/{id}`, `DELETE /api/v1/publications/{id}`, `POST /api/v1/publications/{id}/rotate-token`, `GET /public/publications/{token}`, `GET /embed/{token}`; events `publication.created.v1`, `publication.updated.v1`, `publication.revoked.v1`, `publication.viewed.v1`; tables `publications`, `publication_tokens`, `publication_views`; mutation role `publisher`.
- Domain entities in `crates/domain/src/publishing/`: `Publication { id, tenant_id, workspace_id, target: PublishTarget, title, access: Access, expires_at, embed: EmbedSettings, refresh_interval_s, show_freshness, publisher_id, status, snapshot: Option<SnapshotMeta>, version, audit fields, revoked_at }`, `PublicationToken { id, publication_id, token_hash, scope: TokenScope, issued_at, expires_at, superseded_at }`, `SnapshotMeta { storage_key, generated_at, source_versions, last_error }`, `PublicationView { id, publication_id, token_id, viewed_at, access, client_hash, referrer_origin, stale }`.
- Use cases: `create_publication`, `update_publication`, `revoke_publication`, `rotate_token`, `list_publications`, `resolve_token` (hash lookup, expiry, revocation, scope), `render_public`, `render_embed` (origin check, CSP), `refresh_snapshot` (worker; renders the target through F013 `views::rows_for_actor`, F021 `reports::rows_for_actor`, or F023 `dashboards::widget_data_for_actor` as the publisher), `record_view`, `expire_due_publications` (worker cron).
- Worker: `services/worker/src/publishing/refresh_job.rs` consumes `publishing.refresh` with `{ tenant_id, publication_id, scheduled_at }` and stores the snapshot JSON in object storage under `publications/<id>/<generated_at>.json`; `services/worker/src/publishing/scheduler.rs` enqueues due refreshes and expirations every minute.
- API DTOs (`services/api/src/publishing/dto.rs`): `CreatePublicationRequest`, `UpdatePublicationRequest`, `PublicationResponse { ..., status, view_count_7d, last_viewed_at, snapshot: { generated_at, stale } }`, `TokenIssuedResponse { token, expires_at }`, `PublicRender { target_kind, title, generated_at, stale, payload }`.
- Events: `publication.created.v1` on create; `publication.updated.v1` on patch and rotation; `publication.revoked.v1` on delete and on expiry; `publication.viewed.v1` throttled per token per 5 minutes with `{ access, stale, referrer_origin }`.
- Authorization: `publisher` on the target for create, update, rotate, revoke; list filtered by target read; public routes authorize by token scope only; `tenant` access adds session tenant and target read checks; publication tokens presented to `/api/v1/*` are rejected by the gateway with `denied`.
- Validation: title 1–200 chars, `expires_at` ≤ now + 30 days, `allowed_origins` valid `https://` origins (≤ 10), `refresh_interval_s` 60–3600, one active publication per `(target, access)` pair.
- Error mapping: `PublishError::ExpiryTooFar → 400 invalid`, `PublishError::BadOrigin → 400 invalid`, `PublishError::DuplicateActive → 409 conflict`, `PublishError::StaleVersion → 409 conflict`, `PublishError::NotFound → 404 not_found`, `PublishError::TokenInvalid|Expired|Revoked → 404 not_found`, `PublishError::OriginNotAllowed → 403 denied` (rendered state), `PublishError::RateLimited → 429 rate_limited`.

### PostgreSQL/SQLx

- Migration `*_publishing_*.sql` creates `publications(id uuid pk, tenant_id uuid not null, workspace_id uuid not null, target_kind text not null check (target_kind in ('view','report','dashboard')), target_id uuid not null, title text not null, access text not null check (access in ('link','tenant')), expires_at timestamptz not null, embed_enabled bool not null default false, allowed_origins text[] not null default '{}', refresh_interval_s int not null check (refresh_interval_s between 60 and 3600), show_freshness bool not null default true, publisher_id uuid not null, status text not null default 'active', snapshot_key text, snapshot_generated_at timestamptz, snapshot_source_versions jsonb, snapshot_last_error text, version bigint not null default 1, created_by, created_at, updated_by, updated_at, revoked_at)`, `publication_tokens(id uuid pk, tenant_id, publication_id references publications(id) on delete restrict, token_hash bytea not null, scope jsonb not null, issued_at timestamptz not null, expires_at timestamptz not null, superseded_at timestamptz)`, `publication_views(id uuid pk, tenant_id, publication_id, token_id, viewed_at timestamptz not null, access text not null, client_hash bytea not null, referrer_origin text, stale bool not null)`.
- Invariants: unique `publication_tokens_hash_idx on (token_hash)`; partial unique `publications_active_target_access_idx on (tenant_id, target_kind, target_id, access) where status = 'active'`; check `expires_at <= created_at + interval '30 days'`; at most one token per publication with `superseded_at is null` via partial unique index.
- Indexes: `publications(tenant_id, workspace_id, status, updated_at desc)`, `publications(status, expires_at) where status = 'active'`, `publication_views(publication_id, viewed_at desc)`, `publication_tokens(publication_id) where superseded_at is null`.
- Audit events: `publication.create`, `publication.update`, `publication.rotate-token`, `publication.revoke`, `publication.expire`, `publication.render-denied` with reason; renders themselves are recorded in `publication_views`, not the audit log.
- Retention/deletion: `publication_views` older than 90 days purged by the F027 job; revoked publications and superseded tokens purged after 30 days; snapshot objects deleted with the publication; rollback drops the three tables.

### React/TypeScript

- Routes: `/w/:workspaceId/publications` in `apps/web/src/features/publishing/`; public pages `/public/publications/:token` and `/embed/:token` rendered by `PublicRenderPage` and `EmbedRenderPage` (no app shell, no session required for `link` access); components `PublishDialog`, `TokenRevealPanel`, `EmbedSnippet`, `OriginListEditor`, `PublicationsListPage`, `PublicationRow`, `FreshnessBanner`, `PublicDashboard`, `PublicView`, `PublicReport`, `PublicErrorState`.
- State: TanStack Query keys `['publications', workspaceId, filters]`, `['publication', id]`, `['public-render', token]`; public pages poll `['public-render', token]` every `refresh_interval_s` and update the freshness banner.
- API client: generated `PublishingApi` with `listPublications`, `createPublication`, `updatePublication`, `revokePublication`, `rotateToken`, `renderPublic`, `renderEmbed`.
- Embed behavior: `EmbedRenderPage` posts `{ type: "opshub-embed-height", height }` to `window.parent` for allowed origins only and never reads parent state.
- Feature flag: `useFlag('F059_FEATURE')` gates the `Publish` menu item and the publications route; public routes return not-found when the flag is off.
- Telemetry: `publication_created`, `publication_token_rotated`, `publication_revoked`, `publication_rendered` (server-side), `publication_embed_denied_origin` with `publication_id`, `target_kind`, `access`, `stale`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F059-01 through FR-F059-14 in `testing/features/F059/requirements/cases.md`
- [ ] Failure/edge-case tests: expiry 31 days, bad origin, duplicate active publication, rotated token grace, refresh failure stale, publisher access lost, target deleted, rate limit
- [ ] Permission-negative and tenant-isolation tests: non-publisher create denied, token on `/api/v1` denied, tenant-access token from another tenant not_found, hidden columns absent from render
- [ ] Rust unit tests: `crates/domain/src/publishing/` token hashing and scope, expiry math, stale computation, origin matching, view sampling
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: token hash uniqueness, active target uniqueness, expiry check, rollback
- [ ] React component tests: `PublishDialog`, `TokenRevealPanel`, `PublicRenderPage`, `EmbedRenderPage`, `FreshnessBanner`
- [ ] Browser E2E tests: publish dashboard, open public page logged out, embed in test host page, rotate, revoke
- [ ] Accessibility tests: axe on public page, embed page, publish dialog; freshness as text
- [ ] Performance/load tests: render p95 under 500 ms, refresh 10,000-row view under 10 s, rate limit enforcement

### Fast fanout configuration

- Test harness path: `testing/features/F059/`
- Feature flag: `F059_FEATURE`
- Fixture/seed factory: `testing/fixtures/publishing.rs` builds tenant, publisher, viewer, non-publisher, foreign tenant, a view with two hidden columns over a 10,000-row sheet, a report, a 12-widget dashboard, and a static test host page serving from `https://host.test`
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, fixed token RNG seed, fixed client-hash salt
- Mock/stub contracts: MinIO for snapshots; in-memory JetStream recorder; real F013, F021, F023 render paths; Playwright serves the embed host page on a second origin
- Parallel isolation: one schema per test worker, tenant ID per test, unique snapshot prefix per worker
- Targeted command: `cargo xtask test-feature F059`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F059/`

## 6. Acceptance criteria

```gherkin
Feature: Scoped read-only publishing and embedding

Scenario: Publish a dashboard and view it without an account
  Given a publisher on dashboard "Ops status"
  When they publish it with link access and a 30-day expiry
  Then the response returns the token once and publication.created.v1 is in the outbox
  And a logged-out browser renders /public/publications/{token} with generated_at and no navigation

Scenario: Hidden columns never leak
  Given a view with two hidden columns
  When the publication is refreshed and rendered
  Then the payload contains only visible columns and no row links into the tenant

Scenario: Token cannot call the API
  Given a valid publication token
  When it is presented as a bearer token to GET /api/v1/sheets
  Then the response is 403 denied and publication_token_rejected_total increases

Scenario: Revocation stops access
  Given an embedded publication on https://host.test
  When the publisher revokes it
  Then within 5 seconds /embed/{token} returns 404 and the host page shows the unavailable state
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F013 (view rows for an actor), F023 (dashboard widget data), F036 (share semantics, link expiry policy, guest boundary); decisions sections 2, 3, 4, 6, 7; contracts row F059
- Blocks: none
- Conflicts with: none (disjoint owned paths)
- External dependencies: none
- Risks and mitigations: rendering as the publisher could expose data the publisher gains later, so snapshots are regenerated with the publisher's scope on every refresh and access loss switches the publication to the error state; origin checks depend on `Referer` which browsers may strip, so embed also accepts a signed `origin` query parameter minted by the publish dialog; lobby screens polling every minute can add load, so renders are served from object storage with a 30 s CDN-friendly cache header.
- Rollout: enable `F059_FEATURE` for the pilot tenant, review `publication_token_rejected_total` and `publication_refresh_failures_total` for two weeks before wider rollout.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F013, F023, and F036 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F059/`
- [ ] Migration file name and owned paths claimed
- [ ] Second-origin host page, MinIO harness, and schema-per-worker isolation available in `testing/harness/`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, worker, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation, expiry, and denied render
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F059_FEATURE`, confirm public routes return not_found, run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Publishers can publish views, reports, and dashboards as read-only pages or embeds with expiring, revocable tokens, origin restrictions, and visible freshness.
- Support: denied and stale renders are counted per publication; operators inspect `publishing.refresh` dead letters and `publication_views` for a token.
- Migration adds `publications`, `publication_tokens`, and `publication_views`; rollback drops them. Feature is off by default behind `F059_FEATURE`.
