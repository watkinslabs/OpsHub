---
id: F047
type: feature
status: planned
priority: P1
owner: platform
estimate: 3
target_milestone: M5
parent_epic: E006
depends_on: [F028, F045]
blocks: []
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/mcp/**, crates/persistence/src/mcp/**, crates/contracts/src/mcp/**, services/mcp/src/mcp/**, services/api/src/mcp/**, apps/web/src/features/mcp/**, services/api/migrations/*_mcp_*.sql, testing/harness/mcp/**, testing/features/F047/**]
feature_flag: F047_FEATURE
flag_default: off
branch: f047-mcp-access-server
started_at: null
finished_at: null
---

# F047 — MCP access server

## 1. Identity and dates

- Branch: `f047-mcp-access-server`
- Capability area: integrations and APIs (spec 5.9a MCP-01, MCP-02, MCP-03 and its low-level bullets on generated schemas, actor context, redaction, idempotent reads, and reviewable mutation summaries)
- Decision references: `docs/architecture-decisions.md` sections 1, 2, 2.1, 3, 8, 9; `docs/capability-contracts.md` row F047
- Aggregate: `mcp-server`
- Module slug: `mcp`

## 2. Requirement specification

### Problem and user outcome

Assistants and agent runtimes speak the Model Context Protocol, not the OpsHub REST API. Handing them an API token today would give a model the full authority of the human who minted it, with no per-call record and no chance to stop a write before it lands. OpsHub needs one MCP endpoint that reuses the same `ActorContext`, the same F003 permission evaluation, and the same F028 error vocabulary as the REST surface, exposes reads as MCP resources, exposes writes as MCP tools that stop at a human approval gate, and records every single call.

As a tenant member running an MCP client, I want to attach OpsHub to my assistant with a scoped token, let it read only the workspaces, documents, projects, tasks, tickets, dashboards, and workflows I can already read, and have any write pause for my explicit approval with a diff I can see, so that the assistant is useful without becoming an unaudited second identity.

### Functional requirements

- **FR-F047-01:** `POST /mcp/v1` implements JSON-RPC 2.0 over HTTP for the methods `initialize`, `resources/list`, `resources/read`, `tools/list`, and `tools/call`; a single request object or a batch array of at most 10 is accepted; `initialize` returns `{ protocolVersion: "2025-06-18", serverInfo: { name: "opshub", version: <build> }, capabilities: { resources: { subscribe: true, listChanged: true }, tools: { listChanged: true }, logging: {} } }`; an unsupported `protocolVersion` returns JSON-RPC error `-32602` with `data.supported: ["2025-06-18"]`, and an unknown method returns `-32601`.
- **FR-F047-02:** Every `/mcp/v1` request authenticates with `Authorization: Bearer oh_...` resolved by the F038 bearer path into `ActorContext { tenant_id, actor_id, roles, scopes, correlation_id, auth_kind: ApiToken }`; the token must carry the scope `mcp:access` plus at least one of `records:read`, `records:write`, `documents:read`, `documents:write`, `workflows:run`; a missing, revoked, expired, or `mcp:access`-less token returns JSON-RPC error `-32001` with `data: { code: "denied", reason: "invalid_token", correlation_id }` and HTTP `200`, and the transport never falls back to session cookies.
- **FR-F047-03:** `resources/list` returns permission-filtered resource descriptors with `uri` of the form `opshub://<kind>/<id>` for `kind` in `workspace`, `document`, `folder`, `project`, `task`, `ticket`, `dashboard`, `workflow`, `audit`, plus `name`, `mimeType` (`application/json` except `document` which is `text/markdown`, read from the `mcp_resource_kinds` lookup row for the kind), `description`, and `annotations.lastModified`; it accepts `{ cursor?, kind? }` and returns `{ resources, nextCursor? }` capped at 100 per page using the F028 signed cursor; every candidate is filtered through `authz::check(actor, <kind>:read, resource)` before it enters the page, so counts differ per actor.
- **FR-F047-04:** `resources/read` with `{ uri }` returns `{ contents: [{ uri, mimeType, text }] }` built by a per-kind adapter over the canonical domain read model: `document` returns the current revision body from F045 with `revision` and `updated_at`; `project`, `task`, and `ticket` return the typed record with resolved column values; `dashboard` returns widget definitions with the last computed values; `workflow` returns definition and last 10 runs; `audit` returns the F003 audit page for the referenced resource. A malformed URI returns `-32602` `invalid`; a URI the actor cannot read and a URI that does not exist both return `-32002` `not_found` so existence never leaks.
- **FR-F047-05:** Field-level redaction runs on every resource payload before serialization: attributes the actor lacks `field:read` on are removed and listed in `annotations.redactedFields`; token material, password hashes, webhook secrets, and OAuth ciphertext are removed unconditionally by the shared F027 redaction list; a payload larger than 256 KB is truncated at a record boundary with `annotations.truncated: true` and `annotations.nextCursor`.
- **FR-F047-06:** `tools/list` returns the tool manifest generated at build time from `crates/contracts/src/mcp/manifest.rs`, each with `name`, `description`, `inputSchema` (JSON Schema draft 2020-12), and `annotations.readOnlyHint`; the read tools are `search_records`, `get_record`, `list_children`, `get_report`, `get_workflow_runs`; the mutating tools are `create_record`, `update_record`, `add_comment`, `assign_record`, `run_workflow`; tools whose required scope is absent from the token are omitted from the list; a manifest that drifts from the OpenAPI DTOs fails `cargo xtask check-contracts`.
- **FR-F047-07:** `tools/call` for a read tool executes the same domain use case as the REST route, is side-effect free, and returns `{ content: [{ type: "text", text: <json> }], isError: false }`; `search_records` accepts `{ query, kinds?, workspace_id?, limit? (1–50, default 20) }` and returns matches ordered by rank with `uri`, `title`, `snippet`, and `score`; results are permission-filtered, never cached across actors, and identical arguments within one second return identical results.
- **FR-F047-08:** `tools/call` for a mutating tool never writes on the first call. It validates arguments, evaluates authorization, computes the change summary, inserts an `mcp_confirmations` row through `ConfirmationRepository::insert_pending_confirmation` with `status: pending`, `tool`, `operation`, the target split into `resource_kind` and `resource_id` (both null for a create whose target does not exist yet), `arguments_hash` (SHA-256 of the canonical JSON arguments), `summary`, `expires_at = now + 15 minutes`, publishes `mcp.mutation-proposed.v1`, and returns `{ content: [...summary...], isError: true, structuredContent: { code: "confirmation_required", confirmation_id, expires_at, summary } }`. The returned summary object is unchanged: it lists `resource_uri` (recomposed as `opshub://<resource_kind>/<resource_id>`), `operation` (read from its own column), and a `changes` array of `{ field, before, after }` for updates or the full proposed record for creates.
- **FR-F047-09:** `POST /api/v1/mcp/confirmations/{id}/approve` (session-authenticated human, requires `Idempotency-Key`) sets `status: approved`, `approved_by`, `approved_at`, publishes `mcp.mutation-confirmed.v1`, and returns the confirmation; only the actor that owns the token that proposed it, or a `tenant-admin`, may approve; approving an expired, already-approved, or already-consumed row returns `409 conflict`; a foreign-tenant id returns `404 not_found`.
- **FR-F047-10:** A repeat `tools/call` carrying `{ confirmation_id }` executes only when the row is `approved`, unexpired, and its `arguments_hash` equals the hash of the current arguments; it then runs the domain use case with the caller's `Idempotency-Key` derived as `mcp:<confirmation_id>`, marks the row `consumed` through `ConfirmationRepository::consume_confirmation` in the same `UnitOfWork` transaction as the write and the `mcp_audit` append, and returns the resulting record. A mismatched hash returns `-32602` with `data.code: "invalid"` and `reason: "arguments_changed"`; a `pending`, `expired`, or `consumed` row returns `-32003` `conflict`.
- **FR-F047-11:** Every `/mcp/v1` method call writes exactly one `mcp_audit` row through `McpAuditRepository::append_audit_entry` inside the request transaction with `tenant_id`, `actor_id`, `token_prefix`, `method`, `tool`, the target as the `resource_kind`/`resource_id` column pair (the `opshub://` URI is recomposed for every read model and API response), `arguments_digest`, `decision` (`allowed`, `denied`, `confirmation_required`), `outcome` (`ok`, `error`), `error_code`, `duration_ms`, `redacted_field_count`, `correlation_id`, and `occurred_at`; reads also publish `mcp.resource-read.v1` and tool calls publish `mcp.tool-called.v1`; `mcp_audit` is append-only under the F003 immutability trigger, and arguments are stored only as a digest plus the reviewable summary, never verbatim.
- **FR-F047-12:** Rate limits are enforced in `mcp_rate_limits` as token buckets keyed by `(tenant_id, token_id, bucket)` whose `bucket` is a foreign key into the `mcp_rate_limit_buckets` policy rows — `calls` at 600 per minute with burst 1,200, `mutations` at 60 per minute with burst 60, and `search` at 120 per minute — so the capacity and window live once per bucket instead of being repeated on every token row, and `RateLimitRepository::consume_rate_tokens` joins the policy when it refills; exceeding a bucket returns JSON-RPC error `-32004` with `data: { code: "rate_limited", retry_after_seconds }` and increments `mcp_rate_limited_total{bucket}`; the buckets are separate from the F028 per-application limits so an MCP client cannot exhaust a partner integration's budget.
- **FR-F047-13:** `GET /mcp/v1/sse` opens a `text/event-stream` bound to the same token and returns `notifications/resources/updated` for `document.updated.v1`, `document.revision-added.v1`, and record events on resources the actor may read, `notifications/resources/list_changed` when a workspace grant changes, and a `:heartbeat` comment every 15 seconds; the stream closes with `denied` when the token is revoked or the tenant is suspended, caps at 3 concurrent streams per token, and drops events the actor may no longer read without closing the stream.
- **FR-F047-14:** `GET /api/v1/mcp/audit` lists `mcp_audit` newest first with cursor paging (`limit` ≤ 200) and filters `actor_id`, `method`, `tool`, `decision`, `outcome`, `resource_uri`, `correlation_id`, `occurred_from`, `occurred_to`; the `resource_uri` query parameter keeps its `opshub://<kind>/<id>` form and is parsed into the `resource_kind`/`resource_id` column pair before the query, so the filter is an indexed predicate rather than a string match, and an unknown kind returns `400 invalid`; a `tenant-admin` reads the whole tenant through `McpAuditRepository::list_audit_for_tenant`, any other actor reads only its own rows through `list_audit_for_actor`, and a cross-tenant `resource_uri` filter returns an empty page.
- **FR-F047-15:** `/admin/mcp` in the web app shows a `Pending approvals` list with the tool, target resource link, and the field-level diff, an `Approve` action with a confirm dialog naming the resource, a countdown to `expires_at`, and an `MCP activity` table over `GET /api/v1/mcp/audit` with the same filters and a copy-correlation-id action; members see only their own rows, and non-admins are denied the tenant-wide filter.

### Non-functional requirements

- **NFR-F047-01 Performance:** `initialize` and `tools/list` respond in under 100 ms p95 from the in-memory manifest; `resources/list` of 100 descriptors under 300 ms p95 including permission filtering; `resources/read` of a 100 KB document under 400 ms p95; `tools/call` adds under 30 ms p95 over the underlying REST use case; the server sustains 200 concurrent SSE streams with under 200 MB resident memory.
- **NFR-F047-02 Security/privacy:** the MCP transport is a distinct service (`services/mcp`) that holds no database credentials and no pool of its own and reaches PostgreSQL only through the `crates/persistence/src/mcp/` repositories, never accepts session cookies, never returns a resource without a positive `authz::check`, treats resource and tool arguments as untrusted data (no interpolation into SQL, filters, or workflow expressions), rejects `opshub://` URIs bearing another tenant's id as `not_found`, and never logs arguments, resource bodies, or token plaintext.
- **NFR-F047-03 Accessibility:** `/admin/mcp` passes axe with zero serious or critical violations; the diff viewer exposes before and after as a labelled description list rather than colour alone; the approval countdown is announced through a polite live region at 5 minutes and 1 minute; the confirm dialog traps focus and returns it to the row's `Approve` button.
- **NFR-F047-04 Reliability/observability:** the SSE consumer is resumable by `Last-Event-Id` within a 60-second replay window and drops to `list_changed` when the window is exceeded; confirmation expiry is swept every minute and is also enforced at read time so a stalled sweeper cannot let a stale approval through; metrics `mcp_calls_total{method,tool,decision}`, `mcp_call_duration_seconds{method}`, `mcp_confirmations_total{status}`, `mcp_stream_active`, and `mcp_rate_limited_total{bucket}` exist, and every call carries a tracing span with `correlation_id`, `tool`, and `confirmation_id`.

### Scope

Included: the JSON-RPC transport and `services/mcp` service, token authentication and scope checks reusing F038 and F003, resource URI scheme and per-kind read adapters, redaction and truncation, the generated tool manifest and drift gate, read tools, the two-phase mutation confirmation gate and approval route, per-token rate limit buckets, the `mcp_audit` append-only log and its four events, the SSE notification stream, the audit read route, and the `/admin/mcp` approvals and activity page.

Excluded: REST list, filter, error, and rate-limit conventions and the OpenAPI document itself (F028); API token minting, scopes, and bearer authentication (F038); role, ACL, and audit primitives (F003); document storage and revisions (F045); outbound webhooks (F028); OAuth provider connections (F029); assistant prompting, model hosting, or any client-side agent (out of product scope); MCP stdio transport and local process launching (not offered by a hosted deployment).

## 3. UX specification

- Entry points: admin navigation `MCP`; routes `/admin/mcp` (approvals plus activity) and `/admin/mcp/audit/:eventId` (single call detail drawer); a `Connect an MCP client` panel that shows the endpoint URL, the required `mcp:access` scope, and a link to the F038 token page.
- Primary flow: a member mints a token with `mcp:access` and `records:read`, points the client at `https://<tenant>/mcp/v1`, and the client lists 42 resources; the assistant calls `update_record` on task `Ship beta`, which returns `confirmation_required`; the member opens `/admin/mcp`, sees `update_record · Ship beta` with `due_date 2026-09-10 → 2026-09-24` and a 14-minute countdown, clicks `Approve`, confirms, and the assistant's retry succeeds; the activity table then shows two rows for that tool, `confirmation_required` and `allowed`.
- Loading: skeleton rows in both tables; Empty: `No pending approvals` with the connect panel, and `No MCP calls yet` in activity; Error: banner with `correlation_id` and retry; Success: toast `Approved — the client may now apply this change`; Stale/conflict: an expired row greys out in place with `Expired` and the `Approve` button disabled; Denied: non-admins see their own rows only and the tenant-wide actor filter is hidden.
- Diff viewer: a description list of `field`, `before`, `after`; creates render the proposed record as the same list with `before` empty; long values collapse at 5 lines with `Show more`.
- Responsive: tables collapse to cards under 768 px; the detail drawer becomes a full-screen sheet under 640 px.
- Keyboard: table rows are focusable and `Enter` opens the drawer; `Escape` closes the drawer and dialog; the countdown never steals focus; reduced motion disables the drawer slide and the countdown pulse.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide icons `PlugZap`, `ShieldCheck`, `FileDiff`, `CheckCheck`, `Clock`, `ScrollText`; tokens from `apps/web/src/design/tokens.css`.

- Design: `design/artboards/Mcp.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

### Rust backend

- Data access (decision section 2.1): `crates/persistence/src/mcp/` holds `ConfirmationRepository` (owns `mcp_confirmations`), `McpAuditRepository` (owns `mcp_audit` and its monthly partitions), `RateLimitRepository` (owns `mcp_rate_limits` and the `mcp_rate_limit_buckets` policy rows, which are the bucket child of a token and so belong to the same repository), and `ResourceKindRepository` (owns `mcp_resource_kinds`). No other class writes those tables. Named queries beyond the shared `Repository` contract: `insert_pending_confirmation`, `find_open_proposal`, `get_confirmation_for_actor`, `list_pending_for_tenant`, `approve_confirmation`, `consume_confirmation`, `expire_due_confirmations`, `purge_settled_confirmations`, `append_audit_entry`, `get_audit_entry`, `list_audit_for_tenant`, `list_audit_for_actor`, `ensure_audit_partitions`, `detach_audit_partition_before`, `consume_rate_tokens`, `bucket_policy`, `list_resource_kinds`, `mime_type_for_kind` — there is no generic query escape hatch. The nine resource adapters own no SQL and no read model of their own: `document` and `folder` read F045 `DocumentRepository` and `FolderRepository`, `project`/`task`/`ticket` read the F006 `RecordRepository`, `dashboard` reads the F023 `DashboardRepository`, `workflow` reads the F018 `WorkflowRepository`, and `audit` reads the F003 `AuditRepository`.
- Every use case below depends on these repository traits and contains no SQL; `crates/domain/src/mcp/` carries no `sqlx` dependency. `services/mcp` reaches PostgreSQL only through repositories — it opens no pool, holds no connection string, and contains no `sqlx::query*` call; `state.rs` holds the manifest, the repository set, and the clock. Consuming a confirmation, executing the underlying domain write, appending the `mcp_audit` row, and enqueuing the outbox event run inside one `UnitOfWork`, so a partial mutation cannot leave an unconsumed approval or an unlogged call; the expiry sweeper, the SSE bridge, and the rate-limit check call repositories only.
- Domain entities in `crates/domain/src/mcp/`: `ResourceUri { kind: ResourceKind, id: Uuid }` with `parse`/`to_string`; `ResourceDescriptor { uri, name, mime_type, description, last_modified }`; `ResourceContents { uri, mime_type, text, redacted_fields: Vec<String>, truncated: bool }`; `ToolDefinition { name, description, input_schema, read_only, required_scope }`; `ChangeSummary { resource_uri, operation: Create|Update|Comment|Assign|Run, changes: Vec<FieldChange { field, before, after }> }`; `Confirmation { id, tenant_id, actor_id, token_id, tool, arguments_hash, summary, status: Pending|Approved|Consumed|Expired|Rejected, approved_by, approved_at, expires_at, consumed_at, version }`; `McpAuditEntry { .. per FR-F047-11 }`; `RateBucket { tenant_id, token_id, bucket, tokens, refilled_at }` with its `capacity`, `burst`, and `window_seconds` carried by `BucketPolicy { bucket, capacity, burst, window_seconds }` loaded from `mcp_rate_limit_buckets`.
- Use cases: `initialize`, `list_resources`, `read_resource`, `list_tools`, `call_tool`, `propose_mutation`, `approve_confirmation`, `consume_confirmation`, `list_audit`, `subscribe_stream`, `check_rate_limit`. Traits `ResourceAdapter { kind(), list(ctx, cursor), read(ctx, id) }` and `ToolHandler { definition(), invoke(ctx, args), summarize(ctx, args) }`; adapters `WorkspaceAdapter`, `DocumentAdapter`, `FolderAdapter`, `ProjectAdapter`, `TaskAdapter`, `TicketAdapter`, `DashboardAdapter`, `WorkflowAdapter`, `AuditAdapter` in `crates/domain/src/mcp/adapters/`.
- Transport in `services/mcp/src/mcp/`: `main.rs` builds the Axum router with `POST /mcp/v1` and `GET /mcp/v1/sse`; `jsonrpc.rs` handles envelope parsing, batching, and the code map `invalid → -32602`, `denied → -32001`, `not_found → -32002`, `conflict → -32003`, `rate_limited → -32004`, `unavailable → -32005`, malformed JSON `→ -32700`, unknown method `→ -32601`; `dispatch.rs` routes methods to use cases; `sse.rs` bridges the F004 event stream with per-event authorization; `state.rs` holds the manifest, the `crates/persistence/src/mcp/` repository handles, and the clock — never a pool or a SQL string.
- API endpoints in `services/api/src/mcp/`: `GET /api/v1/mcp/audit` and `POST /api/v1/mcp/confirmations/{id}/approve` mounted on the session-authenticated router, using the F028 list conventions and error schema; DTOs `McpAuditResponse`, `Page<McpAuditResponse>`, `ConfirmationResponse { id, tool, resource_uri, summary, status, expires_at, approved_by, approved_at }`, `ApproveConfirmationRequest { }` (empty body, `Idempotency-Key` header required).
- Manifest generation in `crates/contracts/src/mcp/`: `manifest.rs` derives `ToolDefinition` input schemas from the same typed request DTOs the OpenAPI generator uses; `hash.rs` emits `openapi/mcp-manifest.sha256`; `cargo xtask check-contracts` compares the built manifest with the checked-in hash and fails on drift.
- Events: `mcp.resource-read.v1`, `mcp.tool-called.v1`, `mcp.mutation-proposed.v1`, `mcp.mutation-confirmed.v1`, published through the outbox with the standard `{ tenant_id, actor_id, aggregate_id, version, changed_fields, correlation_id, occurred_at }` envelope where `aggregate_id` is the confirmation id for mutation events and the resource id for read events.
- Authorization: `scoped-actor` — the token's scopes bound the tool set, and `authz::require(&ctx, Permission, ResourceRef)` from F003 decides every resource and tool call; the approval route requires the proposing actor or `tenant-admin`; cross-tenant ids map to `not_found`.
- Validation: `uri` matches `^opshub://(workspace|document|folder|project|task|ticket|dashboard|workflow|audit)/[0-9a-f-]{36}$`; `limit` 1–100 for resources and 1–50 for `search_records`; `query` 1–256 chars; tool arguments validated against the manifest schema before authorization so schema errors never reveal existence; batch size ≤ 10; SSE `Last-Event-Id` must be a UUIDv7 within 60 seconds.
- Error mapping: `McpError::UnsupportedProtocol → -32602 invalid`, `::UnknownMethod → -32601`, `::Unauthenticated → -32001 denied`, `::ScopeMissing → -32001 denied`, `::UriInvalid → -32602 invalid`, `::NotVisible → -32002 not_found`, `::ConfirmationRequired → tools/call isError with structuredContent`, `::ConfirmationState → -32003 conflict`, `::ArgumentsChanged → -32602 invalid`, `::RateLimited → -32004 rate_limited`, `::AdapterUnavailable → -32005 unavailable`.

### PostgreSQL/SQLx

- Migration `*_mcp_*.sql` creates `mcp_confirmations(id uuid pk, tenant_id uuid not null references tenants(id) on delete restrict, actor_id uuid not null references users(id) on delete restrict, token_id uuid not null references api_tokens(id) on delete cascade, tool text not null, operation text not null check (operation in ('create','update','comment','assign','run')), resource_kind text references mcp_resource_kinds(kind) on delete restrict, resource_id uuid, arguments_hash bytea not null, summary jsonb not null, status text not null default 'pending' check (status in ('pending','approved','consumed','expired','rejected')), approved_by uuid references users(id) on delete restrict, approved_at timestamptz, expires_at timestamptz not null, consumed_at timestamptz, version bigint not null default 1, created_at timestamptz not null, correlation_id uuid not null)`, `mcp_audit(id uuid, tenant_id uuid not null references tenants(id) on delete restrict, actor_id uuid not null references users(id) on delete restrict, token_prefix text not null, method text not null check (method in ('initialize','resources/list','resources/read','tools/list','tools/call')), tool text, resource_kind text references mcp_resource_kinds(kind) on delete restrict, resource_id uuid, arguments_digest bytea, decision text not null check (decision in ('allowed','denied','confirmation_required')), outcome text not null check (outcome in ('ok','error')), error_code text, duration_ms int not null, redacted_field_count int not null default 0, confirmation_id uuid, correlation_id uuid not null, occurred_at timestamptz not null, primary key (id, occurred_at))`, and `mcp_rate_limits(tenant_id uuid not null references tenants(id) on delete restrict, token_id uuid not null references api_tokens(id) on delete cascade, bucket text not null references mcp_rate_limit_buckets(bucket) on delete restrict, tokens numeric not null, refilled_at timestamptz not null, primary key (tenant_id, token_id, bucket))`. `mcp_audit.confirmation_id` deliberately carries no foreign key: audit partitions are retained 400 days while `mcp_confirmations` rows are purged after 30, and the `audit_immutable` trigger forbids the `UPDATE` a `set null` action would need.
- Normalized sets and lookups (decision section 2, no array columns and no repeated configuration): `mcp_resource_kinds(kind text primary key check (kind in ('workspace','document','folder','project','task','ticket','dashboard','workflow','audit')), mime_type text not null, read_permission text not null)` is seeded by the migration with one row per `ResourceKind` variant, so the `opshub://<kind>/<id>` composite is stored as the `resource_kind`/`resource_id` column pair on both `mcp_confirmations` and `mcp_audit` with a real foreign key, the kind's `mime_type` and `<kind>:read` permission are joined rather than restated in nine adapters, and the FR-F047-14 `resource_uri` filter becomes an indexed predicate instead of a string match; the kind members carry data, so they are a lookup table rather than a bare check constraint. `mcp_rate_limit_buckets(bucket text primary key check (bucket in ('calls','mutations','search')), capacity int not null, burst int not null, window_seconds int not null)` holds the three policy rows that `mcp_rate_limits` previously repeated in `capacity` and `window_seconds` on every token row; `mcp_rate_limits` is now purely the per-token bucket state `(tenant_id, token_id, bucket)` keyed to that policy. Externally visible shapes are unchanged: `resources/list`, `resources/read`, `tools/call` `structuredContent.summary`, `ConfirmationResponse.resource_uri`, and `McpAuditResponse.resource_uri` still carry the `opshub://<kind>/<id>` string and the same `summary` object — `ConfirmationRepository` and `McpAuditRepository` split the URI on write and recompose it on read, and `GET /api/v1/mcp/audit?resource_uri=` is parsed into the column pair before the query.
- `jsonb` audit (decision section 2): `mcp_confirmations.summary` stays `jsonb` — it is the proposed-mutation diff, a per-tool schema-less list of `{ field, before, after }` values whose `before`/`after` are typed cell values from F007, rendered verbatim by `ChangeSummaryDiff` and never filtered, joined, sorted, aggregated, or constrained on. The scalars the product does read by key moved out of it: `operation` is now a checked `text` column and the target is the `resource_kind`/`resource_id` pair, both of which the approvals list and the audit filters use. `mcp_audit` holds no `jsonb` at all — tool arguments are stored only as `arguments_digest bytea` per FR-F047-11 and every FR-F047-14 filter hits a column — and `mcp_rate_limits`, `mcp_rate_limit_buckets`, and `mcp_resource_kinds` hold none. These are the only `jsonb` columns in the module.
- Invariants: `mcp_audit` is partitioned monthly by `occurred_at` with three months created ahead, and carries the F003 `audit_immutable` trigger rejecting `UPDATE` and `DELETE`; `consumed_at is not null` exactly when `status = 'consumed'` (check); `approved_at is not null` when `status in ('approved','consumed')` (check); `check ((resource_kind is null) = (resource_id is null))` on both `mcp_confirmations` and `mcp_audit`, so a target is either fully identified or absent, and `resource_kind is not null` is required whenever `operation <> 'create'`; a partial unique index `mcp_confirmations_open_idx on (tenant_id, token_id, tool, arguments_hash) where status = 'pending'` collapses repeated proposals of the identical change into one row; `mcp_resource_kinds` contains exactly the nine kinds and `mcp_rate_limit_buckets` exactly the three buckets, asserted by an enumerating test over `ResourceKind` and `RateBucket` so a new variant without a row fails the build rather than the request.
- Indexes: `mcp_confirmations(tenant_id, status, expires_at)` for the sweeper and the approvals list, `mcp_confirmations(actor_id, status)`, `mcp_confirmations(tenant_id, resource_kind, resource_id) where status = 'pending'` for the target link on the approvals page, `mcp_audit(tenant_id, occurred_at desc)`, `mcp_audit(tenant_id, actor_id, occurred_at desc)`, `mcp_audit(tenant_id, resource_kind, resource_id, occurred_at desc)` serving the `resource_uri` filter, `mcp_audit(correlation_id)`, `mcp_rate_limits(refilled_at)` for the bucket sweeper, `mcp_rate_limits(token_id)` for revocation cleanup.
- Audit actions written through F003 `record_audit` in addition to `mcp_audit`: `mcp.confirmation.approve`, `mcp.mutation.execute`, `mcp.token.denied`.
- Retention/deletion: `mcp_audit` partitions follow the F027 retention policy with a 400-day default and are detached rather than deleted; `mcp_confirmations` rows are purged 30 days after `expires_at` or `consumed_at` by `ConfirmationRepository::purge_settled_confirmations`; rollback drops the five tables and the partitions in child-before-parent order — `mcp_audit` partitions, `mcp_audit`, `mcp_rate_limits`, `mcp_confirmations`, then the `mcp_rate_limit_buckets` and `mcp_resource_kinds` lookups — plus the trigger.

### React/TypeScript

- Routes `/admin/mcp` and `/admin/mcp/audit/:eventId` in `apps/web/src/features/mcp/`; components `McpPage`, `PendingApprovalsTable`, `ChangeSummaryDiff`, `ApproveDialog`, `ExpiryCountdown`, `McpActivityTable`, `McpCallDrawer`, `ConnectClientPanel`.
- State: TanStack Query keys `['mcp-confirmations', status]`, `['mcp-audit', filters, cursor]`, `['mcp-audit-event', id]`; approving invalidates both confirmation and audit keys; the approvals list polls every 15 seconds while a pending row is visible.
- API client: generated `McpApi` with `listAudit`, `getAuditEvent`, `listConfirmations`, `approveConfirmation`; `approveConfirmation` sends an `Idempotency-Key` per click and surfaces `409 conflict` as the `Expired` state rather than an error toast.
- Telemetry: `mcp_approval_viewed`, `mcp_approval_approved`, `mcp_approval_expired`, `mcp_activity_filtered`, `mcp_connect_panel_copied` with `tool` and `decision` dimensions.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F047-01 through FR-F047-15 and NFR-F047-01 through NFR-F047-04 in `testing/features/F047/requirements/cases.md`
- [ ] Failure/edge-case tests: unsupported protocol version, unknown method, malformed JSON, batch of 11, unknown `opshub://` kind, arguments changed between proposal and retry, approval after expiry, double consume, revoked token mid-stream, oversized resource body
- [ ] Permission-negative and tenant-isolation tests: token without `mcp:access`, token without `records:write` sees no mutating tools, unreadable resource returns `not_found` on both list and read, tenant B confirmation id returns `404`, non-owner non-admin approval returns `403`
- [ ] Rust unit tests: `crates/domain/src/mcp/` URI parsing, redaction, truncation, change-summary construction, arguments hashing, rate-bucket refill
- [ ] API contract/integration tests: every JSON-RPC method and both REST routes with success and each mapped error code against the stub MCP client
- [ ] Database migration/constraint tests: append-only trigger, status checks, `resource_kind`/`resource_id` both-or-neither check, unknown `resource_kind` and unknown `bucket` rejected by their foreign keys, lookup seeds complete for all nine kinds and three buckets, partial unique index on open confirmations, partition creation, rollback ordering
- [ ] React component tests: `PendingApprovalsTable`, `ChangeSummaryDiff`, `ApproveDialog`, `ExpiryCountdown`, `McpActivityTable` states
- [ ] Browser E2E tests: propose, approve, retry, and observe the audit rows through `/admin/mcp`
- [ ] Accessibility tests: axe on `/admin/mcp` and the drawer, diff semantics, countdown announcements, dialog focus
- [ ] Performance/load tests: manifest and list latencies, tool-call overhead, 200 concurrent SSE streams

### Fast fanout configuration

- Test harness path: `testing/features/F047/`
- Feature flag: `F047_FEATURE`
- Fixture/seed factory: `testing/fixtures/mcp.rs` builds tenants A and B, a member with `mcp:access` plus `records:read`, a member with `records:write`, a tenant-admin, three workspaces with 40 tasks, 12 tickets, 6 documents with revisions, 2 dashboards, and 2 workflows, plus tokens per actor and a 5,000-resource generator for the performance lane
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC, fixed HMAC cursor key, fixed argument hashes
- Mock/stub contracts: the stub MCP client in `testing/harness/mcp/client.rs` speaks JSON-RPC 2.0 in-process over a `tower::Service` with no network listener, records every request and response frame, and replays a recorded conformance script (`initialize`, `resources/list`, `resources/read`, `tools/list`, `tools/call` read, `tools/call` mutate, approve, `tools/call` retry); the SSE stream is driven by an in-memory event bus fed from the outbox stub
- Parallel isolation: one schema per test worker, tenant ID per test, in-process transport per test so no port is bound
- Targeted command: `cargo xtask test-feature F047`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F047/`

## 6. Acceptance criteria

```gherkin
Feature: MCP access with permission filtering and mutation approval

Scenario: Resources are filtered to what the actor may read
  Given tenant A has 40 tasks and the calling token's actor may read 12 of them
  When the stub client calls resources/list with kind task
  Then exactly 12 descriptors are returned with opshub://task/<id> URIs
  And resources/read on an unreadable task returns JSON-RPC -32002 with code not_found

Scenario: A mutating tool stops at the approval gate
  Given a token with records:write calls tools/call update_record changing due_date on task "Ship beta"
  When the first call is made
  Then no write occurs, an mcp_confirmations row is pending with the field diff, mcp.mutation-proposed.v1 is published
  And the response carries structuredContent.code confirmation_required with a confirmation_id

Scenario: Approval unlocks exactly one execution
  Given the proposing member approves that confirmation through POST /api/v1/mcp/confirmations/{id}/approve
  When the client retries tools/call with the same arguments and confirmation_id
  Then the due_date is written once, the row becomes consumed, and mcp.tool-called.v1 is published
  And a second retry with the same confirmation_id returns JSON-RPC -32003 with code conflict

Scenario: Changed arguments invalidate an approval
  Given an approved confirmation for due_date 2026-09-24
  When the client retries with due_date 2026-10-01 and the same confirmation_id
  Then the call returns -32602 with reason arguments_changed and nothing is written

Scenario: Every call is audited
  Given the stub client has run the conformance script
  When a tenant-admin reads GET /api/v1/mcp/audit
  Then one mcp_audit row exists per JSON-RPC method call with decision, outcome, and correlation_id
  And an UPDATE against mcp_audit raises audit_immutable
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F028 (list, cursor, error schema, correlation IDs, OpenAPI generation the manifest derives from); F045 (documents, folders, revisions read by the document and folder adapters); F038 (API tokens, scopes, bearer authentication); F003 (`authz::check`, `record_audit`, append-only partitioned audit); F004 (outbox events, metrics, secret source); decisions sections 1, 3, 8, 9; contracts row F047
- Blocks: none
- Conflicts with: none (disjoint owned paths; `crates/contracts/src/mcp/**` is distinct from F028's `crates/contracts/src/public-api/**`)
- External dependencies: none at runtime — the protocol harness runs against the in-process stub MCP client, and no third-party MCP SDK is linked
- Risks and mitigations: protocol version churn, mitigated by pinning `2025-06-18` in `initialize` and asserting the negotiated version in the conformance script so a bump is a deliberate ticket; over-broad reads through a forgotten adapter, mitigated by a lane test that enumerates `ResourceKind` and fails when an adapter lacks a permission-negative case; approval fatigue leading humans to rubber-stamp, mitigated by the field-level diff and the 15-minute expiry rather than a persistent grant; audit volume from chatty clients, mitigated by monthly partitions, the digest-only argument storage, and the per-token rate buckets; a mutating tool bypassing the gate, mitigated by `call_tool` taking the confirmation as a required typed argument for every `ToolHandler` whose `read_only` is false
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F028 and F045 accepted and archived; F038 scopes include `mcp:access`
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F047/`
- [ ] Migration file name and owned paths claimed; `services/mcp` crate present in the workspace
- [ ] Stub MCP client and conformance script available in `testing/harness/mcp/`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] `mcp_audit` rows and the four outbox events verified for every method, decision, and error path
- [ ] Tool manifest hash checked in and `cargo xtask check-contracts` reports no drift
- [ ] `cargo xtask check-persistence` passes: all SQL in `crates/persistence/src/mcp/`, no pool or `sqlx::query*` in `services/mcp`, `crates/domain/src/mcp/`, or the test lanes
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` passes
- [ ] Rollback verified: disable `F047_FEATURE`, run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- OpsHub now speaks the Model Context Protocol at `POST /mcp/v1` with an SSE notification stream. MCP clients authenticate with a scoped API token, see only the workspaces, documents, folders, projects, tasks, tickets, dashboards, workflows, and audit history the actor may read, and call five read tools. The five mutating tools stop at a human approval gate that shows a field-level diff at `/admin/mcp`; approvals expire in 15 minutes and unlock exactly one execution. Every call is rate-limited per token and recorded in an append-only MCP audit log readable at `GET /api/v1/mcp/audit`.
- Migration adds `mcp_confirmations`, `mcp_audit` (monthly partitions, append-only), `mcp_rate_limits`, and the `mcp_resource_kinds` and `mcp_rate_limit_buckets` lookups that give resource targets and rate policies real foreign keys; rollback drops them children first. Feature is off by default behind `F047_FEATURE`.
