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
owned_paths: [crates/domain/src/publishing/**, crates/persistence/src/publishing/**, services/api/src/publishing/**, apps/web/src/features/publishing/**, services/api/migrations/*_publishing_*.sql, services/worker/src/publishing/**, testing/features/F059/**]
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
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 6, 7; `docs/capability-contracts.md` row F059
- Module slug: `publishing`

## 2. Requirement specification

### Problem and user outcome

Teams want to show a dashboard on a lobby screen, embed a status view in an intranet page, or send a report link to a customer who has no OpsHub account. Sharing (F036) grants identities; it does not produce a read-only, embeddable, revocable surface with clear staleness.

As a publisher, I want to publish a view, report, or dashboard as a scoped read-only artifact with an expiring, revocable token and optional embedding on allowed origins, so that outsiders see exactly what I am allowed to see, never more, and always know how fresh it is.

### Functional requirements

- **FR-F059-01:** An actor with the `publisher` role on a `view`, `report`, or `dashboard` can create a publication with `target: { kind, id }`, `title`, `access: link|tenant`, `expires_at` (≤ 30 days from now, default 30 days), `embed: { enabled, allowed_origins: [origin] ≤ 10 }`, `refresh_interval_s` (60–3600), and `show_freshness: bool`; each submitted origin is stored as one `publication_allowed_origins` row, duplicates within the request collapse to one row, and the request and response keep `allowed_origins` as a JSON array so the API shape is unchanged; the response returns UUIDv7 `id`, `version` 1, and a one-time plaintext `token`.
- **FR-F059-02:** Tokens are 32 random bytes, stored only as SHA-256 hashes in `publication_tokens` whose scope is the typed columns `tenant_id`, `publication_id`, `scope_target_kind`, `scope_target_id`, and `read_only` (constrained `true`) rather than a `jsonb` blob, while `TokenScope` still serialises to `{ tenant_id, publication_id, target, read_only: true }` wherever the scope is echoed; tokens are never returned again after creation or rotation; `POST /api/v1/publications/{id}/rotate-token` issues a new token, expires the old one after a 10-minute grace period, and publishes `publication.updated.v1` with `changed_fields: ["token"]`.
- **FR-F059-03:** `GET /public/publications/{token}` renders the target read-only as the publisher's permission scope at render time, filtered by the target's own filters; if the publisher has lost read access or the target is deleted, the page renders the `error` state with `reason: publisher_access_lost|target_deleted` and no data.
- **FR-F059-04:** Public and embed responses never include row IDs beyond those needed for rendering, hidden columns, comments, attachments, or links to the tenant; navigation, search, and any mutation affordance are absent, and every write route rejects publication tokens with `denied`.
- **FR-F059-05:** Rendering is served from a snapshot refreshed by the worker every `refresh_interval_s`; the response carries `generated_at`, `source_versions` (assembled from the publication's `publication_snapshot_sources` rows, one per contributing view, report, dashboard, sheet, or widget, and serialised as the same JSON object as before), and `stale: true` when the last refresh failed or is older than `2 × refresh_interval_s`; the stale state is shown in the page when `show_freshness` is true and always exposed in the `X-OpsHub-Stale` header.
- **FR-F059-06:** `access: tenant` requires an authenticated session in the same tenant and the target's read ACL in addition to the token; `access: link` requires only the token; a token used from a different tenant's session for `tenant` access returns `not_found`.
- **FR-F059-07:** `GET /embed/{token}` returns the same rendering inside an iframe-safe document with `Content-Security-Policy: frame-ancestors <origins>` and `X-Frame-Options` omitted, where the directive is assembled by space-joining the `origin` column of the publication's `publication_allowed_origins` rows ordered by `origin`, producing the identical header the array produced; a request whose `Origin`/`Referer` matches no `publication_allowed_origins` row renders the `denied` state; `embed_enabled = false` returns `not_found`.
- **FR-F059-08:** `DELETE /api/v1/publications/{id}` revokes every token immediately, publishes `publication.revoked.v1`, and public and embed requests return `404 not_found` within 5 s; expired publications behave the same and show `reason: expired` in the audit view.
- **FR-F059-09:** `PATCH /api/v1/publications/{id}` with `If-Match` updates `title`, `access`, `expires_at` (still ≤ 30 days from now), `embed`, `refresh_interval_s`, `show_freshness`; a supplied `embed.allowed_origins` array replaces the publication's `publication_allowed_origins` rows in the same transaction (delete of removed origins, insert of added ones), so a removed origin stops satisfying the embed check on the next request; a stale version returns `conflict`; every change publishes `publication.updated.v1`.
- **FR-F059-10:** Each public or embed render records a `publication_views` row whose `viewed_at`, `access`, `client_hash`, `referrer_origin`, and `stale` are typed columns — never a `jsonb` payload — because the publications list aggregates and filters on them, sampled to at most one row per token per minute, and publishes `publication.viewed.v1` at most once per token per 5 minutes.
- **FR-F059-11:** `GET /api/v1/publications` lists publications with cursor paging, filters `target_kind`, `target_id`, `status: active|expired|revoked`, and per-row `view_count_7d`, `last_viewed_at`, `expires_at`; `view_count_7d` and `last_viewed_at` are aggregated from `publication_views` over the trailing 7 days on the `(publication_id, viewed_at desc)` index, not stored on `publications`; only publications the actor could read the target for are visible.
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

- Design: `design/artboards/Publishing.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

### Rust backend

- Data access (decision section 2.1): `crates/persistence/src/publishing/` holds `PublicationRepository` (owns `publications`, `publication_allowed_origins`, `publication_snapshot_sources`), `PublicationTokenRepository` (owns `publication_tokens`), and `PublicationViewRepository` (owns `publication_views`); the two child tables belong to the publication aggregate, so no second class writes them. Named queries: `PublicationRepository::{list_for_workspace_page, find_active_for_target, list_allowed_origins, replace_allowed_origins, list_snapshot_sources, replace_snapshot_sources, record_snapshot_success, record_snapshot_failure, mark_access_lost, list_due_for_refresh, list_due_for_expiry, mark_expired, mark_revoked}`; `PublicationTokenRepository::{find_by_token_hash, insert_rotated_token, supersede_with_grace, revoke_all_for_publication, purge_superseded_before}`; `PublicationViewRepository::{record_sampled_view, count_views_since, last_viewed_at, purge_views_before}`. There is no generic query entry point. Every use case below depends on these traits and contains no SQL: the API handlers, the embed and public handlers, the refresh job, and the scheduler call repositories only, and the unauthenticated `GET /public/publications/{token}` and `GET /embed/{token}` routes resolve the presented token through `PublicationTokenRepository::find_by_token_hash` — never an inline `sqlx::query` in a handler or middleware. Create, rotate, patch, and revoke are multi-table writes and run in one `UnitOfWork`: the publication row, its origin and snapshot-source rows, the token rows, the audit row, and the outbox enqueue commit together or not at all.
- Canonical contract: aggregate `publication`; module `publishing`; routes `GET /api/v1/publications`, `POST /api/v1/publications`, `PATCH /api/v1/publications/{id}`, `DELETE /api/v1/publications/{id}`, `POST /api/v1/publications/{id}/rotate-token`, `GET /public/publications/{token}`, `GET /embed/{token}`; events `publication.created.v1`, `publication.updated.v1`, `publication.revoked.v1`, `publication.viewed.v1`; tables `publications`, `publication_tokens`, `publication_views`; mutation role `publisher`.
- Domain entities in `crates/domain/src/publishing/`: `Publication { id, tenant_id, workspace_id, target: PublishTarget, title, access: Access, expires_at, embed: EmbedSettings, refresh_interval_s, show_freshness, publisher_id, status, snapshot: Option<SnapshotMeta>, version, audit fields, revoked_at }`, `PublicationToken { id, publication_id, token_hash, scope: TokenScope { tenant_id, publication_id, target: PublishTarget, read_only }, issued_at, expires_at, superseded_at }`, `SnapshotMeta { storage_key, generated_at, sources: Vec<SnapshotSource { kind, id, version }>, last_error }`, `PublicationView { id, publication_id, token_id, viewed_at, access, client_hash, referrer_origin, stale }`. `EmbedSettings { enabled, allowed_origins: Vec<Origin> }` and `SnapshotMeta.sources` are loaded and stored as child rows by `PublicationRepository`; the domain type keeps the collection shape the DTOs serialise, so no caller sees the change.
- Use cases: `create_publication`, `update_publication`, `revoke_publication`, `rotate_token`, `list_publications`, `resolve_token` (hashes the presented plaintext and calls `PublicationTokenRepository::find_by_token_hash`, then checks expiry, revocation, and the token's scope columns), `render_public`, `render_embed` (matches the request origin against `PublicationRepository::list_allowed_origins` and builds the CSP from those rows), `refresh_snapshot` (worker; renders the target through F013 `views::rows_for_actor`, F021 `reports::rows_for_actor`, or F023 `dashboards::widget_data_for_actor` as the publisher), `record_view`, `expire_due_publications` (worker cron).
- Worker: `services/worker/src/publishing/refresh_job.rs` consumes `publishing.refresh` with `{ tenant_id, publication_id, scheduled_at }` and stores the snapshot JSON in object storage under `publications/<id>/<generated_at>.json`; the job holds no SQL — it reads the publication through `PublicationRepository`, writes the snapshot metadata with `record_snapshot_success` or `record_snapshot_failure`, and replaces the contributing versions with `replace_snapshot_sources` in the same `UnitOfWork`. `services/worker/src/publishing/scheduler.rs` enqueues due refreshes and expirations every minute from `PublicationRepository::list_due_for_refresh` and `list_due_for_expiry`.
- API DTOs (`services/api/src/publishing/dto.rs`): `CreatePublicationRequest`, `UpdatePublicationRequest`, `PublicationResponse { ..., status, view_count_7d, last_viewed_at, snapshot: { generated_at, stale } }`, `TokenIssuedResponse { token, expires_at }`, `PublicRender { target_kind, title, generated_at, stale, payload }`.
- Events: `publication.created.v1` on create; `publication.updated.v1` on patch and rotation; `publication.revoked.v1` on delete and on expiry; `publication.viewed.v1` throttled per token per 5 minutes with `{ access, stale, referrer_origin }`.
- Authorization: `publisher` on the target for create, update, rotate, revoke; list filtered by target read; public routes authorize by token scope only; `tenant` access adds session tenant and target read checks; publication tokens presented to `/api/v1/*` are rejected by the gateway with `denied`.
- Validation: title 1–200 chars, `expires_at` ≤ now + 30 days, `allowed_origins` valid `https://` scheme-host-port origins with no path (≤ 10 distinct rows after deduplication, counted by `PublicationRepository::replace_allowed_origins` before commit), `refresh_interval_s` 60–3600, one active publication per `(target, access)` pair.
- Error mapping: `PublishError::ExpiryTooFar → 400 invalid`, `PublishError::BadOrigin → 400 invalid`, `PublishError::DuplicateActive → 409 conflict`, `PublishError::StaleVersion → 409 conflict`, `PublishError::NotFound → 404 not_found`, `PublishError::TokenInvalid|Expired|Revoked → 404 not_found`, `PublishError::OriginNotAllowed → 403 denied` (rendered state), `PublishError::RateLimited → 429 rate_limited`.

### Interface

Exact shapes. Every field lists its JSON name, type, whether it is required, and the constraint whose
violation produces the stated error. `T?` is nullable; an absent optional field and an explicit
`null` mean the same thing. Ids are UUIDv7 strings, timestamps are RFC 3339 UTC, `version` increments
by one per write. Unlisted request fields are rejected with `400 invalid`. `Page<T>`, `ListQuery`, the
signed cursor, the error body and the six codes are F028's; `ActorContext` is F038's. This module has
two surfaces with different rules, and the difference is the point of the feature: the `/api/v1`
surface is authenticated and behaves like every other module, while `/public/publications/{token}`
and `/embed/{token}` are **unauthenticated** and constrained below.

**`PublishTarget`**: `{ kind: "view" | "report" | "dashboard", id: uuid }`. The id carries no foreign
key because the target is one of three aggregates; a target the caller cannot read as `publisher` is
`404 not_found` on the whole request, never a field error that would confirm the id exists.

**`EmbedSettings`**

| Field | Type | Required | Constraint |
|---|---|---|---|
| `enabled` | bool | yes | `false` makes `/embed/{token}` return `404 not_found` |
| `allowed_origins` | string[] | conditional | required and 1–10 entries when `enabled` is `true`; each is a scheme-host-port origin matching `^https://[a-z0-9.-]+(:[0-9]{1,5})?$` with no path, query or trailing slash, else `400 invalid` with `field_errors.embed.allowed_origins[i]`. Duplicates collapse to one `publication_allowed_origins` row and do not count twice against the limit |

**`CreatePublicationRequest`** — `POST /api/v1/publications`

| Field | Type | Required | Constraint |
|---|---|---|---|
| `target` | PublishTarget | yes | caller holds `publisher` on it; one active publication per `(target, access)` pair, else `409 conflict` |
| `title` | string | yes | 1–200 chars after trim. Shown on the public page, so it must not be assumed private |
| `access` | `"link" \| "tenant"` | no | default `"link"` |
| `expires_at` | timestamp | no | default now + 30 days; more than 30 days ahead → `400 invalid` with `field_errors.expires_at` |
| `embed` | EmbedSettings | no | default `{ enabled: false, allowed_origins: [] }` |
| `refresh_interval_s` | integer | no | 60–3600, default 300 |
| `show_freshness` | bool | no | default `true` |

**`UpdatePublicationRequest`** — `PATCH /api/v1/publications/{id}`, `If-Match` required, at least one
field present: `title`, `access`, `expires_at`, `embed`, `refresh_interval_s`, `show_freshness`, each
constrained as above. `target` is not patchable and is rejected as an unlisted field — repointing a
live token at another aggregate is a new publication, not an edit. A supplied `embed.allowed_origins`
**replaces** the origin rows, so a removed origin stops satisfying the embed check on the next request
(FR-F059-09).

**`TokenIssuedResponse`** — the body of `POST /api/v1/publications` and of
`POST /api/v1/publications/{id}/rotate-token`

| Field | Type | Notes |
|---|---|---|
| `publication_id` | uuid | |
| `token` | string | 32 random bytes, base64url. Returned **exactly once**, on the response that mints it. Only the SHA-256 hash is stored, so no later read, list or event can reproduce it; a client that loses it rotates |
| `expires_at` | timestamp | the token's expiry, which is the publication's |
| `previous_token_expires_at` | timestamp? | on rotation only: when the superseded token stops working, `now + 10 minutes` (FR-F059-02). `null` on first issue |

**`PublicationResponse`**

| Field | Type | Notes |
|---|---|---|
| `id` / `workspace_id` | uuid | |
| `target` | PublishTarget | |
| `title` / `access` / `expires_at` / `embed` / `refresh_interval_s` / `show_freshness` | as the request | |
| `publisher_id` | uuid | |
| `status` | `"active" \| "expired" \| "revoked" \| "error"` | `error` when the publisher lost read access or the target was deleted |
| `error_reason` | `"publisher_access_lost" \| "target_deleted"`? | present only when `status` is `error` |
| `snapshot` | `{ generated_at: timestamp?, stale: bool, last_error: string? }` | `generated_at` is `null` before the first refresh |
| `view_count_7d` | integer | aggregated from `publication_views` over the trailing 7 days on read, not stored |
| `last_viewed_at` | timestamp? | as above; `null` when never viewed |
| `version` | integer | pass as `If-Match` on the next write |
| `created_at` / `updated_at` / `created_by` / `updated_by` / `revoked_at?` | | |

No token, token hash or `snapshot_key` appears here.

**List route.** `GET /api/v1/publications` takes F028's `ListQuery` and returns
`Page<PublicationResponse>`; sort key `updated_at` descending with `id` as tiebreak, or `expires_at`
ascending. Filters: `target_kind` (enum), `target_id` (uuid), `status` (enum), `workspace_id` (uuid).
Only publications whose target the caller may read are visible, so the list is not a way to discover
what colleagues have published from sheets the caller cannot see.

#### The unauthenticated surface

**What an anonymous caller sends.** `GET /public/publications/{token}` and `GET /embed/{token}` take
**one** input: the token in the path. No tenant slug, no workspace id, no publication id, no query
parameter, no cookie and no `Authorization` header participate in resolution — the token is hashed
and looked up, and nothing else in the request selects a row. The one exception is the embed
origin check, which reads the `Origin` header (falling back to `Referer`, and to the signed `origin`
query parameter the publish dialog mints when the browser strips both) purely to *reject*; it never
selects a different publication. `access: "tenant"` additionally requires a session cookie in the
same tenant, and a session from another tenant is treated exactly as no session at all.

**What the response may reveal.** The rendered body carries `title`, the target's visible rows or
widgets, `generated_at` and the freshness state — nothing else. It carries no tenant id, tenant name
or slug, no workspace id, no user id, name or avatar, no sheet or view id, no column ids beyond those
the rendering needs, no hidden columns, no comments, attachments or links, and no navigation into the
app (FR-F059-04, FR-F059-14). Row ids appear only where the rendering needs them as React keys and
are opaque outside the page. The only outbound link permitted is `Open in OpsHub` on `access:
"tenant"`, which is a login-gated route.

**No existence oracle.** Every failure on both public routes returns the same bare `404 not_found`
page with no body detail and no timing difference beyond the constant-time hash comparison: an
unknown token, a well-formed token that was never issued, an expired token, a superseded token past
its grace, a revoked or expired publication, a publication whose `embed.enabled` is `false` on the
embed route, a `tenant`-access token presented with no session or a session from another tenant, and
every request while `F059_FEATURE` is off. A caller cannot distinguish "this token never existed"
from "this token existed and was revoked", and cannot learn that a tenant exists by guessing tokens.
Two states are visibly different, and only because the token was valid: `status = "error"` renders
the error page with `reason`, and an embed from an unlisted origin renders the denied state — both
already prove the caller holds a live token.

**`PublicRender`** — the body of `GET /public/publications/{token}` when the token resolves

| Field | Type | Notes |
|---|---|---|
| `target_kind` | `"view" \| "report" \| "dashboard"` | decides which renderer the page uses |
| `title` | string | |
| `generated_at` | timestamp | when the snapshot was produced |
| `stale` | bool | `true` when the last refresh failed or `generated_at` is older than `2 × refresh_interval_s` |
| `refresh_interval_s` | integer | so the page knows its own poll interval without a second request |
| `show_freshness` | bool | whether the page displays the freshness banner; `stale` is reported either way |
| `source_versions` | map<string, integer> | `"<source_kind>:<source_id>"` to `source_version`, assembled from `publication_snapshot_sources`. Present only for `access: "tenant"`; omitted entirely for `access: "link"`, because source ids are internal identifiers an anonymous viewer has no use for |
| `payload` | object | the target-shaped rendering, already permission-filtered at refresh time under the publisher's scope |
| `error` | `{ reason: "publisher_access_lost" \| "target_deleted" }`? | present instead of `payload` when the publication is in `error`; no data accompanies it |

Response headers on both public routes: `X-OpsHub-Stale: true|false` (FR-F059-05),
`Cache-Control: private, max-age=30`, and on `/embed/{token}` a
`Content-Security-Policy: frame-ancestors <origins>` built by space-joining the
`publication_allowed_origins` rows in `origin` order, with `X-Frame-Options` deliberately omitted so
the CSP directive is the single arbiter. `/public/publications/{token}` sends
`frame-ancestors 'none'`.

**Status codes**

| Status | `code` | Produced by |
|---|---|---|
| `400` | `invalid` | `expires_at` over 30 days, a malformed or non-`https` origin, an 11th origin, `refresh_interval_s` outside 60–3600, a title outside 1–200, an unlisted field |
| `403` | `denied` | a non-`publisher` calling a mutation; a publication token presented to any `/api/v1/*` route, rejected at the gateway before routing (FR-F059-14) |
| `404` | `not_found` | a publication id of another tenant or one whose target the caller may not read; and every failure of the two public routes, as enumerated above. The public routes never answer `403` — a `denied` there would confirm the token is real |
| `409` | `conflict` | stale `If-Match`, a second active publication for the same `(target, access)`, `Idempotency-Key` replayed with a different body |
| `429` | `rate_limited` | more than 60 requests per minute per token or 600 per minute per client address, carrying `Retry-After` (FR-F059-12) |
| `503` | `unavailable` | object storage holding the snapshot is unreachable; the page is not rendered from a partial snapshot |

The origin-denied embed case is **not** an HTTP `403`: it renders a `200` denied *state* inside the
iframe, because the browser needs a document to display and the CSP already stopped the framing.

### Use case signatures

In `crates/domain/src/publishing/`. Each takes `ctx: &Ctx` carrying tenant, actor and correlation id
— on the public routes an anonymous `Ctx` whose actor is the resolved token's scope, never a user —
depends on repository traits rather than a pool or connection, and returns `DomainError`.

```rust
fn create_publication(ctx: &Ctx, uow: &mut UnitOfWork, req: CreatePublication) -> Result<(Publication, PlaintextToken), DomainError>;
fn update_publication(ctx: &Ctx, uow: &mut UnitOfWork, id: PublicationId, expected: Version, req: UpdatePublication) -> Result<Publication, DomainError>;
fn revoke_publication(ctx: &Ctx, uow: &mut UnitOfWork, id: PublicationId) -> Result<(), DomainError>;
fn rotate_token(ctx: &Ctx, uow: &mut UnitOfWork, id: PublicationId, grace: Duration) -> Result<PlaintextToken, DomainError>;
fn list_publications(ctx: &Ctx, repo: &dyn PublicationRepository, filter: PublicationFilter, page: Cursor) -> Result<Page<Publication>, DomainError>;
fn resolve_token(tokens: &dyn PublicationTokenRepository, presented: &str, now: Timestamp) -> Result<ResolvedToken, DomainError>;
fn render_public(ctx: &Ctx, repo: &dyn PublicationRepository, store: &dyn SnapshotStore, token: &ResolvedToken, session: Option<&ActorContext>) -> Result<PublicRender, DomainError>;
fn render_embed(ctx: &Ctx, repo: &dyn PublicationRepository, store: &dyn SnapshotStore, token: &ResolvedToken, origin: Option<&Origin>) -> Result<EmbedRender, DomainError>;
fn refresh_snapshot(ctx: &Ctx, uow: &mut UnitOfWork, store: &dyn SnapshotStore, id: PublicationId, scheduled_at: Timestamp) -> Result<SnapshotMeta, DomainError>;
fn record_view(ctx: &Ctx, uow: &mut UnitOfWork, view: PublicationView) -> Result<(), DomainError>;
fn expire_due_publications(ctx: &Ctx, uow: &mut UnitOfWork, now: Timestamp) -> Result<Vec<PublicationId>, DomainError>;

fn is_stale(generated_at: Option<Timestamp>, interval_s: u32, last_error: bool, now: Timestamp) -> bool;
fn origin_allowed(allowed: &[Origin], presented: Option<&Origin>) -> bool;
```

`resolve_token` returns `DomainError::NotFound` for every failure class — unknown hash, expired,
superseded past grace, revoked publication — so a caller cannot branch on the reason and neither can
a handler accidentally surface it. `is_stale` and `origin_allowed` are pure, which is what lets the
staleness and origin rules be unit tested without a database and keeps the header, the banner and the
CSP consistent.

**Transaction boundaries.**

- `create_publication` writes the `publications` row, its `publication_allowed_origins` rows, the
  first `publication_tokens` row, the audit row and the `publication.created.v1` outbox entry in one
  `UnitOfWork`. The invariant: a publication is never readable without its origin rows, because an
  embed whose origin set had not yet committed would frame anywhere the CSP defaulted to.
- `rotate_token` inserts the new token row and sets `superseded_at = now + 10 minutes` on the
  current one in one `UnitOfWork`, which the partial unique index on
  `(publication_id) where superseded_at is null` requires: exactly one non-superseded token at all
  times, never zero and never two.
- `update_publication` replaces the origin rows and bumps the version under `If-Match` in one
  `UnitOfWork`, so a removed origin and the version a client will next send commit together.
- `revoke_publication` sets `revoked_at`, `status = 'revoked'` and revokes **every** token row in one
  `UnitOfWork`, which is what makes the 5-second guarantee of FR-F059-08 a property of the commit
  rather than of a background job.
- `refresh_snapshot` writes the snapshot object to storage first, then commits the
  `publications` snapshot columns and the replaced `publication_snapshot_sources` rows in one
  `UnitOfWork`. Order matters: a committed `snapshot_key` pointing at an object that does not exist
  would render `503` forever, whereas an orphaned object is only garbage.
- `record_view` writes one sampled `publication_views` row and, at most once per token per five
  minutes, the `publication.viewed.v1` outbox entry in its own short `UnitOfWork` — never the
  render's, because analytics must not be able to fail a public render.
- `list_publications`, `resolve_token`, `render_public` and `render_embed` are reads and take
  repositories, not a `UnitOfWork`.

### PostgreSQL/SQLx

- Migration `*_publishing_*.sql` creates `publications(id uuid pk, tenant_id uuid not null, workspace_id uuid not null references workspaces(id) on delete restrict, target_kind text not null check (target_kind in ('view','report','dashboard')), target_id uuid not null, title text not null, access text not null check (access in ('link','tenant')), expires_at timestamptz not null, embed_enabled bool not null default false, refresh_interval_s int not null check (refresh_interval_s between 60 and 3600), show_freshness bool not null default true, publisher_id uuid not null references users(id) on delete restrict, status text not null default 'active' check (status in ('active','expired','revoked','error')), snapshot_key text, snapshot_generated_at timestamptz, snapshot_last_error text, version bigint not null default 1, created_by, created_at, updated_by, updated_at, revoked_at)`, `publication_tokens(id uuid pk, tenant_id uuid not null, publication_id uuid not null references publications(id) on delete restrict, token_hash bytea not null, scope_target_kind text not null check (scope_target_kind in ('view','report','dashboard')), scope_target_id uuid not null, read_only bool not null default true check (read_only), issued_at timestamptz not null, expires_at timestamptz not null, superseded_at timestamptz)`, `publication_views(id uuid pk, tenant_id uuid not null, publication_id uuid not null references publications(id) on delete cascade, token_id uuid references publication_tokens(id) on delete set null, viewed_at timestamptz not null, access text not null check (access in ('link','tenant')), client_hash bytea not null, referrer_origin text, stale bool not null)`. `target_id` carries no foreign key because the target is one of three aggregates selected by `target_kind`; existence is checked by the F013/F021/F023 repository at create and at every refresh, and a deleted target moves the publication to `status = 'error'` (FR-F059-03).
- Normalized sets (decision section 2, no array columns): `publication_allowed_origins(publication_id uuid not null references publications(id) on delete cascade, tenant_id uuid not null, origin text not null check (origin ~ '^https://[a-z0-9.-]+(:[0-9]{1,5})?$'), created_at timestamptz not null default now(), primary key (publication_id, origin))` replaces `publications.allowed_origins text[]`: an embed origin is a security decision, so each one is a row that can be joined, indexed, audited, and revoked individually. `publication_snapshot_sources(publication_id uuid not null references publications(id) on delete cascade, tenant_id uuid not null, source_kind text not null check (source_kind in ('view','report','dashboard','sheet','widget')), source_id uuid not null, source_version bigint not null, primary key (publication_id, source_kind, source_id))` replaces `publications.snapshot_source_versions jsonb`, which the render and staleness paths read key by key. Both children are cascade-deleted because neither can outlive its publication; `publication_tokens` and `publication_views` keep `on delete restrict`/`cascade` as above so a revoked publication's tokens cannot be dropped silently while the audit view still needs them.
- `jsonb` audit: `publications.snapshot_source_versions` was a map the product read and compared per source — it becomes `publication_snapshot_sources` rows. `publication_tokens.scope` was a blob the token check filtered on — it becomes the typed columns `tenant_id`, `publication_id`, `scope_target_kind`, `scope_target_id`, `read_only`, so scope enforcement is a predicate rather than a JSON extraction. `publication_views` holds no `jsonb`: its counters, `access`, `stale`, and `referrer_origin` are aggregated and filtered by FR-F059-11 and stay typed columns. No `jsonb` column remains in this module; the rendered snapshot payload is a user-shaped document and lives in object storage under `publications/<id>/<generated_at>.json`, referenced by `snapshot_key`, not in a database column.
- Preserved shapes: `CreatePublicationRequest`, `UpdatePublicationRequest`, and `PublicationResponse` keep `embed.allowed_origins` as a JSON array, `TokenScope` still serialises as an object, and `PublicRender.source_versions` is still one object; `PublicationRepository` fans them out to rows on write and reassembles them on read, so no externally visible request, response, event payload, or header changes.
- Invariants: unique `publication_tokens_hash_idx on (token_hash)`; partial unique `publications_active_target_access_idx on (tenant_id, target_kind, target_id, access) where status = 'active'`; check `expires_at <= created_at + interval '30 days'`; at most one token per publication with `superseded_at is null` via partial unique index; `publication_allowed_origins` primary key `(publication_id, origin)` makes a duplicate origin impossible and the ≤ 10 limit is checked in `replace_allowed_origins` before commit, replacing the former array-length check; `publication_snapshot_sources` primary key `(publication_id, source_kind, source_id)` gives one version per contributing source, replacing the former uniqueness-by-JSON-key assumption; `read_only` carries `check (read_only)` so no token row can ever be writable.
- Indexes: `publications(tenant_id, workspace_id, status, updated_at desc)`, `publications(status, expires_at) where status = 'active'`, `publication_views(publication_id, viewed_at desc)` for `view_count_7d` and `last_viewed_at`, `publication_tokens(publication_id) where superseded_at is null`, `publication_tokens(scope_target_kind, scope_target_id)` for "which tokens reach this target", `publication_allowed_origins(publication_id)` for the CSP assembly and origin check on every embed render and `publication_allowed_origins(tenant_id, origin)` for the reverse audit "which publications are embeddable on this host", `publication_snapshot_sources(source_kind, source_id)` so a changed source finds the publications to refresh.
- Audit events: `publication.create`, `publication.update`, `publication.rotate-token`, `publication.revoke`, `publication.expire`, `publication.render-denied` with reason; renders themselves are recorded in `publication_views`, not the audit log.
- Retention/deletion: `publication_views` older than 90 days purged by `PublicationViewRepository::purge_views_before` from the F027 job; revoked publications and superseded tokens purged after 30 days by `purge_superseded_before`, which is why `publication_views.token_id` is `on delete set null` — a view row outlives the token it was served with and keeps its `access`, `stale`, and `referrer_origin` evidence; snapshot objects deleted with the publication; rollback drops `publication_snapshot_sources`, `publication_allowed_origins`, `publication_views`, `publication_tokens`, then `publications`, children before parents.

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
- [ ] Database migration/constraint tests: token hash uniqueness, active target uniqueness, expiry check, duplicate `publication_allowed_origins` row rejected, non-`https` origin rejected by the check constraint, duplicate `publication_snapshot_sources` source rejected, origin and source rows cascade with the publication, `read_only = false` token rejected, rollback ordering
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
- Migration adds `publications`, `publication_tokens`, and `publication_views` plus the child tables `publication_allowed_origins` and `publication_snapshot_sources`; rollback drops them children first. Feature is off by default behind `F059_FEATURE`.
