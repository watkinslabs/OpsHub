---
id: F065
type: feature
status: planned
priority: P2
owner: platform
estimate: 8
target_milestone: M5
parent_epic: E006
depends_on: [F002, F038, F064]
blocks: []
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/signup/**, crates/persistence/src/signup/**, services/api/src/signup/**, services/worker/src/signup/**, apps/web/src/features/signup/**, services/api/migrations/*_signup_*.sql, testing/features/F065/**]
feature_flag: F065_FEATURE
flag_default: off
branch: f065-self-serve-signup-and-trials
started_at: null
finished_at: null
---

# F065 — Self-serve signup and trials

## 1. Identity and dates

- Branch: `f065-self-serve-signup-and-trials`
- Capability area: enterprise security and administration, commercial onboarding (spec 5.8 SEC-01 tenant isolation, section 4 Tenant entity, section 10 plan and entitlement packaging)
- Aggregate: `signup`
- Module slug: `signup`

### Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 7, 9
- Canonical contract: `docs/capability-contracts.md` row F065

## 2. Requirement specification

### Problem and user outcome

Today the only way a tenant can exist is `POST /api/v1/tenants` by a `platform-operator` (FR-F002-01), so every customer needs a human in the loop before they can see the product. That is correct for enterprise deals and fatal for evaluation: a prospect who wants to try OpsHub on a Tuesday evening cannot. This feature adds one unauthenticated path from an email address to a working trial tenant. It does not add a second way to create a tenant: provisioning calls the F002 `create_tenant` use case with a system `platform-operator` context, so the `tenants`, `users`, and role-binding writes stay in exactly one place and the F003 seed hook still makes the first user a `tenant-admin`. The operator route keeps working unchanged.

Because the front door is unauthenticated it is also the most attacked surface in the product. It must not become a customer-enumeration oracle, a mail relay, or a source of thousands of half-created tenants full of personal data.

As a prospective customer, I want to enter my work email and a workspace name, confirm the email, pick my workspace address, and land inside a working 14-day trial with my own tenant, so that I can evaluate OpsHub without contacting sales. As the platform operator, I want that door rate limited, bot checked, non-enumerating, and self-cleaning, so that self-serve does not cost me an incident.

### Functional requirements

- **FR-F065-01:** `POST /public/signup` is unauthenticated and accepts `{ email, company_name, bot_token, company_website, elapsed_ms, utm?: { source, medium, campaign }, requested_slug? }`; it validates `email` as an RFC 5322 addr-spec of at most 254 characters, `company_name` 2–120 characters, and `requested_slug` against the F002 slug grammar `^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$` at 3–63 characters; on any accepted shape it returns `202` with `{ status: "pending_verification", expires_in_seconds: 86400 }` and no other field.
- **FR-F065-02:** `POST /public/signup` returns that identical `202` body whether the email already belongs to a user, the tenant slug is taken, the domain is on the disposable list, or the request tripped a rate limit that still allows silent absorption; the response never varies by status code, body, header, or measurable latency (the handler pads to a fixed 250 ms floor). What differs is only the mail F037 sends: a new prospect gets the verification message, an address that already has an active user gets a "you already have an account" message with a sign-in link and no token, and a suppressed request gets no mail at all. No route in this feature confirms that a given email or tenant exists.
- **FR-F065-03:** Anti-abuse runs before any row is written: `check_rate_limit` (F038 `rate_limit_buckets`) enforces 5 signups per hour per IP, 20 per hour per IPv4 `/24` or IPv6 `/48`, and 3 per 24 hours per `email_hash`; `GET /public/signup/availability` allows 60 per minute per IP; `GET /public/signup/{token}` and `POST /public/signup/{token}/complete` allow 10 per hour per IP and at most 5 attempts per token row. A bucket breach on the availability and token routes returns `429 rate_limited` with `Retry-After`; a breach on `POST /public/signup` is absorbed under FR-F065-02 and increments `signup_rejected_total{reason="rate_limited"}`.
- **FR-F065-04:** Bot defence combines three independent checks through the `BotCheck` trait (`TurnstileBotCheck` in production against the Cloudflare Turnstile siteverify endpoint, `StaticBotCheck` in tests): `bot_token` must verify against the deployment secret `signup/turnstile_secret`, the honeypot field `company_website` must be empty, and `elapsed_ms` must fall between 2,000 and 3,600,000. A failure writes one `signup_request_risk_flags` row per triggered check (`bot_token_invalid`, `honeypot_filled`, `timing_out_of_range`, or `botcheck_unavailable`) through `SignupRequestRepository::add_risk_flags`, sends no mail, and returns the FR-F065-02 body.
- **FR-F065-05:** The email domain is checked against a disposable-domain list compiled into `crates/domain/src/signup/disposable_domains.txt` and refreshed per release, plus a live MX lookup with a 2-second timeout; a listed domain or a domain with no MX record is rejected silently under FR-F065-02 with a `signup_request_risk_flags` row of `disposable_domain` or `no_mx`; a consumer mail domain (`gmail.com`, `outlook.com`, `yahoo.com` and the rest of the compiled consumer list) is accepted but gets a `consumer_domain` flag row, which the invitation console filters on through the `(flag, request_id)` index. `email_hash` is `SHA-256(pepper ‖ normalized_email)` where normalization lowercases, and for the consumer domains that ignore them, strips dots and `+tag` suffixes.
- **FR-F065-06:** `GET /public/signup/availability?slug=acme` returns `{ slug, available: bool }` and nothing else; `available` is `false` for a slug taken by an existing tenant, present in `reserved_slugs`, or soft-reserved by a live signup request, with no field distinguishing the three cases; the route accepts no email parameter, no listing, and no prefix search, so it discloses nothing beyond the single slug the caller already typed.
- **FR-F065-07:** A signup soft-reserves its slug: `signup_requests` carries a partial unique index on `lower(requested_slug)` where `status in ('pending','verified')`, so the first caller holds the name for the 24-hour token life. A second caller for the same slug is stored with `requested_slug = null` and a `slug_taken` row in `signup_request_risk_flags`, still receives the FR-F065-02 body, and is asked to choose an address at completion. The soft reservation is advisory only: the authority is F002 `create_tenant`, whose `SlugTaken` error surfaces at completion as `409 conflict` with `field_errors.slug = "taken"` without consuming the token, so the caller retries with another name.
- **FR-F065-08:** Verification uses one hashed, single-use, expiring token: 32 bytes from the OS CSPRNG encoded base64url, stored only as `SHA-256` in `signup_tokens.token_hash`, valid 24 hours, compared in constant time, never logged, never returned by any read route, and consumed (`consumed_at` set) only inside the successful provisioning transaction. `GET /public/signup/{token}` returns `{ email_masked, company_name, requested_slug, slug_available, expires_at, terms_version }` for a live token and `410 gone` with `reason` in `expired`, `consumed`, `abandoned` otherwise; a token that never existed returns the same `410 gone` with `reason: expired`. The first successful read is what proves the address: it moves the request from `pending` to `verified`, sets `verified_at`, and publishes `signup.verified.v1` exactly once; later reads before completion are idempotent and publish nothing.
- **FR-F065-09:** All signup mail goes through F037 `NotificationService::create` with category `system` and a `dedupe_key` of `signup:{request_id}:{kind}`; F065 owns no SMTP client, no template renderer, and no delivery table, and a resend (at most 3 per request, no sooner than 60 seconds apart) reuses the same token row rather than minting a second one. A delivery that F037 reports `failed` adds an `undeliverable` row to `signup_request_risk_flags` and does not retry outside the F037 schedule.
- **FR-F065-10:** `POST /public/signup/{token}/complete` with `{ slug, admin_display_name, timezone, accepted_terms_version }` provisions in one transaction: consume the token, call the F002 `create_tenant` use case under a system `platform-operator` `ActorContext` with `{ name: company_name, slug, plan: "free", region: "us-east", admin_email, admin_display_name }` so the tenant, the first user, and the `tenant-admin` binding are written by F002 and F003's seed hook exactly as the operator route writes them, write the trial entitlements of FR-F065-11, create the F064 subscription in `status: trialing`, publish `tenant.provisioned.v1`, and mint one session through the F038 `SessionIssuer` port with `auth_kind = signup` returning the `__Host-oh_session` cookie. F065 never inserts into `tenants`, `users`, `groups`, or `role_bindings`, and a rollback of any step rolls back all of them.
- **FR-F065-11:** A trial is 14 days from provisioning, capped at 10 active users and 5 GB of files, and grants F048 entitlements with `state: trial` and `trial_ends_at = provisioned_at + 14 days` for the modules `dynamic-views`, `workapps`, `calendar-app`, and `pivots`; `data-shuttle`, `datamesh`, `bridge`, `assets`, `ai-assist`, and `ai-insights` stay `state: none` and are shown as upgrade rows. The tenant row itself carries `plan: "free"` because F002 admits only `free|team|enterprise`; trial status lives in the subscription and the entitlements, never in a second plan column.
- **FR-F065-12:** At `trial_ends_at` the worker job `signup.trial_lifecycle` opens a 7-day grace period: F048 evaluation returns `trial_expired` for the four trial modules so they are read-only, core sheets, boards, and exports stay writable, and the tenant admin is notified on days 0, 3, and 6 of the grace period through F037. At the end of grace the job calls `POST /api/v1/tenants/{id}/suspend` (F002) so every write returns `403 denied` with `reason = tenant_suspended`; the tenant, its data, and its export path survive, and removal happens only under the F027 retention and purge rules.
- **FR-F065-13:** Conversion is F064's: the admin calls `PUT /api/v1/billing/subscription` with a paid plan, and the F065 consumer of `subscription.updated.v1` with `status: active` flips the four trial entitlements from `trial` to `active`, clears `trial_ends_at`, lifts a grace suspension raised by FR-F065-12, and writes an audit event. No tenant, user, sheet, or file is recreated, copied, or migrated during conversion, and a tenant that converts on the last day of grace loses nothing.
- **FR-F065-14:** A nightly worker job `signup.sweep` marks pending requests past `expires_at` as `abandoned` and publishes `signup.abandoned.v1`; 7 days after creation it scrubs `email`, `email_normalized`, `company_name`, `ip`, and `user_agent` from every request in any status, leaving `email_hash`, `created_at`, `status`, `tenant_id`, and the request's `signup_request_risk_flags` and `signup_request_utm` rows, none of which carry personal data; 30 days after creation it deletes the row, which cascades to its `signup_tokens`, `signup_request_risk_flags`, and `signup_request_utm` children. The job registers with the F027 retention registry as kind `signup_requests` with these fixed windows; because the data is pre-tenant it is not tenant-configurable and not subject to tenant legal holds, and the fixed windows are documented in the F027 policy console as read-only.
- **FR-F065-15:** `POST /api/v1/signup/invitations` requires `platform-operator` and accepts `{ email, company_name, slug?, trial_days (7–60), note? }`; it creates a request with `source: "invitation"`, skips the bot check and the disposable-domain rejection, pins `slug` into `reserved_slugs` with `reason: "pinned"` until the token expires, sends the invitation mail through F037, and returns `201` with `{ request_id, expires_at }`. This keeps the sales-led motion first class: an operator can still hand a named prospect a guaranteed workspace address.
- **FR-F065-16:** The public web flow lives at `/signup`, `/signup/verify-sent`, `/signup/complete/:token`, and `/signup/expired`, is reachable without a session, shows the same success screen for every accepted submission, checks slug availability as the user types (debounced 400 ms) without revealing why a name is unavailable, and ends by redirecting to the new tenant's workspace home with the session cookie already set.

### Non-functional requirements

- **NFR-F065-01 Performance:** `POST /public/signup` responds in 250–600 ms p95 (a deliberate constant-time floor, not a budget), `GET /public/signup/availability` under 150 ms p95, `GET /public/signup/{token}` under 200 ms p95, and provisioning through `POST /public/signup/{token}/complete` under 3 s p95 including the F002 tenant transaction and the F064 subscription create; the `signup.sweep` job handles 100,000 requests in under 5 minutes in 1,000-row batches.
- **NFR-F065-02 Security/privacy:** no route reveals the existence of an email, a user, or a tenant (FR-F065-02, FR-F065-06); tokens exist only as SHA-256 hashes and are compared in constant time; `email_hash` uses a peppered digest so the retained hash is not a rainbow-table lookup of the address; logs and traces carry `request_id` and `email_hash` and never the address, the raw token, or `bot_token`; provisioning runs under a system `platform-operator` context that exists only inside the provisioning transaction and is never issued as a session; the public routes are exempt from the tenant gate but not from the rate limiter.
- **NFR-F065-03 Accessibility:** `/signup`, `/signup/complete/:token`, and `/signup/expired` pass axe with zero serious or critical violations at 320 px and 1,440 px, the slug availability result is announced through a polite live region rather than colour alone, the honeypot field is `aria-hidden` and removed from the tab order, every error is tied to its input through `aria-describedby`, and the Turnstile challenge exposes an accessible fallback.
- **NFR-F065-04 Reliability/observability:** provisioning is idempotent per token — a replayed `complete` after success returns `410 gone` with `reason: consumed` and never creates a second tenant; the `signup.sweep` and `signup.trial_lifecycle` jobs are idempotent per request and per tenant and resumable after restart; metrics `signup_started_total{source}`, `signup_verified_total`, `signup_rejected_total{reason}`, `tenants_provisioned_total{source}`, `trial_conversions_total`, and `trial_expirations_total` are exported; every span carries `request_id`, `correlation_id`, and, after provisioning, `tenant_id`.
- **NFR-F065-05 Abuse containment:** a burst of 10,000 signup attempts from one `/24` in 10 minutes creates at most 20 rows per hour, sends at most that many mails, and leaves p95 latency on authenticated `/api/v1` routes unchanged; the mail path cannot be used to send attacker-chosen text because the only variable content in a signup mail is the masked address, the company name (HTML-escaped, 120 chars), and the token link.

### Scope

Included: the four public routes and the operator invitation route, the `signup_requests`, `signup_request_risk_flags`, `signup_request_utm`, `signup_tokens`, and `reserved_slugs` schema with its seeded reservation list and the three `crates/persistence/src/signup/` repositories that own it, rate limiting and bot and disposable-domain defence, hashed single-use verification tokens, slug soft reservation and race resolution, provisioning through the F002 use case with the F003 seed hook and the F038 first session, trial entitlement grants, grace and suspension lifecycle, conversion handling on `subscription.updated.v1`, the abandonment sweep and PII scrub, and the public signup pages.

Excluded: tenant, user, group, and role writes themselves (F002, F003); login, sessions, MFA, and API tokens (F038); plan catalogue, pricing, payment collection, invoices, dunning, and the billing portal (F064); entitlement and feature-flag storage and evaluation (F048); mail transport, templates, preferences, and delivery records (F037); retention policy storage, legal holds, exports, and purge execution (F027); marketing site, pricing page, and analytics beyond the `utm` capture; in-tenant user invitations, which stay `POST /api/v1/users` (F002).

## 3. UX specification

- Entry points: the public route `/signup` linked from the marketing site and the invitation mail; the verification mail's button targets `/signup/complete/:token`; operators reach the invitation form at `/admin/signup-invitations`.
- Primary flow: a prospect opens `/signup`, types `dana@acme.io` and `Acme Robotics`, the Turnstile widget resolves, they submit, and the screen becomes `Check your email` naming the masked address and the 24-hour window with a `Resend` button that stays disabled for 60 seconds. They open the mail, land on `/signup/complete/:token`, see `acme-robotics` pre-filled with a green `Available`, set their display name and timezone, accept the terms, and submit; 2 seconds later they are inside `/w/acme-robotics` as a `tenant-admin` with a `Trial · 14 days left` chip in the app bar.
- Loading: submit buttons show an inline spinner and stay disabled; the availability field shows a small pending indicator, never a layout shift. Empty: not applicable, the form is the empty state. Error: field-level messages for `email`, `company_name`, and `slug`, and a single banner with `correlation_id` for `503 unavailable`. Success: redirect, no toast. Permission-denied: a non-operator opening `/admin/signup-invitations` sees the shared denied page.
- Expired and consumed tokens render `/signup/expired` with the reason in plain words (`This link has expired`, `This link was already used`) and a `Start again` action, never naming the email or the tenant.
- Slug field: as the user types, a debounced 400 ms check paints `Available` or `That address is not available` — one message for taken, reserved, and soft-reserved, with a suggested alternative generated locally by appending a short suffix.
- Trial surfaces: the app bar chip shows days remaining; from day 11 a dismissible banner offers `Choose a plan` linking to the F064 billing page; in grace the banner is not dismissible and names the suspension date; a suspended tenant shows the F002 suspended notice with the `Choose a plan` action still live.
- Responsive: the form is a single column from 320 px, and the Turnstile widget uses its compact variant under 400 px. Keyboard: a linear tab order over visible fields only, `Enter` submits, and after submission focus moves to the success heading.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide icons `UserPlus`, `MailCheck`, `ShieldCheck`, `Clock`, `Sparkles`; tokens from `apps/web/src/design/tokens.css`.

- Design: `design/artboards/Signup.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

### Rust backend

- Data access (decision section 2.1): `crates/persistence/src/signup/` holds `SignupRequestRepository` (owns `signup_requests`, `signup_request_risk_flags`, `signup_request_utm`), `SignupTokenRepository` (owns `signup_tokens`), and `ReservedSlugRepository` (owns `reserved_slugs`); no other class writes those five tables, and F065 reads tenant slugs through F002's `TenantRepository::slug_exists` rather than touching `tenants`. Named queries: `insert_pending`, `find_by_id`, `find_soft_reservation_for_slug`, `clear_requested_slug`, `mark_verified`, `mark_provisioned`, `count_recent_by_email_hash`, `increment_resend_count`, `add_risk_flags`, `list_risk_flags`, `save_utm`, `list_pending_past_expiry`, `mark_abandoned_batch`, `scrub_personal_data_batch`, `delete_requests_created_before` on `SignupRequestRepository`; `insert_for_request`, `find_live_by_token_hash`, `record_attempt`, `consume` on `SignupTokenRepository`; `is_reserved`, `pin_for_request`, `release_expired_pins` on `ReservedSlugRepository`. There is no generic query entry point, so the anonymous routes cannot grow an ad-hoc filter that turns into an enumeration oracle.
- The use cases below depend on those repository traits and contain no SQL, and neither do the `services/api/src/signup/` handlers, the `services/worker/src/signup/` jobs and consumer, or the F065 test fixtures. Completion is one `UnitOfWork` spanning `SignupTokenRepository::consume`, the F002 `create_tenant` use case with its own repositories, the F048 entitlement writes, the F064 subscription create, and the outbox enqueue, so FR-F065-10's all-or-nothing rollback is a property of the transaction rather than of handler code; the sweep's abandon, scrub, and delete batches each run in one `UnitOfWork` per 1,000 rows.
- Domain entities in `crates/domain/src/signup/`: `SignupRequest { id, source: SelfServe|Invitation, email: Option<Email>, email_normalized: Option<String>, email_hash: [u8; 32], company_name: Option<String>, requested_slug: Option<TenantSlug>, status: Pending|Verified|Provisioned|Abandoned|Rejected, risk_flags: Vec<RiskFlag>, utm: Option<Utm>, ip: Option<IpNet>, user_agent: Option<String>, trial_days: u16, terms_version: String, tenant_id: Option<Uuid>, resend_count: u8, created_at, verified_at, provisioned_at, scrubbed_at }`, `SignupToken { id, request_id, token_hash: [u8; 32], expires_at, consumed_at, attempts: u8 }`, `ReservedSlug { slug, reason: System|Brand|Routing|Profanity|Pinned, pinned_request_id, expires_at }`, `TrialGrant { tenant_id, modules: Vec<ModuleSlug>, trial_ends_at, grace_ends_at, user_cap: 10, storage_cap_gb: 5 }`.
- Use cases: `start_signup`, `check_availability`, `read_signup`, `resend_verification`, `provision_tenant`, `create_invitation`, `apply_trial_grant`, `expire_trials`, `convert_trial`, `sweep_abandoned`; `RiskAssessment::evaluate(bot, domain, rate)` returns the flags and whether mail is sent.
- Ports consumed, none reimplemented: `TenantProvisioner` (F002 `create_tenant`, the only tenant write path), `SessionIssuer` (F038, mints the first session), `RateLimiter::check_rate_limit` (F038 buckets), `NotificationSender` (F037 `NotificationService::create`), `EntitlementWriter` (F048 upsert), `SubscriptionStarter` (F064 trial subscription), `BotCheck`, `MxResolver`, `SecretSource` (F004).
- API endpoints (`services/api/src/signup/`): `POST /public/signup`, `GET /public/signup/{token}`, `POST /public/signup/{token}/complete`, `GET /public/signup/availability`, `POST /api/v1/signup/invitations`. DTOs `StartSignupRequest`, `StartSignupResponse { status, expires_in_seconds }`, `AvailabilityResponse { slug, available }`, `SignupTokenResponse { email_masked, company_name, requested_slug, slug_available, expires_at, terms_version }`, `CompleteSignupRequest { slug, admin_display_name, timezone, accepted_terms_version }`, `CompleteSignupResponse { tenant_id, slug, workspace_url, trial_ends_at }`, `CreateInvitationRequest`, `InvitationResponse`. The `/public` router is mounted outside the tenant gate and the session extractor, inside the rate-limit and correlation layers.
- Worker jobs (`services/worker/src/signup/`): `sweep` (nightly, abandonment plus PII scrub plus delete), `trial_lifecycle` (hourly, grace entry, reminder mails on grace days 0, 3, 6, suspension at grace end), `subscription_consumer` (JetStream consumer of `subscription.updated.v1` implementing FR-F065-13).
- Events published through `crates/events::enqueue` in the writing transaction: `signup.started.v1`, `signup.verified.v1`, `signup.abandoned.v1` with `aggregate: signup`, `aggregate_id: request_id`, and the platform tenant id `00000000-0000-0000-0000-000000000000` since no tenant exists yet; `tenant.provisioned.v1` with the new `tenant_id` and payload `{ request_id, slug, source, trial_ends_at, admin_user_id }`.
- Authorization: the four `/public` routes are anonymous and carry the catalog role `public`; `POST /api/v1/signup/invitations` requires `platform-operator`; provisioning constructs a short-lived system actor whose only permission is `tenant.create` and which is dropped with the transaction.
- Validation: email addr-spec ≤ 254, `company_name` 2–120, slug per F002 grammar and not in `reserved_slugs`, `timezone` an IANA identifier, `accepted_terms_version` equal to the deployment's current `terms_version`, `trial_days` 7–60 on invitations, `elapsed_ms` 2,000–3,600,000.
- Error mapping: `SignupError::TokenExpired | TokenConsumed | TokenUnknown → 410 gone`, `::SlugTaken → 409 conflict`, `::SlugReserved | InvalidSlug | StaleTerms → 400 invalid`, `::TooManyAttempts | RateLimited → 429 rate_limited`, `::ProvisioningFailed → 503 unavailable`, `AuthzError::Denied → 403 denied`; every silently absorbed rejection maps to the FR-F065-02 `202` and a `signup_rejected_total` increment.

### PostgreSQL/SQLx

- Migration `*_signup_*.sql` creates `signup_requests(id uuid pk, source text not null default 'self_serve' check (source in ('self_serve','invitation')), email citext, email_normalized citext, email_hash bytea not null, company_name text, requested_slug text, status text not null default 'pending', ip inet, user_agent text, trial_days smallint not null default 14 check (trial_days between 7 and 60), terms_version text not null, tenant_id uuid references tenants(id) on delete restrict, resend_count smallint not null default 0, created_at timestamptz not null, verified_at timestamptz, provisioned_at timestamptz, scrubbed_at timestamptz)`, `signup_tokens(id uuid pk, request_id uuid not null references signup_requests(id) on delete cascade, token_hash bytea not null, expires_at timestamptz not null, consumed_at timestamptz, attempts smallint not null default 0, created_at timestamptz not null)`, and `reserved_slugs(slug citext pk, reason text not null check (reason in ('system','brand','routing','profanity','pinned')), pinned_request_id uuid references signup_requests(id) on delete set null, expires_at timestamptz, created_at timestamptz not null)`.
- Normalized sets (decision section 2, no array column and no `jsonb` the product reads by key): `signup_request_risk_flags(request_id uuid not null references signup_requests(id) on delete cascade, flag text not null check (flag in ('rate_limited','bot_token_invalid','honeypot_filled','timing_out_of_range','botcheck_unavailable','disposable_domain','no_mx','consumer_domain','slug_taken','undeliverable')), flagged_at timestamptz not null default now(), primary key (request_id, flag))` replaces `risk_flags text[]`; the set is filtered (the operator console lists requests carrying `consumer_domain` or `undeliverable`), aggregated (`signup_rejected_total{reason}` is reconciled against it) and constrained, so it is rows, and the `check` closes the flag vocabulary that an array could not. `signup_request_utm(request_id uuid primary key references signup_requests(id) on delete cascade, source text not null, medium text not null, campaign text not null, created_at timestamptz not null)` replaces `utm jsonb`: the product read it by the known keys `source`, `medium`, and `campaign` and groups acquisition reporting by `source`, which decision section 2 calls a modelling error, and the one-row-per-request primary key keeps the field optional exactly as before. `StartSignupRequest.utm` stays a JSON object and the domain keeps `risk_flags: Vec<RiskFlag>` and `utm: Option<Utm>`, so no request or response shape changes; `SignupRequestRepository` fans both out to rows on write (`insert ... on conflict do nothing` for flags, a single upsert for utm) and reassembles them on read inside the request's `UnitOfWork`. The trial module set of FR-F065-11 likewise never becomes a column: `TrialGrant.modules` is fanned out to one `EntitlementWriter::upsert` call per module against F048's own table.
- `jsonb` audit: this module keeps no `jsonb` column. `utm` was the only candidate and is now `signup_request_utm` because it is read by key. Event payloads for `signup.started.v1`, `signup.verified.v1`, `tenant.provisioned.v1`, and `signup.abandoned.v1` are genuinely schema-less and stay `jsonb`, but they live in the F004 outbox table, which F065 only enqueues into and never queries by payload key.
- Invariants: unique index `signup_requests_slug_idx on (lower(requested_slug)) where status in ('pending','verified')` gives the soft reservation of FR-F065-07; unique index `signup_tokens_hash_idx on (token_hash)`; check `attempts <= 5`; check `resend_count <= 3`; check `status in ('pending','verified','provisioned','abandoned','rejected')`; check `tenant_id is not null = (status = 'provisioned')`; the `signup_request_risk_flags` primary key makes a flag idempotent per request so a retried assessment cannot duplicate it, and its `check` rejects an unknown flag at write time; `signup_request_utm` holds at most one row per request by its primary key and requires all three fields when present; `reserved_slugs` is seeded by the migration with 240 rows covering routing names (`www`, `api`, `app`, `admin`, `auth`, `login`, `logout`, `static`, `cdn`, `assets`, `docs`, `status`, `support`, `help`, `blog`, `mail`, `smtp`, `ws`, `realtime`, `mcp`, `webhooks`, `public`, `billing`, `security`, `signup`), brand names (`opshub`, `opshub-support`, `watkinslabs`), and a profanity list, all `reason` other than `pinned`.
- Indexes: `signup_requests(status, created_at)` for the sweep, `signup_requests(email_hash, created_at desc)` for the per-address limit, `signup_requests(tenant_id)` for conversion lookups, `signup_tokens(expires_at) where consumed_at is null`, `reserved_slugs(expires_at) where reason = 'pinned'`, `signup_request_risk_flags(flag, request_id)` for the operator console's flag filter and the rejection-reason reconciliation that formerly needed an array scan, and `signup_request_utm(source, created_at desc)` for acquisition reporting.
- Audit events written through `record_audit` (F003) on the authenticated and provisioning paths only: `signup.invitation-created`, `signup.provisioned`, `signup.trial-expired`, `signup.trial-suspended`, `signup.converted`; anonymous rejections are metrics and `signup_request_risk_flags` rows, not audit rows, so the audit log cannot be flooded from the public internet.
- Retention and deletion: FR-F065-14 windows are enforced by the `sweep` job; `signup_tokens`, `signup_request_risk_flags`, and `signup_request_utm` cascade with their request; the `tenant_id` foreign key is `on delete restrict`, so an F027 tenant purge deletes the signup request first and can never orphan a provisioned row; `reserved_slugs` rows with `reason = 'pinned'` are removed when `expires_at` passes; rollback drops the five tables children-first and leaves `tenants` untouched.

### React/TypeScript

- Routes in `apps/web/src/features/signup/`: `/signup`, `/signup/verify-sent`, `/signup/complete/$token`, `/signup/expired`, plus `/admin/signup-invitations`; components `SignupPage`, `SignupForm`, `TurnstileField`, `HoneypotField`, `VerifySentPage`, `CompleteSignupPage`, `SlugField`, `TrialBadge`, `TrialBanner`, `ExpiredTokenPage`, `InvitationForm`, `InvitationTable`.
- State: TanStack Query keys `['signup-token', token]`, `['signup-availability', slug]`, `['signup-invitations', cursor]`; the availability query is debounced 400 ms, deduplicated per slug, and never retried on `429`; the public pages mount outside the authenticated app shell and its session bootstrap.
- API client: generated `SignupApi` with `startSignup`, `checkAvailability`, `readSignupToken`, `completeSignup`, `createInvitation`; `TrialBadge` and `TrialBanner` read `trial_ends_at` from the F048 evaluate response rather than calling F065.
- Telemetry: `signup_form_submitted`, `signup_verification_opened`, `signup_completed`, `signup_slug_rejected`, `trial_banner_clicked` with `source` and `days_remaining`, never with the email address.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F065-01 through FR-F065-16 and NFR-F065-01 through NFR-F065-05 in `testing/features/F065/requirements/cases.md`
- [ ] Failure/edge-case tests: expired token, consumed token, unknown token, sixth token attempt, two signups racing one slug, slug taken between verification and completion, honeypot filled, `elapsed_ms` under 2,000, disposable domain, domain without MX, resend before 60 seconds, fourth resend, terms version drift
- [ ] Enumeration-negative tests: identical response bytes and latency band for a new address, an existing user's address, a taken slug, and a suppressed request; availability endpoint identical for taken, reserved, and soft-reserved slugs
- [ ] Permission-negative and tenant-isolation tests: anonymous caller on `POST /api/v1/signup/invitations`, a `tenant-admin` on the same route, a token from one request used on another, a completed signup unable to read or write any other tenant
- [ ] Rust unit tests: `crates/domain/src/signup/` token hashing and constant-time compare, email normalization and peppered hashing, risk assessment, slug validation against `reserved_slugs`, trial window arithmetic across a daylight-saving boundary, all against in-memory repository fakes so the domain crate links without SQLx
- [ ] API contract/integration tests: every route above with success and each error code, including the `202` absorption paths
- [ ] Database migration/constraint tests: soft-reservation partial index, token hash uniqueness, attempt and resend checks, `tenant_id` and status agreement, `signup_request_risk_flags` duplicate-flag rejection and unknown-flag rejection, `signup_request_utm` one-row-per-request, cascade delete of all three child tables, `source` and `trial_days` checks, seeded `reserved_slugs`, children-first rollback
- [ ] React component tests: `SignupForm`, `SlugField`, `VerifySentPage`, `CompleteSignupPage`, `ExpiredTokenPage`, `TrialBanner` states
- [ ] Browser E2E tests: full signup to workspace against the mock bot-check and mock mailbox, expired-link recovery, slug race between two browsers, trial expiry to grace to suspension to conversion
- [ ] Accessibility tests: axe on the three public pages, live-region announcement of availability, honeypot outside the tab order
- [ ] Performance/load tests: constant-time floor on `POST /public/signup`, provisioning p95, sweep throughput, 10,000-attempt burst containment

### Fast fanout configuration

- Test harness path: `testing/features/F065/`
- Feature flag: `F065_FEATURE`
- Fixture/seed factory: `testing/fixtures/signup.rs` seeds every row through `SignupRequestRepository`, `SignupTokenRepository`, and `ReservedSlugRepository` and never opens its own connection or writes SQL; it builds an empty platform with the seeded `reserved_slugs`, an existing tenant `acme` with an active user, a platform operator, a pending request with a live token, an expired request, a consumed request, a provisioned trial tenant at day 13, and a generator for 100,000 requests spread over 60 days
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC, fixed token bytes and pepper, fixed Turnstile verdicts
- Mock/stub contracts: `StaticBotCheck` with programmable verdicts, `StaticMxResolver` with a domain-to-verdict map, an in-memory `NotificationSender` recording category, `dedupe_key`, and rendered link, an in-memory `TenantProvisioner` spy that asserts F002 is the only tenant writer, a `SessionIssuer` stub, and F048 and F064 write spies
- Parallel isolation: one schema per test worker, per-test rate-limit key prefix, per-test IP range, per-worker mock port
- Targeted command: `cargo xtask test-feature F065`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F065/`

## 6. Acceptance criteria

```gherkin
Feature: Self-serve signup and trials

Scenario: A prospect signs up and lands in a working trial
  Given no tenant owns the slug "acme-robotics"
  When a visitor posts a valid signup, opens the verification link, and completes with that slug
  Then the F002 create_tenant use case is the only writer of the tenants and users rows
  And the first user holds the tenant-admin binding from the F003 seed hook
  And tenant.provisioned.v1 is published, the four trial entitlements end in 14 days, and a session cookie is returned

Scenario: Signup never reveals an existing customer
  Given "dana@acme.io" already belongs to an active user and the slug "acme" is taken
  When a visitor posts a signup for that address and that slug
  Then the response is 202 with the same body and latency band as a brand-new signup
  And the only mail sent is the "you already have an account" message with no token

Scenario: Two people race for one slug
  Given two visitors both request the slug "orbit"
  When both verify and both complete
  Then the first completion provisions the tenant
  And the second receives 409 conflict with field_errors.slug taken, keeps an unconsumed token, and succeeds with "orbit-hq"

Scenario: An unverified signup does not keep personal data
  Given a pending signup request created 8 days ago
  When the nightly signup.sweep job runs
  Then the request is abandoned, signup.abandoned.v1 was published, and the email, name, IP, and user agent are null
  And only the peppered hash, the status, and the request's signup_request_risk_flags rows remain

Scenario: A trial expires, then converts without data loss
  Given a trial tenant whose trial_ends_at has passed and whose grace period has ended
  When the tenant is suspended and the admin then converts through PUT /api/v1/billing/subscription
  Then the entitlements move from trial to active, the suspension is lifted, and every sheet, row, and file is unchanged
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F002 (`create_tenant` use case, slug grammar, suspend route, the F003 seed hook it already calls); F038 (`check_rate_limit` buckets, `SessionIssuer` for the first session); F064 (trial subscription creation and `subscription.updated.v1`); consumed but not depended on for ordering: F037 mail delivery, F048 entitlement writes, F027 retention registry, F004 secret source; decisions sections 3, 4, 7, 9; contracts row F065
- Blocks: nothing
- Conflicts with: none (disjoint owned paths; the `tenants` table is written only through F002's use case, never from `services/api/src/signup/`)
- External dependencies: Cloudflare Turnstile siteverify for the bot check with a documented offline mode, DNS MX resolution, and the compiled disposable-domain list refreshed per release
- Risks and mitigations: the public routes are the most exposed surface in the product, mitigated by three-layer rate limits, the bot check, the constant-time absorption of every rejection, and the burst test in NFR-F065-05; duplicating tenant creation would split the source of truth, mitigated by the `TenantProvisioner` port and a fixture spy that fails the suite if any signup code path writes `tenants` directly; a Turnstile outage would close the front door, mitigated by a documented degraded mode that falls back to the honeypot, timing, and rate checks and records a `botcheck_unavailable` flag row rather than rejecting everyone; trial abuse through repeated free tenants is bounded by the per-`email_hash` and per-network limits and visible through `tenants_provisioned_total{source}`; the pre-tenant personal data in `signup_requests` is bounded by the fixed 7-day scrub and 30-day delete of FR-F065-14
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F002, F038, and F064 accepted and archived
- [ ] F037, F048, and F027 ports available or stubbed behind their traits
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F065/`
- [ ] Migration file name, seeded `reserved_slugs` list, and owned paths claimed
- [ ] Turnstile test keys and the disposable-domain list committed under `crates/domain/src/signup/`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, enumeration-negative, accessibility, and performance gates pass
- [ ] The provisioner spy proves `tenants`, `users`, and `role_bindings` are written only through the F002 use case
- [ ] Events `signup.started.v1`, `signup.verified.v1`, `tenant.provisioned.v1`, and `signup.abandoned.v1` verified through the outbox with their payload contracts
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets`, `check-contracts`, and `check-persistence` pass, the last proving no SQL outside `crates/persistence/src/signup/`
- [ ] Rollback verified: disable `F065_FEATURE` (public routes return 404, operator route hidden), run the down migration, existing trial tenants keep working
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Prospects can start a 14-day trial themselves: enter a work email and company name at `/signup`, confirm through a single-use link that expires in 24 hours, choose a workspace address, and land inside their own tenant as its administrator. The trial includes dynamic views, workapps, the calendar app, and pivots for 10 users and 5 GB, followed by a 7-day grace period and then suspension until a plan is chosen; converting through billing keeps every row, file, and user.
- Operators keep the sales-led path unchanged and gain `POST /api/v1/signup/invitations` to pin a workspace address for a named prospect. Signup is rate limited per address, IP, and network, bot checked, closed to disposable domains, and non-enumerating; unverified signups lose their personal data after 7 days and are deleted after 30.
- Migration adds `signup_requests`, `signup_request_risk_flags`, `signup_request_utm`, `signup_tokens`, and `reserved_slugs` with the seeded reservation list; rollback drops them children-first. Feature is off by default behind `F065_FEATURE`.
