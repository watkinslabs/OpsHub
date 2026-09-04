---
id: F073
type: feature
status: planned
priority: P2
owner: platform
estimate: 5
target_milestone: M3
parent_epic: E003
depends_on: [F002, F037]
blocks: []
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/announcements/**, crates/persistence/src/announcements/**, services/api/src/announcements/**, services/worker/src/announcements/**, apps/web/src/features/announcements/**, services/api/migrations/*_announcements_*.sql, testing/features/F073/**]
feature_flag: F073_FEATURE
flag_default: off
branch: f073-announcements-and-in-app-help
started_at: null
finished_at: null
---

# F073 — Announcements and in-app help

## 1. Identity and dates

- Branch: `f073-announcements-and-in-app-help`
- Capability area: product communication and self-service help (spec 2 design principles, spec 5.5 notification surfaces, spec 6 accessibility and privacy)
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 2.2, 3; `docs/capability-contracts.md` row F073; `docs/authorization-model.md` sections 2 and 3.1; `docs/packaging.md` sections 1 and 2; `docs/engineering-standards.md`
- Aggregate: `announcement`
- Module slug: `announcements`

- Milestone note: the plan places F073 in epic E003, whose other features are M2, but its dependency F037 is M3 and the repository rules forbid depending on a later milestone. It is therefore M3, alongside the notification service it delivers through.

## 2. Requirement specification

### Problem and user outcome

The product changes every week and tells nobody. A tenant administrator learns that approvals gained an escalation step when a user files a support request about it, and the user who hit the unfamiliar dialog had no way to ask what it was for without leaving the app and searching a website that does not know which version they are on. The two halves of that failure are the same problem: the product knows what changed and it knows which screen the person is looking at, and it uses neither.

Two surfaces close it. A what's-new panel says what changed, targeted so that a Free tenant is not told about an Enterprise-only module, which reads as an advert rather than news. A help drawer opens beside the screen the person is already on and shows the article for that screen, in their language, without navigating away.

As a person using OpsHub, I want to see what changed that actually applies to me, dismiss it once and never see it again, and open the help for the screen I am on without losing my place, so that the product explains itself instead of interrupting me.

### Functional requirements

- **FR-F073-01:** `GET /api/v1/announcements` returns the announcements visible to the calling user, newest `published_at` first, with `{ id, slug, scope, severity, title, body_markdown, learn_more_article_slug, published_at, expires_at, dismissed, interrupting, translation_fallback }` and cursor pagination (default 20, maximum 50). Visible means `state = 'published'`, `expires_at` null or in the future, `deleted_at` null, the announcement is either platform scope or belongs to the caller's tenant, and every target kind attached to it matches the caller (FR-F073-04). `dismissed` announcements are returned only when `include_dismissed=true`, so the panel can show history without ever re-surfacing one by default.
- **FR-F073-02:** `POST /api/v1/announcements` with `{ scope: "platform", slug, severity, translations: [{ locale, title, body_markdown }], targets: [{ kind, value }], learn_more_article_slug?, expires_at?, publish: bool }` is permitted only to a `platform-operator` principal, which carries no tenant role and no tenant data access; a session holding any tenant role, including `tenant-admin`, receives `403 denied` on `scope: "platform"`. The response is `201` with `{ id, slug, state, audience_size, content_hash, version }`.
- **FR-F073-03:** The same route with `{ scope: "tenant", ... }` is permitted to a `tenant-admin` and writes `announcements.tenant_id` from the session, never from the body. A `targets` entry of kind `tenant` naming any tenant other than the caller's returns `403 denied` with `field_errors.targets = "foreign_tenant"`; a `tenant`-scope body from a `platform-operator` returns `400 invalid` because that principal has no tenant. Both authoring paths write an audit row carrying `actor_id`, `scope`, `slug`, `severity`, the target tuples and `content_hash`.
- **FR-F073-04:** Targeting is a set of `announcement_targets` rows of kind `plan` (`free`, `team`, `enterprise` per `docs/packaging.md` section 1), `entitlement` (an F048 entitlement key such as `assets` or `ai-insights`, matching only when the tenant holds it in state `active` or `trial`), `role` (a role defined in `docs/authorization-model.md` section 3, matching when the user holds it at any scope), and `tenant` (a tenant id). Evaluation is OR within a kind and AND across kinds, so `plan: enterprise` plus `role: tenant-admin` reaches enterprise administrators only. An announcement with no target rows reaches every user in its scope. A `plan` or `entitlement` target is what stops an Enterprise-only capability being announced to a Free tenant.
- **FR-F073-05:** Publishing sets `state = 'published'` and `published_at`, computes `audience_size` as the number of users the target set resolves to at that instant, stores it on the row, and emits `announcement.published.v1` with `{ announcement_id, scope, tenant_id, slug, severity, target_kinds, audience_size, content_hash }`. `audience_size` is a publish-time snapshot and is never recomputed, so it can never become a live count of who is reading.
- **FR-F073-06:** `POST /api/v1/announcements/{id}/dismiss` is a `self` action: it inserts one `announcement_dismissals` row for the calling user with the announcement's current `content_hash` and `dismissed_at`, emits `announcement.dismissed.v1` with `{ announcement_id, tenant_id, dismissed_at }` and no user identifier, and returns `204`. It is idempotent — a second call is `204` and writes nothing. Dismissal is permanent: no route deletes a dismissal row, the F027 retention sweep does not expire them, and a dismissed announcement is excluded from `GET /api/v1/announcements` for that user for the life of the account.
- **FR-F073-07:** A published announcement may be edited only editorially. `PATCH /api/v1/announcements/{id}` accepts `expires_at` and translation text under `revision: "editorial"`, which requires `severity`, the target set and `learn_more_article_slug` to be unchanged and each edited body to differ from the stored body by at most 5% of its NFC-normalized whitespace-collapsed token count. Anything else is a **material change** and returns `409 conflict` with `field_errors.revision = "material"`. A material change is published as a new announcement carrying `supersedes_id`, which sets the original to `state = 'superseded'`; the new announcement has its own `content_hash`, carries no dismissal rows and therefore appears once to everyone it targets. A dismissed announcement is never resurrected — the superseded row stays dismissed and stays out of the list.
- **FR-F073-08:** `severity` is `info`, `change` or `action_required`. `info` and `change` are passive: they appear in the what's-new panel and put a dot on the panel trigger, and `interrupting` is always false for them. Only `action_required` may set `interrupting: true`, and only when it carries a `learn_more_article_slug`, so an interruption always has somewhere to go.
- **FR-F073-09:** The interruption budget is enforced server-side before `interrupting` is set on any list response: at most one interrupting announcement per user per rolling 24 hours and at most three per rolling 7 days, counted from `announcement_interruptions` rows. Over budget, the announcement degrades to a passive list item and is shown as interrupting on a later request. The modal is closable with `Escape` and with a `Later` control that records nothing and leaves the announcement undismissed; it never traps focus outside itself, never blocks navigation, and is suppressed entirely while an editing session is open on a sheet, document or form. Nothing in this feature may block work.
- **FR-F073-10:** `GET /api/v1/help/articles` returns the help index: `{ articles: [{ slug, title, section, updated_at }], locale, translation_fallback }` for the caller's effective F049 locale. With `context=<screen_key>` it returns only the articles mapped to that screen key by `help_article_contexts`, in `position` order, plus `matched: bool`; an unmapped or unknown `context` returns `matched: false` and the full index rather than an error.
- **FR-F073-11:** `GET /api/v1/help/articles/{slug}` returns `{ slug, version, locale, title, body_markdown, updated_at, translation_fallback }` for the highest `help_article_versions.version` of that article. Help articles are content, not code: an article is addressed by `slug`, immutable per version, and shipped as a signed content bundle imported by the worker job `announcements.import_help_bundle`, never authored through a tenant API. When the caller's locale has no `help_article_translations` row for that version, the response falls back to the article's `default_locale` and sets `translation_fallback: true`, matching the per-key fallback rule F049 already applies to UI strings.
- **FR-F073-12:** An unknown or withdrawn `slug` returns `404 not_found`; the drawer treats that code as a degraded read and renders the help index for the current context with a one-line note, so a stale contextual link is never a broken page. A help route is readable by any authenticated session and carries no tenant data, so it is served from a shared cache with a strong `ETag` per `(slug, version, locale)`.
- **FR-F073-13:** Announcement bodies and help article bodies are authored content and are untrusted at render time. Both are stored as Markdown and rendered through one allow-list renderer that can emit only paragraph, heading, list, emphasis, strong, inline code, code block and anchor nodes; a raw HTML node is dropped rather than escaped and displayed, and no image, iframe, object, style or script node is representable by the renderer's output type. Anchors are limited to `https:` URLs and same-origin application paths and are emitted with `rel="noopener noreferrer"`; any other scheme renders as plain text. Neither surface fetches remote content: every byte the panel and the drawer render arrives from the OpsHub API.
- **FR-F073-14:** The only per-user rows this feature stores are the `announcement_dismissals` row required to never re-show an announcement and the `announcement_interruptions` row required to enforce the cap in FR-F073-09. No open, view, scroll, dwell, hover or link-click is recorded for an announcement or a help article; the read figure available to an author is `dismissed_count` aggregated per announcement and tenant plus the publish-time `audience_size`, and no per-user reading history exists to query. No analytics script, tag manager, font, or content host is loaded by either surface, and no announcement or help payload leaves the deployment.
- **FR-F073-15:** Cross-tenant and permission negatives: a `tenant-admin` of tenant B receives `404 not_found` on `PATCH` or dismiss of a tenant-scope announcement of tenant A; an ordinary member receives `403 denied` on `POST /api/v1/announcements`; a `scoped-actor` token without the announcement scope receives `403 denied` on every mutation and may still read; all mutations require `Idempotency-Key` and an `If-Match` version on `PATCH`.

### Non-functional requirements

- **NFR-F073-01 Performance:** `GET /api/v1/announcements` p95 under 150 ms for a user with 200 published announcements in scope, evaluated with one query per request and no per-target round trip; `GET /api/v1/help/articles/{slug}` p95 under 80 ms warm and served with a 304 on a matching `If-None-Match`; publishing an announcement targeting 50,000 users computes `audience_size` in under 3 s; the panel adds no request to first paint — it loads after the route's own data.
- **NFR-F073-02 Security and privacy:** the allow-list renderer is the only path from stored content to the DOM and is fuzzed against an HTML injection corpus with zero escapes; platform-scope authoring is refused to every tenant role; dismissal and interruption rows are the only per-user records and are covered by the F027 export and erasure paths; no third-party origin appears in any request either surface makes.
- **NFR-F073-03 Accessibility:** the what's-new panel and the help drawer pass axe with zero serious or critical violations; both are reachable and operable from the keyboard, return focus to their trigger on close, and announce arrival through a polite live region; severity is carried by text and a labelled icon rather than colour alone; the interrupting modal honours `prefers-reduced-motion` and is escapable, meeting WCAG 2.2 AA including 2.2.1 on any timed dismissal.
- **NFR-F073-04 Reliability and observability:** the help bundle import job is idempotent per `bundle_id` and resumable, and a failed import leaves the previous version serving; metrics `announcement_published_total{scope,severity}`, `announcement_dismissed_total{severity}`, `announcement_interruptions_suppressed_total{reason}` and `help_article_fallback_total{locale}` are emitted; every request runs in a tracing span carrying `tenant_id`, `actor_id`, `correlation_id` and the announcement or article id.
- **NFR-F073-05 Localization and content integrity:** every announcement and article carries at least a `default_locale` translation, enforced by constraint; a missing translation falls back rather than failing; `content_hash` is a SHA-256 over the canonical serialization of severity, sorted target tuples, `learn_more_article_slug` and every translation, so supersession is decidable rather than judged; the imported bundle's signature is verified before any row is written.

### Scope

Included: the announcement aggregate with platform and tenant authoring, plan, entitlement, role and tenant targeting, permanent per-user dismissal, supersession on material change, severity with a server-enforced interruption budget, the what's-new panel, the help article store with versions and locale fallback, the contextual help drawer and index, the signed help bundle import job, and the shared allow-list content renderer.

Excluded: the notification inbox, channels, preferences, quiet hours and digests (F037); message catalogs, locale resolution and the pseudo-locale (F049); entitlement storage and the upgrade surface (F048); plan pricing and subscription changes (F064); the audit store and retention sweep (F027); the design tokens and primitive components both surfaces compose from (F062); marketing email and any outbound campaign; per-user analytics of any kind, which FR-F073-14 forbids rather than defers.

## 3. UX specification

- Entry points: the top-bar bell menu gains a `What's new` tab beside notifications; the top-bar `?` control and the `F1` key open the help drawer for the current route; a `Learn more` link on an announcement opens the drawer on that article without leaving the page.
- Primary flow: a user sees a dot on the bell, opens `What's new`, reads three items — one targeted at enterprise administrators, one plain product change, one dismissed last week shown only under `Show dismissed` — dismisses the top item, watches it leave the list, and does not see it again on reload. On the sheet grid they press `F1`, the drawer opens on `Working with columns` with two more contextual articles listed beneath it, they read it and press `Escape`, and the grid still has their selection and scroll position.
- The what's-new panel is 380 px wide, anchored under the bell, and lists severity chip, title, relative date, a two-line body clamp, and `Learn more` where present. A dismissed item is muted, keeps its dismissal date, and has no dismiss control — the action is gone because it cannot be undone.
- The interrupting modal is used only for `action_required` within budget: 480 px, title, body, the article link, `Later` and `Dismiss`. `Later` closes it and leaves the announcement in the panel. It never appears over an open editor.
- The help drawer is 420 px, docked right, does not overlay the content region's focus, and shows the article title, body, `Updated <date>`, a `Shown in English` note when `translation_fallback` is true, and the contextual article list. A `404 not_found` renders the index with `That article has moved` instead of an error page.
- States: loading uses list and article skeletons; empty is `Nothing new for you` with a link to the help index; error shows the banner with `correlation_id` and retry; denied applies to the authoring form only; stale and offline serve the last cached list read-only with an `Offline` chip; success is the item leaving the list without a toast.
- Responsive: under 768 px the panel and drawer become full-height sheets; both fit 320 px. Keyboard: `F1` opens and `Escape` closes the drawer, focus returns to the trigger, the panel is arrow-navigable, and the modal is escapable at all times.
- Font, icon and design tokens: Plus Jakarta Sans with JetBrains Mono for dates and counts (F062); icons `bell`, `sparkle`, `doc`, `warn`, `check`, `clock`, `chev` from `apps/web/src/ui/icons.ts`; every colour, space and radius from `apps/web/src/design/tokens.css`.
- Design: `design/artboards/Announcements.dc.html` draws the what's-new panel with a targeted item, a dismissed item and the contextual help drawer. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

### Rust backend

- Data access (decision section 2.1): `crates/persistence/src/announcements/` holds `AnnouncementRepository` (owns `announcements`, `announcement_translations`, `announcement_targets`, `announcement_dismissals`, `announcement_interruptions`) and `HelpArticleRepository` (owns `help_articles`, `help_article_versions`, `help_article_translations`, `help_article_contexts`). Child tables belong to their parent object type's repository, so no two classes write the same table. Named queries: `list_visible_for_actor`, `list_dismissed_for_actor`, `resolve_audience_size`, `insert_with_translations_and_targets`, `replace_translations`, `find_by_slug_and_scope`, `mark_superseded`, `record_dismissal`, `count_dismissals_by_tenant`, `count_interruptions_since`, `record_interruption`, `list_index_for_locale`, `list_contextual_slugs`, `load_article_version`, `upsert_bundle_version`. There is no generic query escape hatch. Every use case, handler and job below depends on these traits and contains no SQL; publishing (announcement row, translation rows, target rows, outbox, audit) and bundle import (article, version, translation and context rows) each run in one `UnitOfWork`.
- Tenant predicate exception, stated deliberately: a platform-scope announcement has `tenant_id is null` and is therefore not tenant-owned, so `list_visible_for_actor` is the one named query in this module that widens the base predicate, to `tenant_id is null or tenant_id = $tenant`. It is the only query permitted to do so, it is read-only, and every write path keeps the base tenant predicate.
- Domain entities in `crates/domain/src/announcements/`: `Announcement { id, tenant_id: Option<TenantId>, scope: Platform|Tenant, slug, severity: Info|Change|ActionRequired, state: Draft|Published|Retracted|Superseded, supersedes_id, content_hash, audience_size, published_at, expires_at, learn_more_article_slug, translations: Vec<Translation>, targets: Vec<Target>, version, audit fields }`, `Translation { locale, title, body_markdown }`, `Target { kind: Plan|Entitlement|Role|Tenant, value }`, `Dismissal { announcement_id, user_id, content_hash, dismissed_at }`, `HelpArticle { id, slug, default_locale, current_version, contexts: Vec<ContextKey> }`, `ArticleVersion { article_id, version, bundle_id, published_at, translations: Vec<Translation> }`. The three collections are loaded from and written back to their child tables by the repositories.
- Use cases: `list_announcements`, `publish_announcement`, `edit_announcement`, `supersede_announcement`, `dismiss_announcement`, `evaluate_targets(actor, targets)`, `interruption_budget(actor, now)`, `list_help_index`, `load_help_article`, `import_help_bundle`.
- Content rendering in `crates/domain/src/announcements/markdown.rs`: `render(md) -> SafeDoc`, where `SafeDoc` is an enum of the permitted node kinds only, so an image or script node is not constructible. The web client renders `SafeDoc` nodes, never a Markdown or HTML string, which is what makes FR-F073-13 a type-level guarantee rather than a filter.
- API endpoints (`services/api/src/announcements/`): `GET /api/v1/announcements`, `POST /api/v1/announcements`, `PATCH /api/v1/announcements/{id}`, `POST /api/v1/announcements/{id}/dismiss`, `GET /api/v1/help/articles`, `GET /api/v1/help/articles/{slug}`. DTOs: `AnnouncementResponse`, `Page<AnnouncementResponse>`, `PublishAnnouncementRequest`, `EditAnnouncementRequest { revision, expires_at?, translations? }`, `PublishAnnouncementResponse`, `HelpIndexResponse`, `HelpArticleResponse`. The DTOs keep `translations` and `targets` as JSON arrays and the repositories fan them out to rows on write and reassemble them on read.
- Worker job (`services/worker/src/announcements/`): `import_help_bundle` verifies the bundle signature, upserts `help_articles`, `help_article_versions`, `help_article_translations` and `help_article_contexts` per `bundle_id`, and is a no-op when the bundle is already applied.
- Events: `announcement.published.v1` and `announcement.dismissed.v1`, published through the transactional outbox with the payloads in FR-F073-05 and FR-F073-06.
- Authorization: read of both surfaces is any authenticated session; `scope: platform` authoring requires the `platform-operator` principal kind, which per `docs/authorization-model.md` section 2 is not a role and grants no tenant data access; `scope: tenant` authoring requires `tenant-admin`; dismissal is the `self` principal kind and applies to the caller only.
- Validation: `slug` matches `^[a-z0-9-]{3,64}$` and is unique per scope and tenant; `title` at most 120 graphemes and `body_markdown` at most 4,000; at least one translation whose `locale` equals the announcement's default; `targets` at most 50 rows; `expires_at` in the future; `learn_more_article_slug` must resolve to an existing article.
- Error mapping: `AnnouncementError::UnknownTarget → 400 invalid`, `::MaterialChange → 409 conflict`, `::AlreadyPublished → 409 conflict`, `::ForeignTenantTarget → 403 denied`, `::PlatformScopeDenied → 403 denied`, `::NotFound → 404 not_found`, `::BundleSignature → 503 unavailable`, `AuthzError::Denied → 403 denied`.

### Interface

Exact shapes. `T?` is nullable; a missing optional field and an explicit `null` are the same thing.
Timestamps are RFC 3339 UTC, ids are UUIDv7 strings, `version` increments by one per write. Unlisted
request fields are rejected with `400 invalid`. `Page<T>` and the error body (including its optional
`reason`) are F028's; `ActorContext` is F038's; the permission vocabulary and the `platform-operator`,
`tenant-admin` and `self` principal kinds are `docs/authorization-model.md` sections 2 and 3.

- Filter operators: `docs/filter-vocabulary.md`, subset `eq` — the two read routes offer one switch each and no authored predicate: `include_dismissed` selects on the caller's own dismissal state and `context` selects on a screen key, both equality. Visibility itself is not a filter parameter at all — it is the server-side target evaluation of FR-F073-04, which a caller can neither widen nor inspect.

**`Translation`** — used by both aggregates

| Field | Type | Required | Constraint |
|---|---|---|---|
| `locale` | string | yes | a BCP 47 tag F049 resolves; duplicate locale in one payload → `400 invalid` |
| `title` | string | yes | ≤ 120 graphemes |
| `body_markdown` | string | yes | ≤ 4,000 characters, and restricted Markdown: see the note below |

**Restricted Markdown on the wire.** `body_markdown` is the field FR-F073-01 and FR-F073-11 name, and
it is never a free Markdown string. It is the serialization of the server-side `SafeDoc` node union —
paragraph, heading, list, emphasis, strong, inline code, code block, anchor and nothing else — so a
raw HTML node cannot be represented in a stored or transmitted body, not merely filtered out of one.
`render(md) -> SafeDoc` runs on write, an authored body whose nodes fall outside the union is
`400 invalid`, and `SafeMarkdown` parses the same restricted grammar back into the same node union on
the client. Anchors carry only `https:` URLs and same-origin application paths; any other scheme is a
text node.

**`Target`**

| Field | Type | Required | Constraint |
|---|---|---|---|
| `kind` | `"plan" \| "entitlement" \| "role" \| "tenant"` | yes | |
| `value` | string | yes | `plan` in `free`, `team`, `enterprise` (`docs/packaging.md` section 1); `entitlement` an F048 key, matching only in state `active` or `trial`; `role` a role defined in `docs/authorization-model.md` section 3, matched at any scope; `tenant` a tenant id, and any tenant but the caller's → `403 denied` with `field_errors.targets = "foreign_tenant"`. An unknown value in any kind → `400 invalid` |

Evaluation is OR within a kind and AND across kinds; no target rows at all reaches every user in
scope. At most 50 target rows per announcement.

**`PublishAnnouncementRequest`** — `POST /api/v1/announcements`

| Field | Type | Required | Constraint |
|---|---|---|---|
| `scope` | `"platform" \| "tenant"` | yes | `platform` requires the `platform-operator` principal kind; any session holding a tenant role, `tenant-admin` included, gets `403 denied`. `tenant` requires `tenant-admin`, and from a `platform-operator` is `400 invalid` because that principal has no tenant |
| `slug` | string | yes | `^[a-z0-9-]{3,64}$`, unique per scope and tenant among live rows; a repeat → `409 conflict` with `field_errors.slug` |
| `severity` | `"info" \| "change" \| "action_required"` | yes | `action_required` without `learn_more_article_slug` → `400 invalid`, matching the table's own check constraint |
| `default_locale` | string | yes | the locale the fallback resolves to; must equal the `locale` of one supplied translation. Derived from the `announcements.default_locale` column and this section's Validation bullet, which FR-F073-02's abbreviated body does not name |
| `translations` | Translation[] | yes | 1–50 entries, one of them matching `default_locale`, else `400 invalid` with `field_errors.translations` |
| `targets` | Target[] | no | default empty, which reaches every user in scope; ≤ 50 rows |
| `learn_more_article_slug` | string? | no | must resolve to an existing `help_articles.slug`, else `400 invalid` |
| `expires_at` | timestamp? | no | must be in the future |
| `publish` | bool | no | default `false` leaves `state: "draft"`; `true` publishes immediately, setting `published_at`, computing `audience_size` and emitting `announcement.published.v1` |

`tenant_id` is never a body field: it is written from the session, which is why a tenant author cannot
publish into another tenant even by naming one.

**`PublishAnnouncementResponse`** — `201`

| Field | Type | Notes |
|---|---|---|
| `id` | uuid | |
| `slug` | string | |
| `state` | `"draft" \| "published" \| "retracted" \| "superseded"` | |
| `audience_size` | integer? | `null` while `draft`; a publish-time snapshot once published and never recomputed, so it can never become a live count of who is reading |
| `content_hash` | string | SHA-256 hex over the canonical serialization of `severity`, the sorted target tuples, `learn_more_article_slug` and every translation |
| `version` | integer | pass as `If-Match` on `PATCH` |

**`EditAnnouncementRequest`** — `PATCH /api/v1/announcements/{id}`, `If-Match` required

| Field | Type | Required | Constraint |
|---|---|---|---|
| `revision` | `"editorial"` | yes | the only accepted value; it is an assertion the server verifies, not a mode it trusts |
| `expires_at` | timestamp? | no | future, or explicit `null` to clear |
| `translations` | Translation[] | no | each edited body must differ from the stored body by at most 5% of its NFC-normalized, whitespace-collapsed token count |

Any change to `severity`, the target set or `learn_more_article_slug`, or a body past the 5% bound, is
a **material change**: `409 conflict` with `field_errors.revision = "material"` and nothing written.
The path forward is a new announcement carrying `supersedes_id`, which sets the original to
`superseded`; the replacement has its own `content_hash`, carries no dismissal rows, and therefore
appears once to everyone it targets, while the superseded row stays dismissed for whoever dismissed it.

**`AnnouncementResponse`** — the item of `GET /api/v1/announcements`

| Field | Type | Notes |
|---|---|---|
| `id` | uuid | |
| `slug` | string | |
| `scope` | `"platform" \| "tenant"` | |
| `severity` | `"info" \| "change" \| "action_required"` | carried as text by the client, never colour alone |
| `title` / `body_markdown` | string | the caller's locale, or the `default_locale` when it has no translation |
| `learn_more_article_slug` | string? | |
| `published_at` | timestamp | the sort key, newest first |
| `expires_at` | timestamp? | |
| `dismissed` | bool | `true` only in an `include_dismissed=true` response, since a dismissed item is otherwise absent |
| `interrupting` | bool | `false` for every `info` and `change`; `true` only for an `action_required` that is inside the FR-F073-09 budget at the moment this response was assembled |
| `translation_fallback` | bool | `true` when the body came from `default_locale` rather than the caller's locale |

**`HelpIndexResponse`** — `GET /api/v1/help/articles`

| Field | Type | Notes |
|---|---|---|
| `articles` | `{ slug, title, section, updated_at }[]` | in `position` order when `context` matched, otherwise by `section` then `title` |
| `locale` | string | the caller's effective F049 locale |
| `translation_fallback` | bool | `true` when any listed title fell back to its article's `default_locale` |
| `matched` | bool | present only when `context` was supplied; `false` for an unknown or unmapped key, which returns the full index rather than an error |

**`HelpArticleResponse`** — `GET /api/v1/help/articles/{slug}`

| Field | Type | Notes |
|---|---|---|
| `slug` | string | |
| `version` | integer | the highest `help_article_versions.version`; a version is immutable, which is what makes the `ETag` strong |
| `locale` | string | the locale actually served |
| `title` / `body_markdown` | string | restricted Markdown, as above |
| `updated_at` | timestamp | |
| `translation_fallback` | bool | `true` when served from `default_locale` |

Both help routes are readable by any authenticated session, carry no tenant data, and are served from
a shared cache with a strong `ETag` per `(slug, version, locale)`; a matching `If-None-Match` is `304`.

**List parameters**

| Route | Parameter | Type | Constraint |
|---|---|---|---|
| `GET /api/v1/announcements` | `include_dismissed` | bool? | default `false`; `true` returns dismissed items with `dismissed: true` |
| | `cursor` | string? | F028's opaque signed cursor |
| | `limit` | integer? | 1–50, default 20 |
| `GET /api/v1/help/articles` | `context` | string? | a screen key; unknown or unmapped is `matched: false`, never `404` |

`GET /api/v1/announcements` returns F028's `Page<AnnouncementResponse>` sorted `published_at`
descending then `id`. `GET /api/v1/help/articles` returns `HelpIndexResponse` and is not paginated:
the index is deployment-wide content, bounded by the imported bundle.

**Status codes**

| Status | Produced by |
|---|---|
| `200` | the list, both help routes |
| `201` | `POST /api/v1/announcements` |
| `204` | `POST /api/v1/announcements/{id}/dismiss`, including the second and every later call |
| `304` | a help article whose `ETag` matches `If-None-Match` |
| `400 invalid` | an unknown target value, a slug outside the pattern, a missing `default_locale` translation, `action_required` without an article, a past `expires_at`, a `tenant`-scope body from a `platform-operator`, or an unlisted field |
| `403 denied` | `scope: "platform"` from any tenant role, authoring from an ordinary member, a `targets` entry naming a foreign tenant, and a `scoped-actor` token without the announcement scope on any mutation — that token may still read |
| `404 not_found` | an announcement of another tenant on `PATCH` or dismiss, and an unknown or withdrawn help `slug`, which the drawer treats as a degraded read and answers with the contextual index |
| `409 conflict` | a material change under `revision: "editorial"`, a duplicate `slug`, publishing an already-published announcement, a stale `If-Match`, and an `Idempotency-Key` replayed with a different body |
| `503 unavailable` | `BundleSignature` — the help bundle failed verification, so the previous version keeps serving and nothing is written |

Every mutation requires `Idempotency-Key`, and `PATCH` additionally requires `If-Match`. Dismissal is
idempotent by its primary key rather than by the key alone, so a replay writes nothing either way.

### Use case signatures

In `crates/domain/src/announcements/`; the import job in `services/worker/src/announcements/`. `Ctx`
is F038's `ActorContext`; `JobCtx` is the worker's job context carrying correlation id and no actor.

```rust
fn list_announcements(ctx: &Ctx, repo: &dyn AnnouncementRepository, entitlements: &dyn EntitlementPort, include_dismissed: bool, page: Cursor) -> Result<Page<VisibleAnnouncement>, DomainError>;
fn publish_announcement(ctx: &Ctx, uow: &mut UnitOfWork, req: PublishAnnouncement) -> Result<Announcement, DomainError>;
fn edit_announcement(ctx: &Ctx, uow: &mut UnitOfWork, id: AnnouncementId, expected: Version, req: EditAnnouncement) -> Result<Announcement, DomainError>;
fn supersede_announcement(ctx: &Ctx, uow: &mut UnitOfWork, original: AnnouncementId, req: PublishAnnouncement) -> Result<Announcement, DomainError>;
fn dismiss_announcement(ctx: &Ctx, uow: &mut UnitOfWork, id: AnnouncementId) -> Result<(), DomainError>;
fn evaluate_targets(actor: &Ctx, targets: &[Target], entitlements: &TenantEntitlements) -> bool;
fn interruption_budget(ctx: &Ctx, repo: &dyn AnnouncementRepository, now: Timestamp) -> Result<Budget, DomainError>;
fn list_help_index(ctx: &Ctx, repo: &dyn HelpArticleRepository, locale: &Locale, context: Option<ContextKey>) -> Result<HelpIndex, DomainError>;
fn load_help_article(ctx: &Ctx, repo: &dyn HelpArticleRepository, slug: &Slug, locale: &Locale) -> Result<ArticleView, DomainError>;
fn import_help_bundle(ctx: &JobCtx, uow: &mut UnitOfWork, bundle: SignedBundle, verifier: &dyn BundleVerifier) -> Result<ImportReport, DomainError>;
fn render(md: &str) -> Result<SafeDoc, ContentError>;
```

`Budget` is `{ remaining_today: u8, remaining_week: u8 }` and is what sets `interrupting` on a list
response — the cap is applied server-side before the field is written, never in the client.
`evaluate_targets` and `render` are pure and take no repository, which is what lets the target truth
table and the injection corpus run without a database. A use case never takes a pool or a connection
and never returns a database row type.

Transaction boundaries:

- `publish_announcement` writes the `announcements` row, every `announcement_translations` row, every
  `announcement_targets` row, the `audience_size` snapshot, the audit row and the
  `announcement.published.v1` outbox row in **one `UnitOfWork`**. The default-locale translation
  constraint and the target set are only meaningful against the complete set, and an announcement
  visible with a partial target set would reach the wrong people.
- `supersede_announcement` writes the replacement and flips the original to `superseded` in **one
  `UnitOfWork`**, so no reader ever sees both live and neither sees a gap where neither is.
- `edit_announcement` writes the editorial classification's result — the changed translation rows,
  `expires_at`, the version bump and the audit row — in one `UnitOfWork` under `If-Match`. The
  `content_hash` is recomputed inside it, because supersession is decided from that hash.
- `dismiss_announcement` writes the `announcement_dismissals` row and the
  `announcement.dismissed.v1` outbox row in one `UnitOfWork`; the row's primary key makes the second
  call a no-op inside the same boundary rather than a second event.
- Recording an interruption writes the `announcement_interruptions` row in the same `UnitOfWork` that
  serves the list response's `interrupting: true`, so a modal counted against the budget is always a
  modal the caller was actually told to show.
- `import_help_bundle` writes the `help_articles`, `help_article_versions`,
  `help_article_translations` and `help_article_contexts` rows for one `bundle_id` in **one
  `UnitOfWork`**. That is what makes a failed import leave the previous version serving.
- `list_announcements`, `list_help_index` and `load_help_article` are reads and take repositories,
  never a `UnitOfWork`.

### PostgreSQL/SQLx

- Migration `*_announcements_*.sql` creates `announcements(id uuid pk, tenant_id uuid references tenants(id) on delete cascade, scope text not null check (scope in ('platform','tenant')), slug text not null, severity text not null check (severity in ('info','change','action_required')), state text not null default 'draft' check (state in ('draft','published','retracted','superseded')), supersedes_id uuid references announcements(id) on delete restrict, default_locale text not null, content_hash text not null, audience_size integer, learn_more_article_slug text, published_at timestamptz, expires_at timestamptz, version bigint not null default 1, created_by uuid not null, created_at timestamptz not null, updated_by uuid not null, updated_at timestamptz not null, deleted_at timestamptz, check ((scope = 'tenant') = (tenant_id is not null)), check (severity <> 'action_required' or learn_more_article_slug is not null))`.
- Normalized sets (decision section 2, no array columns): `announcement_translations(announcement_id uuid references announcements(id) on delete cascade, locale text not null, title text not null, body_markdown text not null, primary key (announcement_id, locale))` replaces any per-locale column pair; `announcement_targets(announcement_id uuid references announcements(id) on delete cascade, kind text not null check (kind in ('plan','entitlement','role','tenant')), value text not null, primary key (announcement_id, kind, value))` replaces a `targets text[]`, so a target is joinable, indexable and auditable and a plan value is constrained rather than free text.
- `announcement_dismissals(announcement_id uuid not null references announcements(id) on delete cascade, tenant_id uuid not null references tenants(id) on delete cascade, user_id uuid not null references users(id) on delete cascade, content_hash text not null, dismissed_at timestamptz not null, primary key (announcement_id, user_id))` — the primary key is what makes dismissal idempotent and single. `announcement_interruptions(user_id uuid not null references users(id) on delete cascade, announcement_id uuid not null references announcements(id) on delete cascade, tenant_id uuid not null, shown_at timestamptz not null, primary key (user_id, announcement_id))` holds only the budget ledger.
- Help content: `help_articles(id uuid pk, slug text not null unique, section text not null, default_locale text not null, current_version integer not null default 1, created_at timestamptz not null, updated_at timestamptz not null)`, `help_article_versions(article_id uuid references help_articles(id) on delete cascade, version integer not null, bundle_id text not null, published_at timestamptz not null, primary key (article_id, version))`, `help_article_translations(article_id uuid, version integer, locale text not null, title text not null, body_markdown text not null, primary key (article_id, version, locale), foreign key (article_id, version) references help_article_versions(article_id, version) on delete cascade)`, `help_article_contexts(context_key text not null, article_id uuid not null references help_articles(id) on delete cascade, position smallint not null default 0, primary key (context_key, article_id))`. `help_article_contexts` is a table rather than a column list because the mapping is many-to-many and the drawer orders by `position`.
- `jsonb` audit: this module declares no `jsonb` column. Severity, state, scope and target kind are closed enums with no member data, so decision section 2 keeps them as `text` with a check constraint; the target set, the translations and the context mapping are all enumerable and are child tables. The event payloads that carry a schema-less snapshot live in the F004 outbox table, which this feature does not own.
- Invariants: one dismissal per `(announcement_id, user_id)` and no delete path, so dismissal is permanent; one interruption ledger row per `(user_id, announcement_id)`, so a modal is shown at most once per announcement; `announcements` unique on `(tenant_id, slug)` for tenant scope and on `(slug)` where `tenant_id is null` for platform scope, both partial unique indexes filtered on `deleted_at is null`; at least one `announcement_translations` row matching `announcements.default_locale`, enforced by the repository inside the publish transaction; `supersedes_id` must reference an announcement of the same scope and tenant; `help_article_versions.version` monotonic per article; at least one `help_article_translations` row per version matching the article's `default_locale`.
- Indexes: `announcements(tenant_id, state, published_at desc) where deleted_at is null` for the list; `announcements(state, published_at desc) where tenant_id is null` for the platform slice; `announcement_targets(kind, value)` for audience resolution; `announcement_dismissals(user_id, announcement_id)` for the visibility filter; `announcement_interruptions(user_id, shown_at desc)` for the rolling budget window; `help_articles(slug)` unique; `help_article_translations(article_id, version, locale)`; `help_article_contexts(context_key, position)`.
- Schema change staging (decision section 2.2): this is the expand phase of a new module — every table is created new, nothing is backfilled, no existing read path changes, and the two partial unique indexes are created `CONCURRENTLY` outside the transactional part of the migration.
- Audit events: `announcement.published`, `announcement.edited`, `announcement.superseded`, `announcement.retracted`, `help-bundle.imported`. Dismissal is not audited as an administrative action; it is the user's own preference row and is covered by the F027 subject-access export.
- Retention and deletion: announcements soft-delete and are purged with their tenant; `announcement_interruptions` rows older than 90 days are swept, since the budget window is 7 days; `announcement_dismissals` is exempt from every sweep because expiring a dismissal would resurrect an announcement; help content is deployment-wide and is replaced by bundle import rather than deleted. Rollback drops the nine tables, children before parents.

### React/TypeScript

- Surfaces in `apps/web/src/features/announcements/`: `WhatsNewPanel.tsx`, `AnnouncementItem.tsx`, `InterruptModal.tsx`, `HelpDrawer.tsx`, `HelpIndexList.tsx`, `SafeMarkdown.tsx`, `useHelpContext.ts`, `api.ts`, `hooks.ts`. `SafeMarkdown` renders the `SafeDoc` node union and has no path that accepts a string of HTML.
- State: TanStack Query keys `['announcements', includeDismissed, cursor]`, `['help-index', locale, contextKey]`, `['help-article', slug, locale]`; dismissing mutates optimistically and invalidates the first key only. `useHelpContext` derives the screen key from the TanStack Router match, so the drawer follows the route without any screen registering itself twice.
- The panel and drawer mount in the F062 app shell, import only from `apps/web/src/ui`, and use `className` for layout alone; the severity chip and the `Offline` chip are enumerated variants, not composed ones.
- Telemetry: none. FR-F073-14 makes the absence of client instrumentation on these two surfaces a requirement, and the frontend test lane asserts that neither component issues a request to any origin other than the API.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F073-01 through FR-F073-15 and NFR-F073-01 through NFR-F073-05 in `testing/features/F073/requirements/cases.md`
- [ ] Failure and edge-case tests: expired announcement, superseded announcement still dismissed, editorial edit at exactly the 5% token threshold, `action_required` without an article, budget exhausted then replenished, unknown help slug, missing translation, unsigned bundle
- [ ] Permission-negative and tenant-isolation tests: `tenant-admin` refused platform scope, member refused authoring, foreign-tenant target refused, foreign announcement returns `404 not_found`, dismissal of another user's announcement impossible by construction
- [ ] Rust unit tests: target evaluation truth table, interruption budget arithmetic across the 24 h and 7 d windows, `content_hash` canonicalization, token-distance editorial classifier, `SafeDoc` renderer against the injection corpus
- [ ] API contract and integration tests: every route above with success and each mapped error code
- [ ] Database migration and constraint tests: partial unique indexes, dismissal primary key, severity and scope checks, cascade behaviour, rollback
- [ ] React component tests: panel, item, dismissed state, modal, drawer, index fallback, offline chip
- [ ] Browser E2E tests: dismiss and reload, contextual help from the grid, stale link degrading to the index
- [ ] Accessibility tests: axe on both surfaces, focus return, live-region announcement, severity not colour-only, escapable modal
- [ ] Performance and load tests: list p95 with 200 announcements, article read with `ETag`, 50,000-user audience resolution

### Fast fanout configuration

- Test harness path: `testing/features/F073/`
- Feature flag: `F073_FEATURE`
- Fixture and seed factory: `testing/fixtures/announcements.rs` builds tenant A on `enterprise` with the `assets` entitlement and tenant B on `free`, a `platform-operator` principal, a `tenant-admin` and a member in each tenant, six announcements across the three severities and four target kinds, one superseded pair, one pre-dismissed announcement, and a help bundle of eight articles in `en-US` with four `de-DE` translations and six context mappings
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC, a fixed bundle signing key, and a fixed token corpus for the editorial classifier
- Mock and stub contracts: F048 entitlement lookup stub returning a scripted plan and entitlement set per tenant; F049 locale resolver stub; F037 delivery registry in memory; a signed and an unsigned help bundle fixture
- Parallel isolation: one schema per test worker, tenant ids per test, help content seeded per schema so the shared cache cannot leak across workers
- Targeted command: `cargo xtask test-feature F073`
- Full command: `cargo xtask test-all`
- CI artifact and evidence: `testing/evidence/F073/`

## 6. Acceptance criteria

```gherkin
Feature: Announcements and in-app help

Scenario: An enterprise-only change is not announced to a free tenant
  Given a published platform announcement targeted plan enterprise and entitlement assets
  When a member of a free tenant requests GET /api/v1/announcements
  Then the announcement is absent from the response
  And an enterprise tenant-admin holding the assets entitlement receives it with severity change

Scenario: Dismissal is permanent and a material change is a new announcement
  Given a user who dismissed announcement "approval-escalation"
  When the author changes its severity to action_required and retries the edit
  Then the edit returns 409 conflict with field_errors.revision material
  And publishing a replacement with supersedes_id sets the original to superseded
  And the user sees the replacement once and never sees the superseded announcement again

Scenario: The interruption budget degrades rather than interrupts
  Given a user who was shown an interrupting announcement 4 hours ago
  When a second action_required announcement becomes visible to them
  Then the list returns it with interrupting false and it appears only in the what's-new panel
  And announcement_interruptions_suppressed_total increments with reason daily_cap

Scenario: A stale help link degrades to the index in the reader's language
  Given a de-DE user opening a learn-more link whose slug was withdrawn
  When the drawer requests GET /api/v1/help/articles/{slug}
  Then the response is 404 not_found and the drawer renders the contextual index
  And an article with no de-DE translation renders the default locale with translation_fallback true
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F002 (tenants, users, groups, and the `tenants.plan` column targeting reads); F037 (the bell surface the what's-new tab sits beside and its delivery registry); F048 entitlement state and F049 locale resolution, both read through stubs until they land; F062 primitives; decisions sections 2, 2.1, 2.2, 3
- Blocks: none
- Conflicts with: none — the `announcements` module paths are owned by no other feature
- External dependencies: none. Both surfaces are served entirely by the deployment, which is what FR-F073-14 requires
- Risks and mitigations: announcement fatigue turning the panel into an advert, mitigated by mandatory targeting review at publish and the severity rules in FR-F073-08; the 5% editorial threshold misclassifying a genuine correction, mitigated by the author's ability to publish a superseding announcement instead and by the classifier's fixed corpus test; content injection through an authored body, mitigated by the `SafeDoc` node union and the fuzz corpus in NFR-F073-02; the platform-scope tenant predicate exception being copied into a write path, mitigated by it being one named read-only query that `check-persistence` and review both look at
- Open questions: none

## 7.1 Amendments

Every change made to this ticket after it was first accepted, newest first.

| Date | Caused by | What changed | Why |
|---|---|---|---|
| 2026-09-04 | F073 interface work | The Interface section defines `body_markdown` as the serialization of the server-side `SafeDoc` node union — restricted Markdown, rejected at authoring time when a node falls outside the union — rather than as a free Markdown string | FR-F073-01 and FR-F073-11 put `body_markdown` on the wire while FR-F073-13 and `SafeMarkdown` make the node union the only path to the DOM; without saying which the string is, one implementer ships a server-rendered union and another ships a client-side sanitiser, and only one of those is the type-level guarantee NFR-F073-02 is fuzzed against |
| 2026-09-04 | F073 interface work | `PublishAnnouncementRequest` carries a required `default_locale` | The DDL declares `announcements.default_locale not null` and the validation bullet requires a translation matching it, but FR-F073-02's body listed no field that could supply it |

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F002 and F037 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F073/`
- [ ] Migration file name and owned paths claimed
- [ ] Signed and unsigned help bundle fixtures available under `testing/fixtures/`

## 9. Exit criteria — accepted and releasable

- [ ] All FR and NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit, API, database, React, E2E, permission-negative, accessibility and performance gates pass
- [ ] Audit and outbox events verified for publish, edit, supersede and dismiss
- [ ] The renderer fuzz corpus runs clean and the frontend lane proves no third-party origin is contacted
- [ ] All changed files at most 500 lines; `cargo xtask validate-tickets`, `check-contracts`, `check-persistence`, `check-roles` and `check-design` pass
- [ ] Rollback verified: disable `F073_FEATURE`, run the down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- People see what changed in OpsHub without leaving the product: a what's-new panel targeted by plan, entitlement, role and tenant, so a capability a tenant does not have is never announced to it. Dismissing an item is permanent, a material change arrives as a new announcement rather than a resurrected one, and only an announcement that requires action may interrupt — at most once a day and three times a week. Help articles open in a drawer beside the screen you are on, in your language, falling back to English when a translation is missing and to the index when a link is stale.
- No reading behaviour is recorded and nothing is sent anywhere: the only per-user rows are your dismissal and the interruption ledger that caps the modal.
- Migration adds `announcements`, `announcement_translations`, `announcement_targets`, `announcement_dismissals`, `announcement_interruptions`, `help_articles`, `help_article_versions`, `help_article_translations` and `help_article_contexts`; rollback drops them. Feature is off by default behind `F073_FEATURE`.
