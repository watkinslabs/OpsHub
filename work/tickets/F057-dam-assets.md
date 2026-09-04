---
id: F057
type: feature
status: planned
priority: P2
owner: platform
estimate: 8
target_milestone: M7
parent_epic: E008
depends_on: [F017, F020, F048]
blocks: []
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/assets/**, crates/persistence/src/assets/**, services/api/src/assets/**, apps/web/src/features/assets/**, services/api/migrations/*_assets_*.sql, services/worker/src/assets/**, testing/features/F057/**]
feature_flag: F057_FEATURE
flag_default: off
branch: f057-dam-assets
started_at: null
finished_at: null
---

# F057 — DAM assets

## 1. Identity and dates

- Branch: `f057-dam-assets`
- Capability area: advanced modules, digital asset management (spec 5.11 "assets, metadata, renditions, approvals, collections, and usage rights"; 5.4b COLLAB-04 approval instance; 5.8 files scanned, checksummed, versioned, served by expiring URLs; section 10 entitlement records plus feature flags)
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 5, 7; `docs/capability-contracts.md` row F057
- Module slug: `assets`

## 2. Requirement specification

### Problem and user outcome

Marketing and brand teams keep logos, photos, and videos as loose attachments on rows, so nobody knows which version is approved, whether usage rights have expired, or where a file is used. They need a governed library over the existing file service.

As an asset editor with the DAM entitlement, I want to register files as assets with typed metadata, usage rights, renditions, approval state, and collections, so that approved brand material is discoverable and rights-safe across the tenant.

### Functional requirements

- **FR-F057-01:** An actor with `asset-editor` and the tenant entitlement `dam` can create an asset from an existing scanned `file_id` (F017 scan state `clean`) with `title`, `description`, `tags` (≤ 50), `metadata` (typed fields declared per tenant schema), and optional `collection_ids`; the request and response keep `tags` as a JSON string array and `metadata` as a JSON object, while the server resolves each tag to an `asset_tag_definitions` row and writes one `asset_tags` row per tag and one `asset_metadata_values` row per supplied field; the response returns UUIDv7 `id`, `version` 1, `approval_state: draft`, and `rendition_state: pending`.
- **FR-F057-02:** Creating an asset from a file whose scan state is not `clean` returns `invalid` with `field_errors.file_id = "not_scanned"`; a file the actor cannot read returns `not_found`.
- **FR-F057-03:** On `asset.created.v1` and on every new file version, the worker generates renditions `thumbnail` (256 px), `preview` (1280 px), and `web` (1920 px, JPEG or WebP) for image assets, and `poster` plus `preview` (720p H.264) for video assets, storing each in object storage with checksum and publishing `asset.rendition-ready.v1` per kind.
- **FR-F057-04:** `GET /api/v1/assets/{id}/renditions/{kind}` returns a 302 redirect to a signed object URL expiring in 15 minutes when the rendition is ready, `404 not_found` for an unknown kind, and `409 conflict` with `rendition_state: pending|failed` when not ready.
- **FR-F057-05:** `PUT /api/v1/assets/{id}/rights` sets `{ license: owned|licensed|royalty_free|restricted, licensor?, valid_from?, valid_until?, territories: [ISO-3166]?, channels: [web|print|social|internal]?, notes? }` and publishes `asset.rights-updated.v1`; the request and response keep `territories` and `channels` as JSON string arrays, while the server replaces the asset's `asset_rights_territories` rows (each `code` a foreign key into the seeded `asset_territory_codes` lookup) and `asset_rights_channels` rows, so a territory or channel can be joined, filtered, and audited; an asset whose `valid_until` is past is `rights_state: expired` on every read.
- **FR-F057-06:** Approval uses F020: `PATCH /api/v1/assets/{id}` with `{ approval: request }` creates an approval with the tenant DAM policy; the F020 decision sets `approval_state` to `approved` or `rejected` with decider and reason, and only `approved` assets whose rights are not `expired` are `usable: true`.
- **FR-F057-07:** `GET /api/v1/assets` lists with cursor paging and filters `q` (matched against the `assets.search` vector built from title, description, tag labels, and text metadata values), `tag` (repeatable, joined through `asset_tags`), `territory` and `channel` (joined through `asset_rights_territories` and `asset_rights_channels`), `collection_id`, `approval_state`, `rights_state`, `mime_prefix` (the typed `assets.mime_prefix` column), `usable`, and sorts by `title`, `created_at`, or `updated_at`; hidden assets never appear for actors without read ACL.
- **FR-F057-08:** `POST /api/v1/asset-collections` creates a collection with `name`, `description`, `visibility: private|workspace|tenant`, and `parent_id?` (depth ≤ 5); `PUT /api/v1/asset-collections/{id}/assets` replaces membership with an ordered list of asset IDs (≤ 5,000) and requires read access to every asset.
- **FR-F057-09:** `DELETE /api/v1/assets/{id}` archives the asset (`archived_at` set, `usable: false`), publishes `asset.archived.v1`, keeps renditions for the tenant retention window, and removes the asset from collection listings while preserving `asset_collection_items` rows for restore.
- **FR-F057-10:** Every mutation requires `Idempotency-Key` and `If-Match`, writes an audit event with diff, and publishes `asset.updated.v1` for metadata, tag, and approval-state changes with `changed_fields`; a tag or metadata change diffs the `asset_tags` and `asset_metadata_values` rows added and removed, and `changed_fields` still reports `tags` and `metadata` so consumers are unchanged.
- **FR-F057-11:** A tenant without the `dam` entitlement or with `F057_FEATURE` off receives `denied` with `field_errors.entitlement = "dam"` on every asset and collection route; foreign tenants receive `not_found`.
- **FR-F057-12:** The tenant metadata schema is rows in `asset_metadata_fields` (up to 30 per tenant) of `kind` `text|number|date|select|person`, with `select` choices in `asset_metadata_field_options`; a value violating the declared kind returns `invalid` with `field_errors.metadata.<key>`, an unknown key returns `unknown_key`, and removing a field is rejected while any `asset_metadata_values` row references it.
- **FR-F057-13:** The web library renders a virtualized grid of thumbnails with approval and rights badges, a detail drawer with renditions, rights, approval history, and collections, and a collection tree; unusable assets show a `Not usable` badge with the reason.
- **FR-F057-14:** Rendition generation failure after 3 attempts sets `rendition_state: failed` with `error_code` in `{ unsupported_format, too_large, timeout }` and the UI offers `Retry` to editors.

### Non-functional requirements

- **NFR-F057-01 Performance:** asset list of 50 items with thumbnails responds in under 500 ms p95 for a library of 200,000 assets; thumbnail renditions are ready within 60 s p95 of upload for images up to 50 MB.
- **NFR-F057-02 Security/privacy:** rendition URLs are signed, expire in 15 minutes, and are never logged; entitlement, tenant, and ACL checks run in the domain service; rights notes are excluded from search indexes shared with other modules.
- **NFR-F057-03 Accessibility:** library grid, detail drawer, and collection tree pass axe with zero serious violations; every thumbnail has alt text from `title`; badges carry text, not color alone.
- **NFR-F057-04 Reliability/observability:** rendition jobs are idempotent on `(asset_id, file_version_id, kind)`, retried 3 times with backoff, dead-lettered after that, and expose `asset_rendition_duration_ms` and `asset_rendition_failures_total` with `kind` and `error_code` labels.

### Scope

Included: asset registration over F017 files, typed metadata schema, tags, renditions worker, usage rights with expiry, approval via F020, collections tree and membership, archive, library UI, search filters.

Excluded: uploading files (F017 owns uploads and versions), proofing markup (F017), public brand portals (F059 publishes collections later), AI tagging (F040), external DAM sync (F030).

## 3. UX specification

- Personas: brand manager (approves, sets rights), designer (registers assets, builds collections), marketer (searches usable assets).
- Entry points: workspace navigation `Assets`; row attachment menu `Register as asset`; routes `/w/{workspace_id}/assets`, `/w/{workspace_id}/assets/{asset_id}`, `/w/{workspace_id}/assets/collections/{collection_id}`.
- Primary flow: open Assets, click `Register asset`, choose a clean file, fill title, tags, and metadata, save; thumbnails appear as renditions complete; set rights with a validity window; request approval; approver decides from F020 inbox; asset shows `Usable`; add it to a collection.
- Loading: skeleton tiles; Empty: `Register your first asset`; Error: banner with `correlation_id` and retry; Success: toast on register, rights saved, approval requested; Stale/conflict: drawer banner `This asset changed` with reload; Offline: mutations disabled with badge.
- Permission-denied: unentitled tenants see the module upsell; viewers see the library without register, rights, or approval controls; assets outside the actor's ACL never render.
- Responsive: grid shows 2 columns under 640 px and 4 under 1024 px; the detail drawer becomes a full-screen sheet under 768 px; collection tree collapses to a drawer.
- Keyboard: arrow keys move between tiles, `Enter` opens the drawer, `Escape` closes it, `Tab` cycles renditions and actions; collection tree uses `ArrowRight/Left` to expand and collapse; reduced motion disables tile fade-in.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide `Image`, `Film`, `FolderTree`, `BadgeCheck`, `ShieldAlert`, `Archive`; tokens from `apps/web/src/design/tokens.css`.

- Design: `design/artboards/Assets.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

### Rust backend

- Data access (decision section 2.1): `crates/persistence/src/assets/` holds `AssetRepository` (owns `assets`, `asset_tags`, `asset_metadata_values`), `AssetTagRepository` (`asset_tag_definitions`), `AssetRenditionRepository` (`asset_renditions`), `AssetRightsRepository` (`asset_rights`, `asset_rights_territories`, `asset_rights_channels`, and the migration-seeded read-only `asset_territory_codes`), `AssetCollectionRepository` (`asset_collections`, `asset_collection_items`), and `AssetMetadataFieldRepository` (`asset_metadata_fields`, `asset_metadata_field_options`). Junction and child tables belong to the repository of their parent object type, so no two classes write the same table. Named queries: `insert_asset`, `find_asset_for_actor`, `list_assets_page`, `update_asset_fields`, `replace_asset_tags`, `replace_asset_metadata_values`, `refresh_search_vector`, `archive_asset`, `resolve_or_create_tag_definitions`, `list_tag_definitions_with_counts`, `upsert_rendition`, `find_rendition`, `mark_rendition_failed`, `count_rendition_attempts`, `upsert_rights`, `replace_rights_territories`, `replace_rights_channels`, `list_rights_expiring_before`, `list_territory_codes`, `create_collection`, `list_collection_tree`, `replace_collection_items`, `list_collection_assets`, `list_metadata_fields`, `count_values_for_field`. No repository exposes a generic query escape hatch.
- Every use case below depends on those repository traits and contains no SQL; `crates/domain/src/assets/`, the `services/api/src/assets/` handlers, the rendition worker, the approval consumer, and the rights-expiry sweep (`AssetRightsRepository::list_rights_expiring_before` feeding the list filter and the F027 retention pass) issue no `sqlx::query*` call and open no connection. Register, update, rights replacement, and collection membership replacement are multi-table writes and run in one `UnitOfWork`: the asset row, its tag rows, its metadata-value rows, its collection-item rows, the audit row, and the outbox row commit together or not at all.
- Canonical contract: aggregate `asset`; module `assets`; routes `GET /api/v1/assets`, `POST /api/v1/assets`, `GET /api/v1/assets/{id}`, `PATCH /api/v1/assets/{id}`, `DELETE /api/v1/assets/{id}`, `PUT /api/v1/assets/{id}/rights`, `GET /api/v1/assets/{id}/renditions/{kind}`, `GET /api/v1/asset-collections`, `POST /api/v1/asset-collections`, `PUT /api/v1/asset-collections/{id}/assets`; events `asset.created.v1`, `asset.updated.v1`, `asset.rendition-ready.v1`, `asset.rights-updated.v1`, `asset.archived.v1`; tables `assets`, `asset_renditions`, `asset_rights`, `asset_collections`, `asset_collection_items`; mutation role `asset-editor`.
- Domain entities in `crates/domain/src/assets/`: `Asset { id, tenant_id, workspace_id, file_id, current_file_version_id, title, description, mime_type, mime_prefix, byte_size, width, height, duration_ms, tags: Vec<Tag>, metadata: Vec<MetadataValue>, approval_state: ApprovalState, approval_id, rendition_state: RenditionState, version, audit fields, archived_at }`, `Tag { id, slug, label }`, `MetadataValue { field_key, kind: MetadataKind, value: TypedValue }`, `Rendition { id, asset_id, file_version_id, kind: RenditionKind, storage_key, checksum, width, height, bytes, state, error_code }`, `Rights { asset_id, license, licensor, valid_from, valid_until, territories: Vec<TerritoryCode>, channels: Vec<Channel>, notes }`, `Collection { id, tenant_id, workspace_id, name, description, visibility, parent_id, depth, version }`. The collections are loaded and stored by the repositories as child rows; the DTOs keep them as JSON arrays.
- Use cases: `register_asset`, `update_asset`, `archive_asset`, `list_assets`, `get_asset`, `set_rights`, `rendition_url`, `request_asset_approval`, `apply_approval_decision` (consumer of `approval.decided.v1`), `create_collection`, `replace_collection_assets`, `list_collections`, `validate_metadata`, `derive_usable`.
- Worker: `services/worker/src/assets/rendition_job.rs` consumes `assets.render` with payload `{ tenant_id, asset_id, file_version_id, kinds, correlation_id }`, streams the source from object storage, renders with the image and video toolchains behind `RenditionBackend`, and persists through `AssetRenditionRepository::upsert_rendition` and `AssetRepository::update_asset_fields`; `services/worker/src/assets/approval_consumer.rs` applies F020 decisions through `AssetRepository`. Neither worker file contains SQL; both take repository traits from the worker context and wrap the rendition row plus the `rendition_state` transition plus the outbox row in one `UnitOfWork`.
- API DTOs (`services/api/src/assets/dto.rs`): `RegisterAssetRequest`, `UpdateAssetRequest`, `SetRightsRequest`, `AssetResponse { ..., rights, rights_state, usable, renditions: [{ kind, state }] }`, `CreateCollectionRequest`, `ReplaceCollectionAssetsRequest { asset_ids }`, `CollectionResponse`, `Page<AssetResponse>`.
- Events: `asset.created.v1` on register; `asset.updated.v1` on metadata, tag, approval-state, and file-version changes; `asset.rendition-ready.v1` per rendition kind with `{ kind, checksum, bytes }`; `asset.rights-updated.v1` on rights change; `asset.archived.v1` on archive.
- Authorization: `asset-editor` on the workspace for register, update, rights, archive, collection mutations; `asset-viewer` (resource ACL read) for list, get, and rendition URLs; `authz::require_entitlement(tenant, "dam")` first; explicit deny wins; file read is re-checked through F017 on every rendition request.
- Validation: title 1–200 chars, description ≤ 4,000, tags ≤ 50 of ≤ 40 chars, metadata keys must exist as `asset_metadata_fields` rows and `select` values must exist as `asset_metadata_field_options` rows, collection name 1–120 chars unique per parent, `valid_until >= valid_from`, every territory must be an `asset_territory_codes` row (ISO-3166 alpha-2) and every channel one of the four checked values, both rejected by the foreign key and the check constraint as well as by the service.
- Error mapping: `AssetError::FileNotClean → 400 invalid`, `AssetError::MetadataType → 400 invalid`, `AssetError::EntitlementMissing → 403 denied`, `AssetError::NotFound → 404 not_found`, `AssetError::StaleVersion → 409 conflict`, `AssetError::RenditionNotReady → 409 conflict`, `AssetError::CollectionTooDeep → 400 invalid`, `AssetError::TooManyItems → 400 invalid`.

### PostgreSQL/SQLx

- Migration `*_assets_*.sql` creates `assets(id uuid pk, tenant_id uuid not null references tenants(id) on delete restrict, workspace_id uuid not null references workspaces(id) on delete restrict, file_id uuid not null references files(id) on delete restrict, current_file_version_id uuid not null references file_versions(id) on delete restrict, title text not null, description text, mime_type text not null, mime_prefix text generated always as (split_part(mime_type,'/',1)) stored, byte_size bigint not null, width int, height int, duration_ms int, probe jsonb, approval_state text not null default 'draft' check (approval_state in ('draft','pending','approved','rejected')), approval_id uuid references approvals(id) on delete restrict, rendition_state text not null default 'pending' check (rendition_state in ('pending','ready','failed')), rendition_error text check (rendition_error is null or rendition_error in ('unsupported_format','too_large','timeout')), search tsvector not null default ''::tsvector, version bigint not null default 1, created_by, created_at, updated_by, updated_at, archived_at)`, `asset_renditions(id uuid pk, tenant_id, asset_id uuid not null references assets(id) on delete restrict, file_version_id uuid not null references file_versions(id) on delete restrict, kind text not null check (kind in ('thumbnail','preview','web','poster')), storage_key text, checksum text, width int, height int, bytes bigint, state text not null check (state in ('pending','ready','failed')), error_code text check (error_code is null or error_code in ('unsupported_format','too_large','timeout')), attempts smallint not null default 0, created_at, updated_at)`, `asset_rights(asset_id uuid pk references assets(id) on delete cascade, tenant_id, license text not null check (license in ('owned','licensed','royalty_free','restricted')), licensor text, valid_from date, valid_until date, notes text, version bigint, audit fields)`, `asset_collections(id uuid pk, tenant_id, workspace_id uuid not null references workspaces(id) on delete restrict, name text not null, description text, visibility text not null check (visibility in ('private','workspace','tenant')), parent_id uuid references asset_collections(id) on delete restrict, depth smallint not null default 0 check (depth <= 5), version, audit fields, deleted_at)`, `asset_collection_items(collection_id uuid not null references asset_collections(id) on delete cascade, asset_id uuid not null references assets(id) on delete restrict, position integer not null, added_by, added_at, primary key (collection_id, asset_id))`. `asset_collection_items.asset_id` is `restrict` because FR-F057-09 keeps membership rows for an archived asset so restore is exact; `asset_renditions.asset_id` is `restrict` so the F027 purge must delete the object-storage keys before the rows.
- Normalized sets (decision section 2, no array columns): `asset_tag_definitions(id uuid pk, tenant_id uuid not null, slug text not null, label text not null, created_by, created_at, unique (tenant_id, slug))` plus `asset_tags(asset_id uuid not null references assets(id) on delete cascade, tag_id uuid not null references asset_tag_definitions(id) on delete restrict, tenant_id, added_by, added_at, primary key (asset_id, tag_id))` replace `assets.tags text[]`, so a tag is renamed once, joined, counted for facets, and audited; `asset_rights_territories(asset_id uuid not null references asset_rights(asset_id) on delete cascade, code char(2) not null references asset_territory_codes(code) on delete restrict, tenant_id, primary key (asset_id, code))` and `asset_territory_codes(code char(2) pk, name text not null)` seeded with ISO-3166 alpha-2 by the migration replace `asset_rights.territories text[]`; `asset_rights_channels(asset_id uuid not null references asset_rights(asset_id) on delete cascade, channel text not null check (channel in ('web','print','social','internal')), tenant_id, primary key (asset_id, channel))` replaces `asset_rights.channels text[]`, giving the "which assets may run on social" query an index instead of an array scan; `asset_metadata_fields(id uuid pk, tenant_id uuid not null, key text not null, label text not null, kind text not null check (kind in ('text','number','date','select','person')), required bool not null default false, position smallint not null, created_at, updated_at, unique (tenant_id, key))`, `asset_metadata_field_options(field_id uuid not null references asset_metadata_fields(id) on delete cascade, option_key text not null, label text not null, position smallint not null, primary key (field_id, option_key))`, and `asset_metadata_values(asset_id uuid not null references assets(id) on delete cascade, field_id uuid not null references asset_metadata_fields(id) on delete restrict, tenant_id, text_value text, number_value numeric, date_value date, option_key text, person_id uuid references users(id) on delete restrict, primary key (asset_id, field_id), foreign key (field_id, option_key) references asset_metadata_field_options(field_id, option_key) on delete restrict, check (num_nonnulls(text_value, number_value, date_value, option_key, person_id) = 1))` replace `assets.metadata jsonb` and the tenant-settings field list. The API keeps `tags`, `territories`, and `channels` as JSON string arrays and `metadata` as a JSON object keyed by field key, so no externally visible request or response shape changes; `AssetRepository` and `AssetRightsRepository` fan each set out to rows and reassemble it on read, replacing a set with one `delete` of removed rows and one `insert ... on conflict do nothing` inside the caller's `UnitOfWork`.
- `jsonb` audit: `assets.probe` stays `jsonb` — it is the verbatim EXIF/ffprobe snapshot from the extraction toolchain, a provider response snapshot kept for support and never filtered, joined, or constrained. Everything the library queries is lifted out of it into typed columns: `mime_type` and the generated `mime_prefix` back the FR-F057-07 `mime_prefix` filter, `byte_size`, `width`, `height`, and `duration_ms` back the detail drawer and the 50 MB rendition budget in NFR-F057-01. `assets.metadata jsonb` is removed: the product validates it per key (FR-F057-12), blocks field removal while values exist, and searches its text, so it is a table, not a document. `asset_rights` holds no `jsonb`: `rights_state` derives from the typed `valid_until` column, and `license` is a checked closed enum. No other `jsonb` column exists in the module; JetStream payloads for `assets.render` and the five `asset.*.v1` events remain JSON documents on the wire, which decision section 2 permits as event payloads.
- Denormalization: `assets.search` is a maintained `tsvector`, not a generated column, because it spans `asset_tags` → `asset_tag_definitions.label` and `asset_metadata_values.text_value`. It is a derived, rebuildable cache serving only the FR-F057-07 `q` filter; `AssetRepository::refresh_search_vector` rewrites it inside the same transaction as any title, description, tag, or metadata write, and `cargo xtask reindex-assets` rebuilds a tenant from the base tables.
- Invariants: unique `asset_renditions_asset_version_kind_idx on (asset_id, file_version_id, kind)` makes the rendition job idempotent per NFR-F057-04; unique `asset_collections_parent_name_idx on (tenant_id, coalesce(parent_id, '00000000-0000-0000-0000-000000000000'), lower(name)) where deleted_at is null`; `asset_tags` primary key blocks a duplicate tag on an asset and `asset_tag_definitions(tenant_id, slug)` blocks two spellings of one tag; `asset_rights_territories` and `asset_rights_channels` primary keys block duplicate entries and their foreign key and check constraints reject an unknown ISO code or channel; `asset_metadata_values` primary key allows one value per field per asset, its composite foreign key forces a `select` value to be a declared option, and its `num_nonnulls` check forces exactly one typed column to be populated; `asset_metadata_fields(tenant_id, key)` is unique and a tenant is limited to 30 rows by `AssetMetadataFieldRepository`; the `field_id` `restrict` reference from `asset_metadata_values` is what rejects removing a field that still has values (FR-F057-12); checks on `approval_state`, `rendition_state`, `rendition_error`, `asset_renditions.kind`, `asset_renditions.state`, `asset_renditions.error_code`, `license`, and `visibility` bound every closed enum in the module.
- Indexes: `assets using gin(search)`, `assets(tenant_id, workspace_id, updated_at desc) where archived_at is null`, `assets(tenant_id, approval_state)`, `assets(tenant_id, mime_prefix) where archived_at is null`, `asset_tags(tag_id, asset_id)` for the tag facet and the reverse "which assets carry this tag" query, `asset_tag_definitions(tenant_id, slug)`, `asset_collection_items(asset_id)`, `asset_rights(tenant_id, valid_until)` for the rights-expiry sweep, `asset_rights_territories(code, asset_id)` and `asset_rights_channels(channel, asset_id)` for the territory and channel filters, `asset_metadata_values(field_id, text_value)` and `asset_metadata_values(field_id, date_value)` for per-field filtering and sorting, `asset_metadata_field_options(field_id, position)`.
- Audit events: `asset.register`, `asset.update`, `asset.archive`, `asset.rights.set`, `asset.approval.request`, `asset.approval.apply`, `collection.create`, `collection.replace-items` with field-level diffs.
- Retention/deletion: archived assets and renditions purged by the F027 job after the tenant retention window, which deletes object keys first, then `asset_renditions` and `asset_collection_items`, then the asset, whose `on delete cascade` children (`asset_tags`, `asset_metadata_values`, `asset_rights` and its territory and channel rows) go with it; every purge statement lives in the `crates/persistence/src/assets/` repositories. Rollback drops the thirteen tables children before parents: `asset_metadata_values`, `asset_metadata_field_options`, `asset_metadata_fields`, `asset_rights_channels`, `asset_rights_territories`, `asset_territory_codes`, `asset_tags`, `asset_tag_definitions`, `asset_collection_items`, `asset_collections`, `asset_rights`, `asset_renditions`, `assets`.

### React/TypeScript

- Routes: `/w/:workspaceId/assets`, `/w/:workspaceId/assets/:assetId`, `/w/:workspaceId/assets/collections/:collectionId` in `apps/web/src/features/assets/`; components `AssetLibraryPage`, `AssetGrid`, `AssetTile`, `AssetDetailDrawer`, `RenditionPanel`, `RightsForm`, `ApprovalPanel`, `MetadataForm`, `CollectionTree`, `CollectionAssetsEditor`, `RegisterAssetDialog`, `EntitlementUpsell`.
- State: TanStack Query keys `['assets', workspaceId, filters]`, `['asset', id]`, `['asset-collections', workspaceId]`, `['collection-assets', collectionId]`; rendition state subscribes to `asset.rendition-ready.v1` through the F046 sheet-independent notification channel and otherwise polls every 5 s while `pending`.
- API client: generated `AssetsApi` with `listAssets`, `registerAsset`, `getAsset`, `updateAsset`, `archiveAsset`, `setRights`, `renditionUrl`, `listCollections`, `createCollection`, `replaceCollectionAssets`.
- Optimistic updates: tag and title edits apply locally and roll back on `conflict`; collection reorder applies locally and re-sends the full list.
- Feature flag: `useFlag('F057_FEATURE')` and `useEntitlement('dam')` gate navigation and routes.
- Telemetry: `asset_registered`, `asset_rights_set`, `asset_approval_requested`, `asset_archived`, `collection_created`, `asset_rendition_retry` with `asset_id`, `mime_prefix`, `kind`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F057-01 through FR-F057-14 in `testing/features/F057/requirements/cases.md`
- [ ] Failure/edge-case tests: unscanned file, metadata type mismatch, expired rights, collection depth 6, 5,001 items, rendition failure after 3 attempts, archived asset excluded from collections
- [ ] Permission-negative and tenant-isolation tests: no entitlement denied, viewer rights change denied, foreign tenant not_found, rendition URL for unreadable file not_found
- [ ] Rust unit tests: `crates/domain/src/assets/` usable derivation, metadata validation, rights expiry, collection depth, all against repository fakes so the domain compiles without SQLx
- [ ] API contract/integration tests: every route above with success and each error code, asserting `tags`, `territories`, `channels`, and `metadata` keep their JSON array and object shapes while the rows land in the child tables
- [ ] Database migration/constraint tests: rendition uniqueness, collection name uniqueness, depth check, GIN search index, rollback, duplicate `asset_tags` row rejected, unknown territory code rejected by the `asset_territory_codes` foreign key, invalid channel rejected by the check constraint, `asset_metadata_values` rejected when two typed columns are set, `select` value rejected when the option is not declared, metadata field removal rejected while values exist, and `assets.probe` the only remaining `jsonb` column in the module
- [ ] React component tests: `AssetGrid`, `AssetDetailDrawer`, `RightsForm`, `CollectionTree` states
- [ ] Browser E2E tests: register, renditions ready, rights, approval, collection, archive
- [ ] Accessibility tests: axe on library and drawer, keyboard tile navigation, badge text
- [ ] Performance/load tests: 200,000-asset list p95 under 500 ms, thumbnail ready within 60 s p95

### Fast fanout configuration

- Test harness path: `testing/features/F057/`
- Feature flag: `F057_FEATURE`
- Fixture/seed factory: `testing/fixtures/assets.rs` builds entitled and unentitled tenants, editor, viewer, approver, foreign tenant, 20 clean files (PNG, JPEG, MP4, PDF), one quarantined file, a tenant metadata schema with 5 fields, and a 3-level collection tree
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, rights windows around the fixed clock
- Mock/stub contracts: MinIO from compose for object storage; `RenditionBackend` fake that emits deterministic PNG/MP4 bytes; in-memory JetStream recorder; real F020 approval engine with a fixture policy
- Parallel isolation: one schema per test worker, tenant ID per test, unique bucket prefix per worker
- Targeted command: `cargo xtask test-feature F057`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F057/`

## 6. Acceptance criteria

```gherkin
Feature: Governed asset library

Scenario: Register an asset and receive renditions
  Given an asset editor in a tenant with the dam entitlement and a clean 8 MB PNG
  When they register the file as asset "Logo 2026" with tags "brand,logo"
  Then the asset has version 1, approval_state draft, and rendition_state pending
  And within 60 seconds asset.rendition-ready.v1 is published for thumbnail, preview, and web

Scenario: Expired rights make an approved asset unusable
  Given an approved asset with rights valid_until 2026-09-01
  When any actor reads it on 2026-09-03
  Then rights_state is expired and usable is false

Scenario: Viewer cannot change rights
  Given a viewer on the workspace
  When they call PUT /api/v1/assets/{id}/rights
  Then the response is 403 denied and no audit diff is written

Scenario: Rights territories are stored as joinable rows
  Given an approved asset with rights territories "US,DE" and channel "web"
  When an editor replaces the territories with "US,FR" through PUT /api/v1/assets/{id}/rights
  Then the response still returns territories as a JSON array
  And asset_rights_territories holds exactly the rows US and FR for that asset
  And a request containing territory "XX" is rejected as invalid

Scenario: Unentitled tenant is denied
  Given a tenant without the dam entitlement
  When an asset editor lists assets
  Then the response is 403 denied with field_errors.entitlement "dam"
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F017 (files, versions, scan state, signed URLs), F020 (approval instances and decisions), F048 (entitlements and flags); decisions sections 2, 3, 4, 5, 7; contracts row F057
- Blocks: none
- Conflicts with: none (disjoint owned paths)
- External dependencies: image and video toolchains inside the worker container (`infra` provides the image); MinIO in compose
- Risks and mitigations: video transcoding is slow and memory-heavy, so video renditions run on a dedicated JetStream consumer with concurrency 2 and a 10-minute timeout; rights expiry evaluated in the tenant timezone could flip at midnight, so `rights_state` is derived from `valid_until` at end of day in the tenant timezone with fixture cases on both sides; metadata schema changes can orphan values, so `asset_metadata_values.field_id` references `asset_metadata_fields` with `on delete restrict` and the database rejects removing a field while any asset carries a value.
- Rollout: enable `F057_FEATURE` for the pilot tenant, grant the `dam` entitlement, watch `asset_rendition_failures_total` for 48 hours.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F017, F020, and F048 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F057/`
- [ ] Migration file name and owned paths claimed
- [ ] Rendition backend fake, MinIO harness, and schema-per-worker isolation available in `testing/harness/`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, worker, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation and rendition outcome
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F057_FEATURE`, revoke entitlement, run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Teams with the DAM entitlement can register scanned files as assets with typed metadata, renditions, usage rights, approvals, and collections, and search for usable brand material.
- Support: rendition failures show `error_code` and `correlation_id`; operators inspect `assets.render` dead letters in the worker console.
- Migration adds `assets`, `asset_renditions`, `asset_rights`, `asset_collections`, and `asset_collection_items` plus the normalized child tables `asset_tag_definitions`, `asset_tags`, `asset_territory_codes`, `asset_rights_territories`, `asset_rights_channels`, `asset_metadata_fields`, `asset_metadata_field_options`, and `asset_metadata_values`; rollback drops them children first. Feature is off by default behind `F057_FEATURE` and the `dam` entitlement.
