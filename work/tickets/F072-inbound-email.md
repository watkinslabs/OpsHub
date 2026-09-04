---
id: F072
type: feature
status: planned
priority: P1
owner: platform
estimate: 8
target_milestone: M3
parent_epic: E003
depends_on: [F006, F017, F037]
blocks: []
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/inbound-email/**, crates/persistence/src/inbound-email/**, services/api/src/inbound-email/**, services/worker/src/inbound-email/**, apps/web/src/features/inbound-email/**, services/api/migrations/*_inbound-email_*.sql, testing/features/F072/**]
feature_flag: F072_FEATURE
flag_default: off
branch: f072-inbound-email
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 2.1, 2.2, 3, 4, 5, 7, 9
- Capability contract: `docs/capability-contracts.md` row F072
- Threats: `docs/threat-model.md` sections 2.5, 3.1, 3.4, 3.5
- Authorization: `docs/authorization-model.md` section 3.2 (`sheet-editor`)

# F072 — Inbound email

## 1. Identity and dates

- Branch: `f072-inbound-email`
- Capability area: intake (spec phase 2 intake; epic E003)
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 2.2, 3, 4, 5, 7; `docs/capability-contracts.md` row F072
- Aggregate: `inbound-message`
- Module slug: `inbound-email`
- Milestone note: the plan places F072 in epic E003, whose other features are M2. Its dependencies F017 and F037 are M3, and the repository rules forbid depending on a later milestone, so this ticket targets M3.

## 2. Requirement specification

### Problem and user outcome

Most intake already exists as email. A customer writes, a vendor sends an invoice, a colleague forwards a thread — and someone retypes it into a sheet. Giving a sheet its own address removes the retyping: forward the mail, get the row. The address is on the public internet, so the specification is mostly about what happens to mail we did not ask for. An address anyone can guess is a write handle on the sheet; an unauthenticated sender is a forgery; an HTML body is attacker-controlled markup; a reply to a notification is an instruction to write to a specific row. Each of those is answered here or the feature is a liability.

As a sheet editor, I want a per-sheet email address whose body, subject, sender and attachments land in the columns I choose, and I want unauthenticated, unauthorised, oversized and looping mail refused without ever confirming that the address exists, so that intake reaches the team without opening the sheet to the internet.

### Functional requirements

- **FR-F072-01:** `POST /api/v1/inbound-addresses` with `{ sheet_id, label?, sender_policy?, auth_policy?, allow_list?, mappings, max_messages_per_hour?, max_message_bytes?, rotate_from_id? }` by a `sheet-editor` on the sheet mints an address whose local part is 22 lowercase Crockford base32 characters over 110 CSPRNG bits (`k7m2q9x4tb6vhz3npr8sfd@in.<deployment-domain>`); the local part is never derived from the sheet name, id, tenant or a counter, is unique across the deployment by a `lower(local_part)` unique index, and is returned only in this response and to actors holding `sheet-editor` on that sheet. A sheet may hold at most 5 `active` addresses; a sixth returns `409 conflict` with `field_errors.sheet_id = "address_limit"`.
- **FR-F072-02:** `GET /api/v1/inbound-addresses` lists addresses the caller may read with `sheet_id`, `status` and `sender_policy` filters, cursor paging and `limit` 1–100, returning `address`, `label`, `sender_policy`, `auth_policy`, `allow_list`, `mappings`, `status`, `max_messages_per_hour`, `max_message_bytes`, `last_message_at`, and counts of `accepted`, `rejected` and `quarantined` over the last 30 days; the arrays are assembled by `InboundAddressRepository` from `inbound_address_senders` and `inbound_address_mappings` in one batched read per page.
- **FR-F072-03:** `DELETE /api/v1/inbound-addresses/{id}` revokes the address: `status = 'revoked'`, `revoked_at`, `revoked_by`, and every later message to it is refused as `unknown_recipient` with no distinguishable response. Rotation is `POST` with `rotate_from_id`: a new address is minted, the old one keeps accepting for a 7-day grace window with `rotation_grace_ends_at` set and every message tagged `rotated_source` in the log, then hard-refuses. Revocation and rotation write audit events and are irreversible — a revoked local part is never reissued.
- **FR-F072-04:** `POST /webhooks/inbound-email/{provider}` with `provider` in `postmark`, `sendgrid`, `mailgun` verifies an HMAC-SHA256 signature over `timestamp || "\n" || raw_body` using the deployment secret `inbound-email/<provider>/webhook_secret` with a previous-secret window for rotation, constant-time comparison and a 300-second skew bound; a missing, stale or invalid signature returns `403 denied` and writes an audit event without persisting the message. A verified delivery inserts one `inbound_messages` row in the same transaction as its effect, keyed by a unique `(provider, provider_message_id)`; a repeat delivery returns `200` with the first message's id and creates no second row, no second event and no second row in the sheet.
- **FR-F072-05:** Every message records the provider's `spf`, `dkim` and `dmarc` results and the header-From alignment verdict on `inbound_messages`, and the outcome decides the disposition before any other policy runs: `dmarc = pass` continues; `dmarc = none` with an aligned `spf = pass` or `dkim = pass` continues and records `auth_note = 'dmarc_none_aligned'`; `dmarc = fail`, or `dmarc = none` with no aligned pass, is `rejected` with `rejection_reason` `dmarc_fail` or `unauthenticated_sender` under the default `auth_policy = 'enforce'` and `quarantined` under `auth_policy = 'quarantine'`; any `temperror` or `permerror` is `quarantined` regardless of policy so a transient DNS failure never destroys mail. No policy value, `sender_policy = 'anyone'` included, skips this check, and no failing message is ever applied to a sheet.
- **FR-F072-06:** `sender_policy` is `anyone`, `tenant_members` (the default on every new address) or `allow_list`. `tenant_members` requires the header-From address to resolve to an active user in the address's tenant; `allow_list` requires a match against an `inbound_address_senders` row of kind `address` (exact, case-insensitive) or `domain` (the domain or a subdomain of it), with 1–200 rows per address. A sender that fails the policy is `rejected` with `rejection_reason = 'sender_not_permitted'`.
- **FR-F072-07:** Every refusal — unknown recipient, revoked address, failed authentication, failed sender policy, exceeded limit — produces the identical provider-level bounce `550 5.1.1 Recipient address rejected` with no tenant, sheet, workspace, policy or reason detail, and the webhook responds in a constant time floor of 250 ms across all of them, so neither the body nor the latency confirms that an address exists. Bounces are suppressed to at most one per sending address per inbound address per hour and are never sent to a null return path, a bounce or an auto-reply.
- **FR-F072-08:** Limits are enforced per address from `inbound_rate_windows` on fixed one-hour tumbling windows: `max_messages_per_hour` (default 60, settable 1–600), 300 messages per address per day, 10 messages per sending address per inbound address per hour, and 2,000 messages per tenant per day; excess is `rejected` with `rejection_reason = 'rate_limited'`. `max_message_bytes` defaults to 26,214,400 and is settable 1,048,576–52,428,800; a larger message is `rejected` with `rejection_reason = 'too_large'` before any part is parsed.
- **FR-F072-09:** A message is `rejected` with `rejection_reason = 'loop_suspected'` and no bounce when `Auto-Submitted` is present and not `no`, when `Precedence` is `bulk`, `junk` or `list`, when `List-Id` or `List-Unsubscribe` is present, when `X-Loop` carries any address of this deployment, when the return path is null, when the header-From is an inbound address or the deployment notification sender, or when the message carries more than 25 `Received` headers. A reply token may carry at most 20 messages, after which it is retired and further replies are `rejected` with `rejection_reason = 'thread_cap'`.
- **FR-F072-10:** Body content is untrusted. The `text/plain` part is preferred; when only `text/html` exists it is reduced to text by an allowlist that drops `script`, `style`, `iframe`, `object`, `embed`, `svg`, `link`, `meta`, every event-handler attribute and every `javascript:` or `data:` URL, and no HTML is ever stored or rendered. Nothing in a message causes a network fetch: no remote image, stylesheet, link prefetch or `cid:` resolution outside the message's own parts. Cell values are written through the F008 write path as literal text with formula interpretation off, so a leading `=`, `+`, `-`, `@`, tab or carriage return survives as text and is never parsed by F035; the subject is truncated to 500 characters and `\r`, `\n` and NUL are stripped from any value reused in a bounce or a notification; the stored body text is capped at 262,144 bytes with an `body_truncated` issue when it is cut.
- **FR-F072-11:** `inbound_address_mappings` binds sources `subject`, `body_text`, `from`, `to`, `received_at`, `message_id` and `attachments` to columns. An accepted message creates one row through the F006 row path: `subject` to its text column (defaulting to the sheet's primary column), `body_text` to a text or long-text column, `received_at` to a date column, and `from` to a contact column resolved to the active tenant user with that address — when the address resolves to no user the cell holds the raw address as an unresolved contact and a `sender_unresolved` issue is recorded. `inbound-message.applied.v1` carries the message id, address id and row id.
- **FR-F072-12:** Attachments are stored through F017 against the created row: each part is offered to `POST /api/v1/files/uploads` with `target_kind = 'row'`, and the resulting file id, name, MIME type, size and disposition are recorded as one `inbound_message_attachments` row per part in `position` order. A part outside the F017 MIME allowlist is recorded `rejected_type`, one over the F017 size limit `rejected_size`, and one the F017 scan quarantines `quarantined`; at most 10 parts are stored and any beyond that are recorded `rejected_count`. A rejected or quarantined part never blocks the row, and a mapped file column holds only the parts that reached `clean`.
- **FR-F072-13:** A mapping that cannot be satisfied never drops the message. A missing, deleted or type-incompatible target column, a value the column rejects, or an unmapped source writes the value into the sheet's primary column when nothing else takes it and records one `inbound_message_issues` row with `code` in `mapping_failed`, `column_missing`, `type_mismatch`, `value_rejected`, `body_truncated`, `sender_unresolved`, `attachment_rejected` plus the column and reason; the row is created, `inbound-message.applied.v1` is published, the issues appear on the row and in the message log, and F037 notifies the address owner. The single mapping-side refusal is a sheet that is deleted or has no writable column, which is `rejected` with `rejection_reason = 'target_unavailable'`.
- **FR-F072-14:** F037 notification mail about a row sets `Reply-To: <local_part>+<token>@<domain>` where `token` is 32 CSPRNG bytes in base32url, stored only as SHA-256 in `inbound_reply_tokens.token_hash`, compared in constant time, bound to one tenant, address, row and recipient user, expiring in 30 days and revoked when the row is deleted. A valid token appends an F016 comment to its bound row attributed to the token's recipient and publishes `inbound-message.applied.v1` with the comment id and no new row. The plus-token is the only threading authority: `In-Reply-To` and `References` are recorded for display and never select a row, a message with `In-Reply-To` and no valid token creates a new row, and a token that does not match is `rejected` with `rejection_reason = 'invalid_thread_token'` behind the FR-F072-07 bounce.
- **FR-F072-15:** `GET /api/v1/inbound-messages` returns the log for addresses the caller may read, with filters `address_id`, `sheet_id`, `disposition`, `from`, `received_after`, `received_before`, cursor paging and `limit` 1–100, each entry carrying `received_at`, `from_address`, `from_display_name`, `subject`, `size_bytes`, `authentication` (`spf`, `dkim`, `dmarc`, `aligned`), `disposition`, `rejection_reason`, `row_id`, `comment_id`, attachments and issues. The route never returns body text, headers or the raw message, and cross-tenant ids return `404 not_found`.
- **FR-F072-16:** The raw RFC 822 message is stored through the F017 object store under `inbound-raw/<tenant_id>/<message_id>.eml`, referenced by `inbound_messages.raw_object_key`, downloadable through no route in this feature, and deleted by the F027 sweep after the retention policy key `inbound_raw_message` (default 30 days, settable 1–90); the metadata row is kept 400 days and then purged with the sheet's rows. `from_address` appears in logs, traces and metrics only as its domain, and a legal hold on the sheet suspends both sweeps.
- **FR-F072-17:** The web app gives a sheet an `Inbound email` settings surface showing the address with a copy control, the sender policy and allow-list editor, the column mapping editor, the limits, rotation and revocation, and a message log with the authentication results and disposition of each message, including rejected and quarantined messages that never became rows.

### Non-functional requirements

- **NFR-F072-01 Performance:** webhook acknowledgement p95 under 400 ms excluding the 250 ms constant-time floor of a refusal; a 5 MB message with three attachments becomes a row within 15 s p95 end to end; the message log and address list read under 500 ms p95 at 100,000 messages per tenant; the ingest job sustains 20 messages per second per deployment.
- **NFR-F072-02 Security/privacy:** the local part carries at least 110 bits of entropy and is never guessable from tenant content; every refusal is indistinguishable in body and timing; webhook signatures are verified before parsing with a rotation window; reply tokens are stored hashed and compared in constant time; no message content is fetched from the network, interpreted as a formula, or rendered as HTML; raw messages are encrypted at rest and reachable through no route; cross-tenant negatives and PII redaction are tested.
- **NFR-F072-03 Accessibility:** the inbound email settings surface and the message log pass axe with zero serious or critical violations; disposition and authentication results carry text as well as colour; the address copy control announces success; the log table is fully keyboard operable and the message drawer traps focus.
- **NFR-F072-04 Reliability/observability:** ingestion is idempotent per `(provider, provider_message_id)` and resumable after a worker restart; a poison message dead-letters after 3 attempts with the address left serving; metrics `inbound_messages_total{provider,disposition}`, `inbound_auth_results_total{mechanism,result}`, `inbound_bounces_suppressed_total` and `inbound_apply_duration_seconds`; every webhook and job runs in a span carrying `tenant_id`, `address_id`, `message_id` and `correlation_id`.
- **NFR-F072-05 Interoperability:** headers are decoded per RFC 2047 and RFC 2231, invalid byte sequences are replaced with U+FFFD, a declared charset is honoured with a UTF-8 fallback, `multipart/alternative`, `multipart/mixed`, `multipart/related` and `message/rfc822` forwards are parsed to a depth of 5, and an unparseable MIME structure is `quarantined` rather than dropped.

### Scope

Included: per-sheet unguessable addresses with rotation and revocation, sender policy and allow-lists, provider webhook with signature verification and replay protection, SPF/DKIM/DMARC recording and enforcement, rate, size, chain and loop limits, uniform non-confirming refusal, MIME parsing and content sanitisation, mapping to columns with issues instead of dropped mail, attachments through F017, reply-token threading into F016 comments, message log, raw-message retention under F027, and the settings and log surfaces.

Excluded: outbound mail transport and templates (F037); releasing or replaying a quarantined message, which has no route in this catalog row and is a follow-up; public form intake (F014); update-request links (F061); mailbox polling over IMAP or POP; calendar invitations and chat thread import (F029); attachment virus scanning itself and file versioning (F017); tenant-level DMARC reporting.

## 3. UX specification

- Entry points: sheet settings `Inbound email` at `/sheets/:sheetId/settings/inbound-email`; a workspace-level index at `/admin/inbound-email` listing every address and its recent traffic.
- Primary flow: an editor opens `Inbound email` on `Vendor intake`, clicks `Create address`, keeps the default sender policy `Tenant members only`, maps `Subject` to `Request`, `Body` to `Details`, `From` to `Requested by` and `Attachments` to the row, copies the address, forwards a supplier mail to it, and sees a new row plus an `Accepted` entry in the log within seconds.
- Log states: an `Accepted` entry links to its row; a `Rejected` entry shows the reason and the three authentication results and links to no row; a `Quarantined` entry shows the held-until date and states that it was never applied. Loading uses table skeletons; empty shows `No mail yet` with the address and a hint to forward one; error shows a banner with `correlation_id` and retry; denied shows the denied page for actors without `sheet-editor`; stale and offline reuse the F062 patterns.
- Rotation and revocation are confirm dialogs that state, in words, that the old address stops working — rotation after a 7-day grace window and revocation immediately — and that a revoked address is never reissued.
- Responsive: the settings column stacks above the log under 1,024 px; the log collapses to `From`, `Subject` and `Disposition` under 768 px; every dialog fits 320 px.
- Keyboard: the copy control is a button that announces `Address copied` through a polite live region; the log is arrow-navigable with `Enter` opening the message drawer, which traps focus and restores it on close; reduced motion disables the drawer transition.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for the address and identifiers (F062); Lucide icons `Mail`, `AtSign`, `ShieldCheck`, `ShieldAlert`, `Copy`, `RefreshCw`, `Ban`, `Paperclip`; tokens from `apps/web/src/design/tokens.css`.
- Design: `design/artboards/InboundEmail.dc.html`, generated by `design/generator/inbound_email.py`, showing the address settings, the sender policy, and a log holding an accepted, a DMARC-rejected and a quarantined message. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

### Rust backend

- Data access (decision section 2.1): `crates/persistence/src/inbound-email/` holds `InboundAddressRepository` (owns `inbound_addresses`, `inbound_address_mappings`, `inbound_address_senders`, `inbound_rate_windows`), `InboundMessageRepository` (owns `inbound_messages`, `inbound_message_attachments`, `inbound_message_issues`) and `InboundReplyTokenRepository` (owns `inbound_reply_tokens`). Child tables belong to their parent object's repository, so no two classes write the same table. Named queries: `find_active_by_local_part`, `list_addresses_for_scope`, `count_active_for_sheet`, `replace_mappings`, `replace_allow_list`, `match_allow_list`, `revoke_address`, `set_rotation_grace`, `bump_window`, `count_in_window`, `insert_message_once`, `find_by_provider_message_id`, `record_disposition`, `append_attachment`, `append_issue`, `list_messages`, `count_dispositions_since`, `mint_token`, `claim_token`, `retire_token`, `revoke_tokens_for_row`, `list_raw_expiring_before`, `clear_raw_key`. There is no generic query escape hatch. Every use case, MIME parser, handler and job below depends on these traits and contains no SQL; the webhook (message insert plus rate-window bump) and the apply step (row write through the F006 repositories, attachment rows, issue rows, disposition, outbox event) each run in one `UnitOfWork` that owns the transaction.
- Domain entities in `crates/domain/src/inbound-email/`: `InboundAddress { id, tenant_id, sheet_id, local_part, domain, label, sender_policy: Anyone|TenantMembers|AllowList, auth_policy: Enforce|Quarantine, mappings: Vec<Mapping>, allow_list: Vec<SenderRule>, status: Active|Revoked, rotation_grace_ends_at, rotated_from_id, max_messages_per_hour, max_message_bytes, version, audit fields }` with the two collections loaded from and written back to their child tables, `Mapping { source: Subject|BodyText|From|To|ReceivedAt|MessageId|Attachments, column_id }`, `SenderRule { kind: Address|Domain, pattern }`, `InboundMessage { id, tenant_id, address_id, provider, provider_message_id, rfc822_message_id, in_reply_to, from_address, from_display_name, to_address, subject, size_bytes, spf, dkim, dmarc, aligned, auth_note, disposition: Accepted|Rejected|Quarantined, rejection_reason, row_id, comment_id, reply_token_id, raw_object_key, raw_expires_at, received_at, applied_at }`, `AttachmentRecord { message_id, position, file_id, file_name, mime_type, size_bytes, content_id, disposition }`, `MessageIssue { message_id, code, column_id, detail }`, `ReplyToken { id, address_id, row_id, recipient_user_id, token_hash, expires_at, use_count, retired_at }`.
- Use cases: `create_address`, `rotate_address`, `revoke_address`, `list_addresses`, `verify_webhook`, `record_delivery`, `evaluate_authentication`, `evaluate_sender_policy`, `enforce_limits`, `detect_loop`, `parse_mime`, `sanitize_body`, `apply_to_row`, `append_thread_comment`, `list_messages`, `send_bounce`, `sweep_raw_messages`.
- Provider adapters in `crates/domain/src/inbound-email/providers/{postmark.rs, sendgrid.rs, mailgun.rs}` implement `InboundProvider { verify(signature, timestamp, raw_body) -> Result<(), Denied>, parse(raw_body) -> ProviderDelivery }`. The three members carry no stored data — the signature scheme lives in the adapter and the secret is reached by the `inbound-email/<provider>/webhook_secret` convention — so `provider` stays a `text` column with a `check` constraint rather than a lookup table (decision section 2).
- API endpoints (`services/api/src/inbound-email/`): `GET /api/v1/inbound-addresses`, `POST /api/v1/inbound-addresses`, `DELETE /api/v1/inbound-addresses/{id}`, `GET /api/v1/inbound-messages`, `POST /webhooks/inbound-email/{provider}`. DTOs: `InboundAddressResponse`, `CreateInboundAddressRequest`, `Page<InboundAddressResponse>`, `InboundMessageResponse`, `Page<InboundMessageResponse>`, `ProviderInboundEvent`. `allow_list`, `mappings`, `attachments`, `issues` and `authentication` stay JSON arrays and objects on the wire; the repositories fan them out to rows on write and reassemble them on read.
- Worker jobs (`services/worker/src/inbound-email/`): `ingest` (consumes verified deliveries, runs authentication, policy, limits, loop detection, parsing, sanitisation and apply), `bounce` (emits the uniform refusal through the F037 transport with per-sender suppression), `retention` (deletes raw objects past `raw_expires_at` and retires expired reply tokens).
- Events: `inbound-message.received.v1` at verified delivery, `inbound-message.applied.v1` when a row or comment is written, `inbound-message.rejected.v1` on every refusal including quarantine expiry; payloads follow the catalog conventions and carry the address id and disposition, never body text.
- Authorization: `sheet-editor` on the sheet for address creation, rotation and revocation; sheet read access for the message log and address list; the webhook is unauthenticated by session and authorized solely by the provider signature, deriving the tenant from the resolved local part; cross-tenant ids return `not_found`.
- Validation: `label` ≤ 120 characters; `mappings` 1–7 entries with distinct sources and columns belonging to the sheet; `allow_list` 1–200 rows required when `sender_policy = 'allow_list'`; `max_messages_per_hour` 1–600; `max_message_bytes` 1,048,576–52,428,800; `rotate_from_id` must name an `active` address on the same sheet.
- Error mapping: `InboundError::AddressLimit → 409 conflict`, `::InvalidMapping → 400 invalid`, `::BadSignature → 403 denied`, `::UnknownRecipient → 404 not_found`, `::LimitExceeded → 429 rate_limited`, `::ProviderUnavailable → 503 unavailable`, `AuthzError::Denied → 403 denied`; the webhook translates every message-level refusal into a `200` acknowledgement with a recorded disposition rather than an error status, so a provider never retries a decision.

### PostgreSQL/SQLx

- Migration `*_inbound-email_*.sql` is an expand phase (decision section 2.2) that adds only new tables. It creates `inbound_addresses(id uuid pk, tenant_id uuid not null, sheet_id uuid not null references sheets(id) on delete cascade, local_part text not null, domain text not null, label text, sender_policy text not null default 'tenant_members' check (sender_policy in ('anyone','tenant_members','allow_list')), auth_policy text not null default 'enforce' check (auth_policy in ('enforce','quarantine')), status text not null default 'active' check (status in ('active','revoked')), rotation_grace_ends_at timestamptz, rotated_from_id uuid references inbound_addresses(id) on delete restrict, max_messages_per_hour int not null default 60 check (max_messages_per_hour between 1 and 600), max_message_bytes int not null default 26214400 check (max_message_bytes between 1048576 and 52428800), last_message_at timestamptz, revoked_at timestamptz, revoked_by uuid references users(id) on delete restrict, version bigint not null default 1, created_by, created_at, updated_by, updated_at, deleted_at)`, `inbound_messages(id uuid pk, tenant_id uuid not null, address_id uuid not null references inbound_addresses(id) on delete cascade, provider text not null check (provider in ('postmark','sendgrid','mailgun')), provider_message_id text not null, rfc822_message_id text, in_reply_to text, from_address text not null, from_display_name text, to_address text not null, subject text, size_bytes int not null, spf text not null check (spf in ('pass','fail','softfail','neutral','none','temperror','permerror')), dkim text not null check (dkim in ('pass','fail','softfail','neutral','none','temperror','permerror')), dmarc text not null check (dmarc in ('pass','fail','softfail','neutral','none','temperror','permerror')), aligned boolean not null default false, auth_note text, disposition text not null check (disposition in ('accepted','rejected','quarantined')), rejection_reason text check (rejection_reason in ('unknown_recipient','dmarc_fail','unauthenticated_sender','sender_not_permitted','rate_limited','too_large','loop_suspected','thread_cap','invalid_thread_token','target_unavailable','unparseable')), row_id uuid references rows(id) on delete set null, comment_id uuid, reply_token_id uuid references inbound_reply_tokens(id) on delete set null, provider_snapshot jsonb not null, raw_object_key text, raw_expires_at timestamptz, received_at timestamptz not null, applied_at timestamptz, created_at, updated_at)` and `inbound_message_attachments(id uuid pk, tenant_id uuid not null, message_id uuid not null references inbound_messages(id) on delete cascade, position smallint not null check (position between 1 and 50), file_id uuid references files(id) on delete set null, file_name text not null, mime_type text not null, size_bytes int not null, content_id text, disposition text not null check (disposition in ('stored','rejected_type','rejected_size','rejected_count','quarantined')))`.
- Normalized sets (decision section 2, no array column anywhere in this module): `inbound_address_mappings(address_id uuid not null references inbound_addresses(id) on delete cascade, tenant_id uuid not null, source text not null check (source in ('subject','body_text','from','to','received_at','message_id','attachments')), column_id uuid not null references columns(id) on delete restrict, primary key (address_id, source), unique (address_id, column_id))` replaces the per-source column ids the settings surface would otherwise repeat; `inbound_address_senders(address_id uuid not null references inbound_addresses(id) on delete cascade, tenant_id uuid not null, kind text not null check (kind in ('address','domain')), pattern text not null, primary key (address_id, kind, pattern))` replaces the allow-list, which the policy check joins on rather than scans; `inbound_message_issues(message_id uuid not null references inbound_messages(id) on delete cascade, tenant_id uuid not null, code text not null check (code in ('mapping_failed','column_missing','type_mismatch','value_rejected','body_truncated','sender_unresolved','attachment_rejected')), column_id uuid, detail text not null, primary key (message_id, code, coalesce(column_id, '00000000-0000-0000-0000-000000000000'::uuid)))` replaces an issue payload the row drawer and the log both read by key; `inbound_reply_tokens(id uuid pk, tenant_id uuid not null, address_id uuid not null references inbound_addresses(id) on delete cascade, row_id uuid not null references rows(id) on delete cascade, recipient_user_id uuid not null references users(id) on delete restrict, token_hash bytea not null, expires_at timestamptz not null, use_count smallint not null default 0 check (use_count between 0 and 20), retired_at timestamptz, created_at)`; `inbound_rate_windows(address_id uuid not null references inbound_addresses(id) on delete cascade, tenant_id uuid not null, bucket_key text not null, window_start timestamptz not null, message_count int not null default 0, primary key (address_id, bucket_key, window_start))` is the counter behind FR-F072-08, a rebuildable cache whose only reader is `enforce_limits` and whose rows the retention job trims after 48 hours.
- `jsonb` audit: `inbound_messages.provider_snapshot` stays `jsonb` because it is the verbatim provider webhook payload snapshot kept for support and signature disputes; it is never filtered, joined, sorted or constrained, and every query over the log uses `address_id`, `disposition`, `received_at`, `from_address`, `dmarc` and `rejection_reason`, all of which are columns. No other `jsonb` column exists in this module; body text is `text` and the raw message is an object-store key, not a column.
- Invariants: `unique (domain, lower(local_part))` on `inbound_addresses` makes a local part unique deployment-wide and a revoked one unreissuable, because revoked rows are kept; `unique (provider, provider_message_id)` on `inbound_messages` is the replay guard and is inserted in the same transaction as the effect; at most 5 `active` addresses per sheet enforced by `InboundAddressRepository::count_active_for_sheet` inside the creating transaction; `unique (message_id, position)` on `inbound_message_attachments`; `unique (token_hash)` on `inbound_reply_tokens`; `disposition = 'accepted'` requires exactly one of `row_id` or `comment_id` and `disposition <> 'accepted'` requires both to be null, both checked by the repository in the transaction that sets the disposition; `rejection_reason` is null unless the disposition is `rejected`; `rotated_from_id` may not equal `id`.
- Indexes: `inbound_addresses(tenant_id, sheet_id, status)` and `inbound_addresses(status, rotation_grace_ends_at)` for the grace sweep; `inbound_messages(address_id, received_at desc)` for the log, `inbound_messages(tenant_id, disposition, received_at desc)` for the counts, `inbound_messages(tenant_id, from_address, received_at desc)` for the per-sender limit, `inbound_messages(raw_expires_at) where raw_object_key is not null` for the retention sweep; `inbound_address_senders(kind, pattern)` for the allow-list join; `inbound_message_attachments(message_id, position)`; `inbound_message_issues(message_id)`; `inbound_reply_tokens(row_id)` and `inbound_reply_tokens(expires_at) where retired_at is null`; `inbound_rate_windows(window_start)` for trimming. Every index is created `concurrently`.
- Audit events: `inbound-address.created`, `inbound-address.rotated`, `inbound-address.revoked`, `inbound-address.policy-updated`, `inbound-webhook.signature-rejected`, `inbound-message.rejected`, `inbound-message.quarantined`, `inbound-message.applied`.
- Retention/deletion: raw objects are deleted by the F027 sweep at `raw_expires_at` under the `inbound_raw_message` policy key; `inbound_messages` rows are purged at 400 days with their attachment and issue rows by cascade; revoking an address keeps its messages and its local part; deleting the sheet cascades addresses, messages, attachments, issues, tokens and rate windows; a legal hold on the sheet suspends both sweeps. Rollback drops the eight tables, children before parents, and is safe because the expand migration adds nothing to an existing table.

### React/TypeScript

- Routes `/sheets/:sheetId/settings/inbound-email` and `/admin/inbound-email` in `apps/web/src/features/inbound-email/`; components `InboundEmailPage`, `AddressCard`, `AddressDialog`, `SenderPolicyField`, `AllowListEditor`, `MappingEditor`, `LimitsField`, `RotateAddressDialog`, `MessageLogTable`, `MessageDetailDrawer`, `AuthResultChips`, `AttachmentList`.
- State: TanStack Query keys `['inbound-addresses', sheetId]`, `['inbound-address', id]`, `['inbound-messages', filter, cursor]`; creating, rotating or revoking an address invalidates the address keys and the log key.
- API client: generated `InboundEmailApi` with `listAddresses`, `createAddress`, `revokeAddress`, `listMessages`; the webhook has no client.
- Telemetry: `inbound_address_created`, `inbound_address_rotated`, `inbound_address_revoked`, `inbound_address_copied`, `inbound_log_filtered`, `inbound_message_opened` with `sheet_id` and `address_id`, never the address or a sender.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F072-01 through FR-F072-17 and NFR-F072-01 through NFR-F072-05 in `testing/features/F072/requirements/cases.md`
- [ ] Failure/edge-case tests: replayed delivery, stale and rotated webhook signature, every SPF/DKIM/DMARC combination, allow-list subdomain match, hourly and per-sender limits, oversize message, auto-reply and mailing-list headers, 26 `Received` headers, HTML-only body with a script tag and a remote image, a body beginning with `=`, an unparseable MIME tree, a forged `In-Reply-To`, a token used 21 times, a deleted target column, an attachment the scanner quarantines
- [ ] Permission-negative and tenant-isolation tests: a viewer cannot create, rotate or revoke an address; a member of another tenant gets `not_found` on the address and the log; a local part from tenant A never resolves to tenant B; the address is absent from responses to actors without `sheet-editor`
- [ ] Rust unit tests: `crates/domain/src/inbound-email/` local-part entropy and uniqueness, signature verification, authentication decision table, allow-list matcher, limit windows, loop detector, MIME parser and sanitiser, formula-literal writer, token hashing and constant-time compare
- [ ] API contract/integration tests: every route above with success and each error code against a mock provider
- [ ] Database migration/constraint tests: local-part uniqueness including revoked rows, replay uniqueness, disposition and reason invariants, cascade on sheet delete, rollback
- [ ] React component tests: `AddressCard`, `AddressDialog`, `MappingEditor`, `MessageLogTable`, `MessageDetailDrawer` states
- [ ] Browser E2E tests: create an address, forward a mail, see the row; a DMARC-failing message rejected and absent from the sheet; a reply to a notification appended as a comment
- [ ] Accessibility tests: axe on both routes and the drawer, copy announcement, disposition not colour-only
- [ ] Performance/load tests: 20 messages per second sustained, 100,000-message log paging, apply latency

### Fast fanout configuration

- Test harness path: `testing/features/F072/`
- Feature flag: `F072_FEATURE`
- Fixture/seed factory: `testing/fixtures/inbound_email.rs` builds tenants A and B, a sheet `Vendor intake` with text, long-text, date, contact and file columns, a sheet editor and a viewer, one active address per policy, a reply token bound to a row, and a mock provider server for the three webhook formats
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC, fixed CSPRNG stream for local parts and tokens, fixed webhook secrets
- Mock/stub contracts: mock provider server in `testing/harness/providers/inbound-email/` signing and posting a corpus of `.eml` fixtures; F017 upload and scan stubs with programmable clean, quarantined and rejected outcomes; F037 transport stub recording bounces and notification `Reply-To` headers
- Parallel isolation: one schema per test worker, tenant id per test, mock provider port per worker, address domain per worker
- Targeted command: `cargo xtask test-feature F072`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F072/`

## 6. Acceptance criteria

```gherkin
Feature: Inbound email into a sheet

Scenario: A forwarded supplier mail becomes a row with its attachment
  Given an active address on sheet "Vendor intake" with sender policy tenant_members
  And subject, body, from and attachments mapped to columns
  When a tenant member sends a message with one PDF that passes SPF, DKIM and DMARC
  Then inbound-message.received.v1 and inbound-message.applied.v1 are published
  And one row carries the subject, the sanitised text body and the sender as a contact
  And the PDF is stored through F017 against that row with disposition stored

Scenario: A DMARC failure is refused without confirming the address
  Given an address with auth_policy enforce
  When a message arrives with dmarc fail
  Then the message is recorded with disposition rejected and reason dmarc_fail
  And no row is created and inbound-message.rejected.v1 is published
  And the bounce is the uniform recipient-rejected refusal with no tenant or sheet detail
  And the response time matches the refusal for an address that does not exist

Scenario: An authentication temperror is quarantined rather than lost
  Given an address with auth_policy enforce
  When a message arrives with dkim temperror
  Then the message is recorded with disposition quarantined and no row is created
  And the log shows it as held with its three authentication results

Scenario: A forged In-Reply-To cannot write to another row
  Given a reply token bound to row 1482
  When a message arrives with In-Reply-To naming row 9001 and no plus token
  Then no comment is appended to any row and a new row is created on the address's own sheet

Scenario: The same delivery twice creates one row
  Given a verified delivery with provider message id "pm-8817"
  When the provider posts it a second time
  Then the response is 200 with the first message id and the sheet still holds one row
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F006 (sheets, rows and the row write path), F017 (upload, MIME allowlist, size limits, scanning and the object store), F037 (mail transport for bounces and the notification `Reply-To` that carries the reply token); decisions sections 2, 2.1, 2.2, 3, 4, 5, 7; contracts row F072
- Blocks: none
- Conflicts with: none (disjoint owned paths)
- External dependencies: an inbound mail provider (Postmark, SendGrid or Mailgun) with a wildcard MX record on the deployment's inbound domain and a configured webhook secret; the mock provider stands in during tests
- Risks and mitigations: backscatter from bounces to forged senders, mitigated by per-sender suppression, no bounce to a null return path or an auto-reply, and no bounce on a loop rejection; address leakage through forwarding, mitigated by rotation with a grace window and by never printing the address in logs or telemetry; provider parsing differences, mitigated by an adapter per provider over a shared `.eml` corpus; an oversized attachment stream exhausting the worker, mitigated by refusing on declared size before parsing and by streaming parts to F017; quarantine growth, mitigated by the 30-day raw sweep and the 400-day metadata purge
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F006, F017 and F037 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F072/`
- [ ] Inbound domain, wildcard MX and per-provider webhook secrets provisioned in the deployment secret manager
- [ ] Migration file name and owned paths claimed; `design/artboards/InboundEmail.dc.html` regenerates from `design/generator/inbound_email.py`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] The refusal corpus proves body and timing are identical across unknown recipient, revoked address, authentication failure, policy failure and limit failure
- [ ] Audit events and outbox events verified for every address mutation, refusal and applied message
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets`, `check-contracts`, `check-persistence` and `check-design` pass
- [ ] Rollback verified: disable `F072_FEATURE`, run the down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- A sheet can be given its own unguessable email address; mail sent to it becomes a row with the subject, body, sender and attachments in chosen columns, and a reply to an OpsHub notification appends a comment to the row it was about. Senders are authenticated with SPF, DKIM and DMARC, restricted by a per-address policy, rate and size limited, and refused with a bounce that never confirms the address exists; message bodies are never rendered as HTML, never fetched from the network and never interpreted as formulas.
- Migration adds `inbound_addresses`, `inbound_address_mappings`, `inbound_address_senders`, `inbound_messages`, `inbound_message_attachments`, `inbound_message_issues`, `inbound_reply_tokens` and `inbound_rate_windows`; rollback drops them. Raw messages are kept 30 days by default under the F027 `inbound_raw_message` retention policy. Feature is off by default behind `F072_FEATURE`.
