---
id: F064
type: feature
status: planned
priority: P1
owner: platform
estimate: 8
target_milestone: M5
parent_epic: E006
depends_on: [F002, F048]
blocks: [F065]
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/billing/**, crates/persistence/src/billing/**, services/api/src/billing/**, services/worker/src/billing/**, apps/web/src/features/billing/**, services/api/migrations/*_billing_*.sql, testing/features/F064/**]
feature_flag: F064_FEATURE
flag_default: off
branch: f064-billing-and-subscriptions
started_at: null
finished_at: null
---

# F064 — Billing and subscriptions

## 1. Identity and dates

- Branch: `f064-billing-and-subscriptions`
- Capability area: administration and packaging (spec section 10 "Advanced modules use entitlement records plus feature flags; packaging is an administration concern"; spec 5.9 INT-03; spec section 3 tenant `plan` attribute)
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 7, 9; `docs/capability-contracts.md` row F064
- Aggregate: `subscription`
- Module slug: `billing`

## 2. Requirement specification

### Problem and user outcome

Nothing in OpsHub charges anyone today. `tenants.plan` already carries `free|team|enterprise` (FR-F002-02) and F048 already decides which modules a tenant may use, but no record says what a tenant agreed to pay, no counter says how much they used, and no invoice exists. Without this, plan changes are manual operator edits, a lapsed payment has no defined consequence, and F065 self-serve signup has nothing to convert a trial into.

F064 adds exactly one new source of truth — the subscription — and makes everything downstream a derivation of it. A plan change writes the subscription and then projects plan-derived entitlement records into the F048 store; F064 never keeps a second entitlement table and never gates a request itself. All money movement lives behind a payment provider port with one adapter, so the domain never sees a provider type and no test needs a real provider.

As a billing administrator, I want to see my current plan, change it with the price and proration shown before I confirm, watch metered usage accumulate against the plan's allowances, download invoices, and manage the payment method in the provider's hosted portal, so that I control cost without filing a ticket. As a tenant administrator, I want a payment failure to degrade my tenant slowly and loudly — notice first, premium modules next, write access last, data access never without warning — so that a lapsed card never silently destroys my team's work.

### Functional requirements

- **FR-F064-01:** `GET /api/v1/billing/subscription` returns `{ plan, status, provider, current_period_start, current_period_end, cancel_at_period_end, trial_ends_at, scheduled_plan, scheduled_effective_at, dunning: { stage, entered_at, next_action_at, retries_remaining }, seats: { included, in_use }, allowances: { seats, storage_gb, automation_runs }, payment_method: { brand, last4, exp_month, exp_year } or null, version }`; the response object shape is unchanged by normalization — `payment_method` is read from the tenant's `subscription_payment_methods` row by `SubscriptionRepository::load_payment_method` and is `null` when no row exists; `status` is one of `trialing`, `active`, `past_due`, `restricted`, `suspended`, `canceled`; a tenant with no `subscriptions` row is returned as the synthetic free subscription `{ plan: "free", status: "active", version: 0 }` rather than `404`.
- **FR-F064-02:** `PUT /api/v1/billing/subscription` by a `billing-admin` with `If-Match` and `Idempotency-Key` accepts `{ plan, apply: "immediate" | "period_end", cancel_at_period_end?: bool, preview?: bool }`; `plan` must be one of `free`, `team`, `enterprise` (the FR-F002-02 set) or the request returns `400 invalid` with `field_errors.plan`; `preview: true` returns the computed `ProrationPreview` and writes nothing; `enterprise` requires an existing provider payment method or returns `409 conflict` with `field_errors.payment_method = "required"`.
- **FR-F064-03:** An upgrade (`free→team`, `free→enterprise`, `team→enterprise`) applies immediately: the adapter changes the provider subscription with proration enabled, the credit for the unused remainder of the old plan and the charge for the remainder of the current period are computed as `unit_price * remaining_seconds / period_seconds` rounded half-up to the minor unit, and the resulting `ProrationPreview { credit_cents, charge_cents, net_cents, effective_at, next_invoice_at }` matches the provider's returned line items to the cent or the change is rejected with `502 unavailable` and no local write.
- **FR-F064-04:** A downgrade (`enterprise→team`, any plan `→free`) defaults to `apply: "period_end"`: `scheduled_plan` and `scheduled_effective_at = current_period_end` are stored, entitlements and limits stay at the current plan until that instant, and the worker job `billing.apply_scheduled` performs the change within 5 minutes of the period end; `apply: "immediate"` on a downgrade issues a credit note for the unused remainder instead of a refund and takes effect at once.
- **FR-F064-05:** After any subscription write the projector `plan_entitlements` upserts one F048 entitlement per module named by the plan catalog through the F048 service with `source: "plan"` — `free` grants no premium module, `team` grants `dynamic-views`, `calendar-app`, `pivots` with limits `{ max_views: 50, max_pivots: 20 }`, `enterprise` grants those plus `workapps`, `data-shuttle`, `datamesh`, `bridge`, `assets`, `ai-assist`, `ai-insights` with limits `{ max_views: 1000, max_pivots: 500, max_flows: 100 }`; an entitlement row whose `source` is `manual` is never overwritten and is returned in the billing UI as an operator override. F064 creates no entitlement table of its own and performs no gating decision.
- **FR-F064-06:** Every provider call goes through the port `PaymentProvider` in `crates/domain/src/billing/provider.rs` with methods `ensure_customer`, `change_subscription`, `preview_proration`, `create_portal_session`, `fetch_invoice`, `verify_webhook`, and `parse_event`, exchanging only domain types (`ProviderCustomerRef`, `ProviderSubscriptionRef`, `ProrationPreview`, `PortalSession`, `ProviderInvoice`, `WebhookEnvelope`); the single adapter `StripeAdapter` in `crates/domain/src/billing/adapters/stripe.rs` is the only file permitted to name provider JSON fields, and a compile gate keeps `stripe` out of every other billing path.
- **FR-F064-07:** `POST /api/v1/billing/portal-session` by a `billing-admin` returns `{ url, expires_at }` from `create_portal_session` with a return URL of `/admin/billing`, valid for 15 minutes, rate-limited to 5 sessions per tenant per hour with `429 rate_limited`; the URL is never logged and never stored.
- **FR-F064-08:** `POST /webhooks/billing/{provider}` is unauthenticated by session and authenticated by signature: the raw body plus the `t=<unix>` timestamp is verified with HMAC-SHA256 against the provider signing secret, a timestamp skew above 300 seconds or a bad signature returns `400 invalid` with no state change and an audit event, and an unknown `{provider}` path segment returns `404 not_found`.
- **FR-F064-09:** Webhook application is idempotent by construction: the handler calls `WebhookEventRepository::claim_event`, which inserts `billing_webhook_events(provider, provider_event_id)`, and applies the effect in the same `UnitOfWork` transaction, so a redelivered event hits the unique constraint, is answered `200` with `{ status: "duplicate" }`, and applies nothing; an event whose type is outside the handled set (`subscription.updated`, `invoice.finalized`, `invoice.paid`, `invoice.payment_failed`, `payment_method.updated`) is stored with `status: "ignored"` and answered `200`; an event whose `provider_subscription_id` matches no tenant is stored with `status: "ignored"` and never guessed at.
- **FR-F064-10:** Handled webhooks apply as follows: `invoice.finalized` upserts `invoices` and replaces that invoice's `invoice_lines` rows in the same transaction through `InvoiceRepository::upsert_from_provider`, then publishes `invoice.issued.v1`; `invoice.paid` sets `status: paid`, clears dunning, and restores `status: active` plus plan entitlements; `invoice.payment_failed` publishes `invoice.payment-failed.v1` and advances dunning per FR-F064-13; `subscription.updated` reconciles `plan`, period bounds, and `cancel_at_period_end` and publishes `subscription.updated.v1`; provider state always wins over local state on reconciliation and the difference is written to the audit trail.
- **FR-F064-11:** Three metrics are metered, and only three: `seats` (distinct `users` rows with `status: active` and at least one F003 role binding), `storage_gb` (sum of `file_versions.size_bytes` for non-deleted files from F017, divided by 2^30), and `automation_runs` (count of F019 `workflow_runs` rows reaching a terminal status). Rows, columns, sheets, views, and API calls are deliberately not metered: their counts churn continuously, so an invoice built on them could not be reproduced from history. `seats` and `storage_gb` are recorded as a daily `sample` at 00:05 UTC by the worker job `billing.meter`; `automation_runs` is recorded as an hourly `delta` aggregated from the F019 outbox stream.
- **FR-F064-12:** `usage_records` is append-only: a correction is a new row with `kind: "adjustment"`, a signed `quantity`, `corrects_record_id` pointing at the row being corrected, and a `reason` of 10–500 characters; the API and worker never `UPDATE` or `DELETE` a usage row, a database rule rejects both, and `GET /api/v1/billing/usage?metric=&from=&to=&granularity=day|month` returns the summed effective quantity with `adjustments_applied` and `as_of` from `UsageRecordRepository::sum_effective_quantity`; every recorded row publishes `usage.recorded.v1`. Usage above the plan allowance never blocks work; it is reported as `overage` on the invoice preview and in the usage view.
- **FR-F064-13:** Dunning is a fixed, notified ladder driven by `invoice.payment-failed.v1` and the daily job `billing.dunning`: day 0 sets `status: past_due` and notifies every `billing-admin` and `tenant-admin` through F037; retries are attempted on days 1, 3, 5, and 7; day 7 sets `status: restricted`, which suspends only the plan-sourced F048 entitlements so premium modules stop while core sheets stay read-write; day 14 sets `status: suspended`, which makes the tenant read-only except for export; day 30 sets `status: canceled` and moves the tenant to the `free` plan. Each transition notifies again and states the next step and its date. Billing never deletes tenant data and never removes read or export access before day 30; deletion is only ever the F027 retention path after an explicit tenant decision.
- **FR-F064-14:** A `trialing` subscription carries `trial_ends_at`; the job `billing.trial_expiry` notifies at 7, 3, and 1 days remaining; at expiry with a usable payment method the subscription becomes `active` and the first invoice is issued, and at expiry without one the plan falls back to `free` with `status: active` — a trial that ends never enters dunning, never suspends, and never restricts read access. `cancel_at_period_end: true` keeps full access until `current_period_end`, then moves the tenant to `free` and publishes `subscription.updated.v1`.
- **FR-F064-15:** `GET /api/v1/billing/invoices?status=&from=&to=&cursor=&limit=` returns `InvoiceResponse { id, number, status (draft|open|paid|uncollectible|void), currency, subtotal_cents, tax_cents, total_cents, amount_paid_cents, period_start, period_end, issued_at, due_at, paid_at, hosted_url, lines: [ { description, metric?, quantity, unit_amount_cents, amount_cents } ] }` newest first; the DTO keeps `lines` as a JSON array in provider line order, and `InvoiceRepository::list_with_lines` reads the `invoice_lines` rows for the page in one keyset-ordered query and reassembles the array by `line_no`, so the response body is byte-identical to the pre-normalization shape; `hosted_url` is fetched from the adapter on read and is never persisted; all billing routes require `billing-admin`, mutations write audit events, and any tenant id present in a body is rejected with `400 invalid` since the tenant comes from the gateway context.

- **FR-F064-19:** The plan-to-module mapping is `docs/packaging.md` section 2, which is the single definition of what a plan includes. On a plan change or renewal `entitlements_projection` writes exactly that set with `source: plan`, never touching a `manual` row, and the upgrade surface names what a tenant would gain by generating it from the same table rather than restating it. Removing a module from a plan grandfathers current holders as `manual` rather than downgrading them silently.
- **FR-F064-16:** A platform operator can `POST /api/v1/billing/credit-codes` with `{ amount_cents (1–1,000,000), currency, count (1–1,000), expires_at, note, restrictions?: { new_tenants_only?: bool, plans?: [..], tenant_id? } }` to mint one-time credit codes. The request and response keep `restrictions` as a JSON object with a `plans` array; `CreditCodeRepository` stores `new_tenants_only` and `restricted_tenant_id` as typed columns on `credit_codes` and fans `plans` out to one `credit_code_plans` row per plan, and reassembles the object on read, so the operator-facing contract does not change while redemption filters on rows instead of reading a `jsonb` key. Each code is 16 characters from an unambiguous alphabet (Crockford base32, no `I`, `L`, `O`, `U`) formatted `XXXX-XXXX-XXXX-XXXX`, generated from a CSPRNG, returned in the response exactly once, and stored only as a SHA-256 `code_hash` with a lookup index — the plaintext is never persisted, logged, audited, or recoverable, so a lost code is reissued, never retrieved. The call publishes `credit-code.issued.v1` with the batch id and count but no code material, and a `billing-admin` who is not a platform operator receives `403 denied`.
- **FR-F064-17:** `POST /api/v1/billing/credits/redeem` with `{ code }` by a `billing-admin` redeems exactly once. `CreditCodeRepository::claim_by_hash` looks the code up by hash in constant time and evaluates the restrictions against columns and `credit_code_plans` rows rather than a document; redemption is atomic: the conditional claim (`redeemed_at is null`) and the `CreditLedgerRepository` entry are written in one `UnitOfWork` transaction, so two concurrent redemptions of the same code produce exactly one success and one `409 conflict` with `reason: already_redeemed`. Distinct failures are distinguished — `invalid_code`, `expired`, `already_redeemed`, `not_applicable` (restrictions unmet) — but the response never reveals a code's value or existence beyond those codes, and redemption is rate-limited to 5 attempts per tenant per hour through the F038 bucket to make guessing the 16-character space useless. Success returns the new balance, writes an audit event with the code id and never the code, and publishes `credit.redeemed.v1`.
- **FR-F064-18:** Credit is an account balance, not a payment method. `credit_ledger` is append-only with signed `amount_cents` entries (`redemption`, `application`, `expiry`, `adjustment`) and the balance is their sum, never a stored mutable total. At invoice finalization the available balance is applied before the provider charges: a balance covering the invoice reduces the amount due to zero and marks it `paid_by_credit` without a provider charge, a partial balance reduces the due amount and the remainder is charged, and any unused balance carries forward. Credit is per tenant, non-transferable, never refundable to cash, and is not returned by cancellation; unused credit expires on the ledger entry's `expires_at` with an `expiry` entry and a notification 14 days before. Because credit settles the invoice, a tenant whose balance covers a failed payment leaves `past_due` on the next run and never enters the FR-F064-13 dunning ladder. `GET /api/v1/billing/credits` returns the balance from `CreditLedgerRepository::balance_for_tenant`, the ledger with cursor paging, and each entry's source and expiry.

### Non-functional requirements

- **NFR-F064-01 Performance:** `GET /api/v1/billing/subscription` under 300 ms p95 and `GET /api/v1/billing/invoices` with `limit=50` under 500 ms p95; a usage query over 13 months of daily records for three metrics under 800 ms p95; the daily meter job covers 10,000 tenants in under 10 minutes; webhook handling returns within 2 s p95 excluding adapter latency so the provider never times out.
- **NFR-F064-02 Security/privacy:** credit codes are CSPRNG-generated, stored only as SHA-256 hashes, compared in constant time, rate-limited per tenant, and never written to a log, audit diff, export, or error message; no card data, PAN, CVC, or provider secret key ever enters OpsHub — only the provider brand, last four digits, and expiry are stored, and payment capture happens exclusively in the provider-hosted portal; webhook signing secrets live in the F004 secret manager under `billing/<provider>/signing_secret` with a two-secret rotation window; portal URLs and raw webhook bodies are excluded from logs and from the F027 export; `billing-admin` is required on every route and cross-tenant ids return `not_found`.
- **NFR-F064-03 Accessibility:** `/admin/billing` and its plan-change, cancel, and correction dialogs pass axe with zero serious or critical violations; the proration preview is a described table rather than a color-coded figure; subscription and dunning status is conveyed by text plus a labelled icon, never color alone; the dunning banner is a polite live region that states the stage, the consequence, and the date of the next step.
- **NFR-F064-04 Reliability/observability:** every webhook is replay-safe by the `(provider, provider_event_id)` unique constraint, every meter run is idempotent by `(tenant_id, metric, period_date, kind, source_ref)`, and both are resumable after a restart; a webhook whose application fails is stored with `status: "failed"`, retried 5 times with exponential backoff, then dead-lettered with an operator alert; metrics `billing_webhook_events_total{provider,type,status}`, `billing_dunning_stage_total{stage}`, `usage_records_written_total{metric,kind}`, and `billing_provider_call_duration_seconds{operation}` are exported, and every provider call carries a tracing span with `tenant_id` and `operation`.

### Scope

Included: the subscription record and its lifecycle, the plan catalog and its projection into F048 entitlement records, proration preview and application, scheduled downgrades, trial expiry, cancellation with end-of-period grace, the payment provider port and its single Stripe-shaped adapter, hosted portal sessions, signed and replay-protected webhooks, invoice storage and listing, three metered usage metrics with append-only corrections, the dunning ladder with notifications and staged degradation, and the `/admin/billing` surface.

Excluded: entitlement evaluation, feature-flag lifecycle, and the `RequireModule` guard (F048 owns all of it, and F064 only writes plan-sourced records); tenant, user, and group state including the `tenants.plan` column itself (F002); public signup, email verification, anti-abuse, and trial provisioning (F065); notification channels and delivery (F037); tax determination and remittance, dunning email copy authoring, revenue recognition, multi-currency price books, resellers, purchase orders, and offline invoicing (all out of this release); data retention, legal hold, and purge (F027).

## 3. UX specification

- Entry points: admin navigation `Billing`; routes `/admin/billing`, `/admin/billing/invoices`, `/admin/billing/usage`; a dunning banner in the app shell for `past_due`, `restricted`, and `suspended`.
- Primary flow: a billing administrator opens `/admin/billing`, sees `Team · active · renews 1 October`, clicks `Change plan`, selects `Enterprise`, and reads the preview — `Credit 42.10, charge 190.55, due today 148.45, next invoice 1 October` — before confirming; after confirming, the plan card updates and the entitlements panel shows the modules that just unlocked.
- Downgrade flow: selecting `Team` from `Enterprise` shows `Takes effect 1 October — you keep Bridge, WorkApps, DataMesh, Data Shuttle, and assets until then`, with a secondary `Switch now and receive a credit note` action behind a confirmation naming the modules that stop today.
- Usage view: three cards (`Seats`, `Storage`, `Automation runs`) with the current period total, the plan allowance, a percentage bar with a numeric label, and a daily table; a corrected day shows the original value struck through, the adjustment, the reason, and the actor.
- Dunning banner: `past_due` is a warning stating the failed invoice, the next retry date, and what happens on day 7; `restricted` lists the modules paused and states that sheets remain editable; `suspended` states that the tenant is read-only, that export still works, and the date data access would end without action; every stage links to the hosted portal.
- Loading, empty, error, denied, success: card skeletons; a tenant on `free` sees an upgrade card naming what each plan unlocks; provider failures show a banner with `correlation_id`, a retry, and the assurance that nothing was charged; non-`billing-admin` actors see the denied page; plan changes, portal hand-off, and corrections raise toasts.
- Responsive and keyboard: plan cards stack under 768 px and the invoice table collapses to a definition list; the plan-change dialog traps focus, the preview is announced when it loads, and confirmation requires an explicit button rather than an on-change commit; `prefers-reduced-motion` disables the usage bar animation.
- Font, icon, and design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide icons `CreditCard`, `ReceiptText`, `Gauge`, `TrendingUp`, `AlertTriangle`, `ExternalLink`; tokens from `apps/web/src/design/tokens.css`.

- Design: `design/artboards/Billing.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

### Rust backend

- Data access (decision section 2.1): `crates/persistence/src/billing/` holds `SubscriptionRepository` (owns `subscriptions`, `subscription_payment_methods`), `InvoiceRepository` (owns `invoices`, `invoice_lines`), `UsageRecordRepository` (owns `usage_records` and its partitions), `WebhookEventRepository` (owns `billing_webhook_events`), `CreditCodeRepository` (owns `credit_codes`, `credit_code_plans`), and `CreditLedgerRepository` (owns `credit_ledger`). Each child table is owned by the repository of its parent object type, so no two classes write the same table. Named queries beyond the shared `Repository` contract: `find_by_tenant`, `save_payment_method`, `clear_payment_method`, `list_due_scheduled_changes`, `list_due_dunning_actions`, `set_dunning_stage`, `upsert_from_provider` (invoice header plus `replace_lines` in one statement pair), `list_with_lines`, `append_sample`, `append_delta`, `append_adjustment`, `sum_effective_quantity`, `list_daily_usage`, `claim_event` (insert of `(provider, provider_event_id)` that returns the duplicate rather than raising), `mark_event_applied`, `mark_event_ignored`, `mark_event_failed`, `list_failed_events_for_retry`, `strip_expired_payloads`, `insert_code_batch`, `claim_by_hash`, `list_plan_restrictions`, `append_ledger_entry`, `balance_for_tenant`, `list_ledger_entries`, `list_credit_expiring_before`. There is no generic query method on any of them. The use cases below depend on these traits and contain no SQL: `services/api/src/billing/` handlers, the `services/worker/src/billing/` jobs, `crates/domain/src/billing/` services, and the `testing/features/F064/` fixtures all reach PostgreSQL only through them. Multi-table writes run in one `UnitOfWork`: a plan change writes `subscriptions` plus its payment-method row and the audit and outbox rows together; a webhook application claims the event, upserts the invoice with its lines, and applies credit in one transaction; a redemption claims the code and appends the ledger entry in one transaction.
- Domain entities in `crates/domain/src/billing/`: `Subscription { id, tenant_id, plan: Plan (Free|Team|Enterprise), status: SubscriptionStatus (Trialing|Active|PastDue|Restricted|Suspended|Canceled), provider: ProviderId (Stripe), provider_customer_id, provider_subscription_id, current_period_start, current_period_end, cancel_at_period_end, trial_ends_at, scheduled_plan, scheduled_effective_at, dunning: DunningState { stage: u8, entered_at, next_action_at, retries_remaining }, payment_method: Option<PaymentMethodSummary { brand, last4, exp_month, exp_year }>, version, audit fields }`, `PlanCatalog { plan, unit_price_cents, currency, allowances: Allowances { seats, storage_gb, automation_runs }, modules: Vec<(ModuleSlug, Limits)> }` as a compiled-in table, `Invoice`, `InvoiceLine`, `UsageRecord { id, tenant_id, metric: Metric (Seats|StorageGb|AutomationRuns), quantity: Decimal, unit, kind: RecordKind (Sample|Delta|Adjustment), period_date, source_ref, corrects_record_id, reason, recorded_at }`, `WebhookEvent { provider, provider_event_id, event_type, signature_ts, status: WebhookStatus (Applied|Duplicate|Ignored|Failed), payload, received_at, applied_at, attempts, error }`.
- Use cases in `service.rs`, `lifecycle.rs`, `metering.rs`, `dunning.rs`, `webhook.rs`: `get_subscription`, `preview_change`, `change_plan`, `apply_scheduled_change`, `open_portal_session`, `record_usage`, `correct_usage`, `query_usage`, `list_invoices`, `ingest_webhook`, `advance_dunning`, `expire_trial`, `project_plan_entitlements`.
- Proration in `proration.rs` is pure and provider-independent: `proration(old_price, new_price, period_start, period_end, at) -> ProrationPreview` with half-up rounding to the minor unit and a zero net when the plans are equal; the adapter's returned line items are compared against it and a mismatch raises `BillingError::ProviderMismatch`.
- Entitlement projection in `entitlements_projection.rs` calls the F048 service `upsert_entitlement(module, state, limits, source: Plan)` and skips any module whose stored `source` is `manual`; F064 depends on the F048 crate interface and never reads or writes the `entitlements` table directly.
- API endpoints in `services/api/src/billing/`: `GET /api/v1/billing/subscription`, `PUT /api/v1/billing/subscription`, `GET /api/v1/billing/usage`, `GET /api/v1/billing/invoices`, `POST /api/v1/billing/portal-session`, `POST /webhooks/billing/{provider}`. DTOs: `SubscriptionResponse`, `ChangeSubscriptionRequest`, `ProrationPreviewResponse`, `UsageQuery`, `UsageResponse`, `InvoiceResponse`, `Page<InvoiceResponse>`, `PortalSessionResponse`, `WebhookAck { status }`.
- Worker jobs in `services/worker/src/billing/`: `meter.rs` (daily 00:05 UTC samples plus hourly automation-run deltas), `dunning.rs` (daily ladder advance), `scheduled.rs` (`billing.apply_scheduled` every 5 minutes), `trial.rs` (`billing.trial_expiry` daily), `webhook_retry.rs` (failed-event backoff and dead-letter).
- Events: `subscription.updated.v1` with `changed_fields` covering `plan`, `status`, `dunning.stage`, and `cancel_at_period_end`; `invoice.issued.v1`; `invoice.payment-failed.v1` with `attempt` and `next_retry_at`; `usage.recorded.v1` with `metric`, `kind`, `period_date`, and `quantity`.
- Authorization: `billing-admin` on every `/api/v1/billing` route; the webhook route is exempt from session auth and authenticated by signature alone, with the tenant resolved from `provider_customer_id`; cross-tenant ids return `not_found`.
- Validation: `plan` in the F002 set; `apply` in `immediate|period_end`; `reason` 10–500 characters; `from` before `to` and a range of at most 400 days; `limit` 1–100; webhook body at most 512 KB.
- Error mapping: `BillingError::PlanUnknown → 400 invalid`, `::PaymentMethodRequired → 409 conflict`, `::StaleVersion → 409 conflict`, `::ProviderMismatch → 502 unavailable`, `::ProviderUnavailable → 502 unavailable`, `::SignatureInvalid → 400 invalid`, `::PortalRateLimited → 429 rate_limited`, `::NotFound → 404 not_found`, `AuthzError::Denied → 403 denied`.

### Interface

Exact shapes. Every field lists its JSON name, type, whether it is required, and the constraint whose
violation produces the stated error. `T?` is nullable; an absent optional field and an explicit
`null` mean the same thing. Ids are UUIDv7 strings, timestamps are RFC 3339 UTC, `version` increments
by one per write. Money is always an integer **minor unit** field named `*_cents` — never a float and
never a formatted string — paired with an ISO 4217 `currency`. Unlisted request fields are rejected
with `400 invalid`, and a `tenant_id` in **any** body is rejected that way too: the tenant comes from
the gateway context and never from the caller. `Page<T>`, `ListQuery`, the signed cursor, the error
body and the six codes are F028's; `ActorContext` is F038's; the entitlement record and its `source`
field are F048's and this feature only calls F048's `upsert_entitlement`.

**`Allowances`**: `{ seats: integer, storage_gb: integer, automation_runs: integer }` — the plan's
included amounts, from the compiled-in `PlanCatalog`. Exceeding one never blocks work; it becomes an
`overage` line (FR-F064-12).

**`PaymentMethodSummary`**: `{ brand: string, last4: string (4 digits), exp_month: integer 1–12,
exp_year: integer }`. This is the whole of what OpsHub stores about a card. There is no field on any
request or response in this module that could carry a PAN, a CVC, a token or a provider secret key;
capture happens only in the provider-hosted portal.

**`DunningState`**: `{ stage: integer 0–30, entered_at: timestamp?, next_action_at: timestamp?,
retries_remaining: integer }`. `stage` is the day number of the FR-F064-13 ladder, so `0` means not
in dunning.

**`SubscriptionResponse`** — `GET` and `PUT /api/v1/billing/subscription`

| Field | Type | Notes |
|---|---|---|
| `plan` | `"free" \| "team" \| "enterprise"` | the FR-F002-02 set; F002 owns `tenants.plan` and this is the record that drives it |
| `status` | `"trialing" \| "active" \| "past_due" \| "restricted" \| "suspended" \| "canceled"` | |
| `provider` | `"stripe"` | the adapter in use; a client never branches on it |
| `current_period_start` / `current_period_end` | timestamp? | `null` on the synthetic free subscription |
| `cancel_at_period_end` | bool | |
| `trial_ends_at` | timestamp? | non-null only while `status` is `trialing` |
| `scheduled_plan` | `"free" \| "team" \| "enterprise"`? | a downgrade already agreed; `null` when none |
| `scheduled_effective_at` | timestamp? | present exactly when `scheduled_plan` is |
| `dunning` | DunningState | always present; `stage: 0` when healthy |
| `seats` | `{ included: integer, in_use: integer }` | `in_use` is the live count, not the last meter sample |
| `allowances` | Allowances | |
| `payment_method` | PaymentMethodSummary? | `null` means no `subscription_payment_methods` row exists — the row is deleted, never blanked |
| `credit_balance_cents` | integer | the sum of `credit_ledger`, so the plan card can show what a future invoice will absorb |
| `version` | integer | pass as `If-Match` on the next write. **`0`** on the synthetic free subscription of a tenant with no row, which is returned with `200`, never `404` (FR-F064-01) |

**`ChangeSubscriptionRequest`** — `PUT /api/v1/billing/subscription`, `If-Match` and
`Idempotency-Key` required

| Field | Type | Required | Constraint |
|---|---|---|---|
| `plan` | `"free" \| "team" \| "enterprise"` | yes | outside the set → `400 invalid` with `field_errors.plan`. `enterprise` with no stored payment method → `409 conflict` with `field_errors.payment_method = "required"` |
| `apply` | `"immediate" \| "period_end"` | no | defaults `"immediate"` for an upgrade and `"period_end"` for a downgrade; `"period_end"` on an upgrade is accepted and simply schedules it |
| `cancel_at_period_end` | bool | no | may be sent with an unchanged `plan` to cancel or un-cancel |
| `preview` | bool | no | default `false`. `true` returns `ProrationPreviewResponse` and **writes nothing** — no subscription row, no provider call that changes state, no audit row, no event |

**`ProrationPreviewResponse`**: `{ credit_cents, charge_cents, net_cents, currency, effective_at,
next_invoice_at, credit_applied_cents, amount_due_cents }`. `net_cents = charge_cents -
credit_cents` and may be negative on a downgrade, where it becomes a credit note rather than a
refund. `credit_applied_cents` is how much of the tenant's ledger balance would settle it, and
`amount_due_cents = max(0, net_cents - credit_applied_cents)`. The adapter's line items must match
`credit_cents`, `charge_cents` and `net_cents` **to the cent**; a mismatch is `502 unavailable` and
nothing is written locally (FR-F064-03).

**`UsageQuery`** — `GET /api/v1/billing/usage`

| Field | Type | Required | Constraint |
|---|---|---|---|
| `metric` | `"seats" \| "storage_gb" \| "automation_runs"` | yes | the only three metered metrics |
| `from` / `to` | date | yes | `from < to`, range ≤ 400 days, else `400 invalid` |
| `granularity` | `"day" \| "month"` | no | default `"day"` |

**`UsageResponse`**: `{ metric, unit: "count" | "gigabyte", granularity, allowance: integer,
as_of: timestamp, adjustments_applied: integer, buckets: [{ period, quantity: decimal-string,
overage: decimal-string }] }`. `quantity` is a decimal **string**, not a JSON number, because
`numeric(20,4)` does not round-trip through a double. `overage` is `max(0, quantity - allowance)` and
is informational: usage above allowance never blocks work.

**`InvoiceLine`**: `{ line_no: integer, description: string, metric: string?, quantity:
decimal-string, unit_amount_cents: integer, amount_cents: integer }`. `line_no` starts at 1 and is
contiguous; the array is in `line_no` order and `sum(amount_cents)` equals the invoice
`subtotal_cents`.

**`InvoiceResponse`**: `{ id, number: string?, status: "draft" | "open" | "paid" | "uncollectible" |
"void", currency, subtotal_cents, tax_cents, total_cents, amount_paid_cents, credit_applied_cents,
period_start, period_end, issued_at, due_at, paid_at, hosted_url: string?, lines: InvoiceLine[] }`.
`hosted_url` is fetched from the adapter on read, never persisted, and is `null` when the adapter is
unreachable — a failed URL fetch degrades one field, it does not fail the list.

**`PortalSessionResponse`** — `POST /api/v1/billing/portal-session`: `{ url, expires_at }`. `url` is
valid 15 minutes, is never logged and never stored; a second call before expiry mints a new session
rather than returning the old one. Rate-limited to 5 per tenant per hour.

**Webhook** — `POST /webhooks/billing/{provider}`. Unauthenticated by session and authenticated by
signature: the **raw** body plus the `t=<unix>` element of the signature header is verified with
HMAC-SHA256 against the current or previous signing secret. The body is the provider's own JSON and
this feature defines no schema for it — only the adapter names its fields. Response is always
`WebhookAck { status: "applied" | "duplicate" | "ignored" }` with `200`, so a redelivery, an
unhandled event type and an event for an unknown customer are all acknowledged rather than retried
forever. An unknown `{provider}` path segment is `404 not_found`; a bad signature or a timestamp skew
over 300 s is `400 invalid` with no state change and an audit row.

**`CreateCreditCodesRequest`** — `POST /api/v1/billing/credit-codes`, platform operator only

| Field | Type | Required | Constraint |
|---|---|---|---|
| `amount_cents` | integer | yes | 1–1,000,000 |
| `currency` | string | yes | ISO 4217 alpha-3, uppercase |
| `count` | integer | yes | 1–1,000 codes in the batch |
| `expires_at` | timestamp | yes | in the future |
| `note` | string? | no | ≤ 500 chars, operator-facing |
| `restrictions` | `{ new_tenants_only?: bool, plans?: string[], tenant_id?: uuid }`? | no | `plans` entries from the F002 plan set, distinct; stored as `credit_code_plans` rows, the other two as typed columns |

**`CreateCreditCodesResponse`**

| Field | Type | Notes |
|---|---|---|
| `batch_id` | uuid | |
| `count` | integer | |
| `amount_cents` / `currency` / `expires_at` | as the request | |
| `codes` | string[] | The plaintext codes, formatted `XXXX-XXXX-XXXX-XXXX` in Crockford base32 without `I`, `L`, `O`, `U`. **Returned exactly once, in this response, and nowhere else, ever.** Only the SHA-256 `code_hash` is stored; there is no column, log line, audit diff, export, event payload or later route that holds or can reproduce the plaintext. A lost code is reissued as a new code, never retrieved — `GET`ting the batch is not a route, and `credit-code.issued.v1` carries the batch id and count and no code material (FR-F064-16) |

**`RedeemCreditRequest`** — `POST /api/v1/billing/credits/redeem`: `{ code: string }`, the formatted
16-character value with dashes optional and case-insensitive. **`RedeemCreditResponse`**:
`{ credit_id, amount_cents, currency, expires_at, balance_cents }`. Failures are distinguished by
`field_errors.code`: `invalid_code`, `expired`, `already_redeemed`, `not_applicable`. The response
never confirms a code's existence or value beyond those four reasons, the hash lookup is
constant-time, and attempts are limited to 5 per tenant per hour, which is what makes guessing the
16-character space pointless (FR-F064-17).

**`CreditLedgerEntry`**: `{ id, kind: "redemption" | "application" | "expiry" | "adjustment",
amount_cents: integer (signed), currency, credit_code_id: uuid?, invoice_id: uuid?, expires_at:
timestamp?, reason: string?, created_at, created_by: uuid? }`. **`GET /api/v1/billing/credits`**
returns `{ balance_cents, currency, entries: Page<CreditLedgerEntry> }` sorted `created_at`
descending with `id` as tiebreak. `balance_cents` is the sum of the entries, never a stored column.

**List route.** `GET /api/v1/billing/invoices` takes F028's `ListQuery` with `limit` capped at 100
and returns `Page<InvoiceResponse>`; sort key `issued_at` descending with `id` as tiebreak — the only
accepted sort. Filters: `status` (enum), `from` / `to` (date, against `issued_at`).

**Status codes**

| Status | `code` | Produced by |
|---|---|---|
| `400` | `invalid` | an unknown `plan`, `apply` or `metric`, `from >= to` or a range over 400 days, `amount_cents` or `count` out of range, a `reason` outside 10–500 chars, a bad webhook signature or a timestamp skew over 300 s, a body carrying `tenant_id`, an unlisted field |
| `403` | `denied` | any `/api/v1/billing` route without `billing-admin` — including a `tenant-admin` who lacks it; `POST /billing/credit-codes` by a `billing-admin` who is not a platform operator |
| `404` | `not_found` | an invoice or credit id of another tenant; an unknown `{provider}` segment. `GET /billing/subscription` never answers `404` — a tenant with no row gets the synthetic free subscription |
| `409` | `conflict` | stale `If-Match`; `enterprise` without a payment method (`field_errors.payment_method`); a credit code already redeemed; `Idempotency-Key` replayed with a different body |
| `429` | `rate_limited` | a 6th portal session per tenant per hour, or a 6th redemption attempt per tenant per hour; carries `Retry-After` |
| `502` | `unavailable` | the provider is unreachable or timed out, or its line items disagree with `proration.rs` to the cent. Nothing is written locally and nothing was charged — the message says so, because a client must be able to retry without fearing a double charge |

### Use case signatures

In `crates/domain/src/billing/`. Each takes `ctx: &Ctx` carrying tenant, actor and correlation id,
depends on repository traits and the `PaymentProvider` port rather than a pool, connection or HTTP
client, and returns `DomainError`.

```rust
fn get_subscription(ctx: &Ctx, repo: &dyn SubscriptionRepository, credits: &dyn CreditLedgerRepository) -> Result<SubscriptionView, DomainError>;
fn preview_change(ctx: &Ctx, repo: &dyn SubscriptionRepository, provider: &dyn PaymentProvider, req: ChangePlan) -> Result<ProrationPreview, DomainError>;
fn change_plan(ctx: &Ctx, uow: &mut UnitOfWork, provider: &dyn PaymentProvider, entitlements: &dyn EntitlementService, expected: Version, req: ChangePlan) -> Result<Subscription, DomainError>;
fn apply_scheduled_change(ctx: &Ctx, uow: &mut UnitOfWork, entitlements: &dyn EntitlementService, id: SubscriptionId) -> Result<Subscription, DomainError>;
fn open_portal_session(ctx: &Ctx, provider: &dyn PaymentProvider, limiter: &dyn RateLimiter) -> Result<PortalSession, DomainError>;
fn record_usage(ctx: &Ctx, uow: &mut UnitOfWork, metric: Metric, kind: RecordKind, quantity: Decimal, period: civil::Date, source_ref: &str) -> Result<UsageRecord, DomainError>;
fn correct_usage(ctx: &Ctx, uow: &mut UnitOfWork, corrects: UsageRecordId, delta: Decimal, reason: &str) -> Result<UsageRecord, DomainError>;
fn query_usage(ctx: &Ctx, repo: &dyn UsageRecordRepository, q: UsageQuery) -> Result<UsageView, DomainError>;
fn list_invoices(ctx: &Ctx, repo: &dyn InvoiceRepository, provider: &dyn PaymentProvider, filter: InvoiceFilter, page: Cursor) -> Result<Page<Invoice>, DomainError>;
fn ingest_webhook(ctx: &Ctx, uow: &mut UnitOfWork, provider: &dyn PaymentProvider, raw: &[u8], signature: &str, now: Timestamp) -> Result<WebhookAck, DomainError>;
fn advance_dunning(ctx: &Ctx, uow: &mut UnitOfWork, entitlements: &dyn EntitlementService, notify: &dyn NotificationService, now: Timestamp) -> Result<usize, DomainError>;
fn expire_trial(ctx: &Ctx, uow: &mut UnitOfWork, entitlements: &dyn EntitlementService, id: SubscriptionId, now: Timestamp) -> Result<Subscription, DomainError>;
fn issue_credit_codes(ctx: &Ctx, uow: &mut UnitOfWork, req: MintCodes) -> Result<(BatchId, Vec<PlaintextCode>), DomainError>;
fn redeem_credit(ctx: &Ctx, uow: &mut UnitOfWork, limiter: &dyn RateLimiter, code: &str) -> Result<CreditLedgerEntry, DomainError>;
fn apply_credit_to_invoice(ctx: &Ctx, uow: &mut UnitOfWork, invoice: InvoiceId) -> Result<AppliedCredit, DomainError>;
fn project_plan_entitlements(ctx: &Ctx, entitlements: &dyn EntitlementService, plan: Plan) -> Result<(), DomainError>;

fn proration(old_price: Cents, new_price: Cents, period_start: Timestamp, period_end: Timestamp, at: Timestamp) -> ProrationPreview;
fn effective_quantity(records: &[UsageRecord]) -> Decimal;
fn next_dunning_step(stage: u8, entered_at: Timestamp, now: Timestamp) -> Option<DunningStep>;
```

`proration`, `effective_quantity` and `next_dunning_step` are pure — no `ctx`, no repository, no
provider, no clock beyond their arguments. `proration` being pure is exactly what makes FR-F064-03's
cent-for-cent comparison against the adapter possible: the two are computed independently and a
disagreement is a rejection, not a silent acceptance of whatever the provider said.
`issue_credit_codes` returns `Vec<PlaintextCode>` only so the handler can serialise it once; it is a
transient type with no `Serialize` on any stored struct and no `Display` that could reach a log.

**Transaction boundaries.**

- `change_plan` calls the provider **first**, outside any transaction, then writes the
  `subscriptions` row, its `subscription_payment_methods` row, the audit row and the
  `subscription.updated.v1` outbox entry in one `UnitOfWork`, and calls F048's `upsert_entitlement`
  inside that same unit. Order matters both ways: a transaction is never held open across a provider
  round trip, and the entitlement projection commits with the plan that justifies it, so a tenant is
  never charged for `enterprise` while F048 still says `team`. The projection skips any row whose
  `source` is `manual` — F064 owns no entitlement table and this call is its only write into one.
- `ingest_webhook` claims the event and applies its effect in **one** `UnitOfWork`:
  `WebhookEventRepository::claim_event` inserts `(provider, provider_event_id)`, and the invoice
  upsert with its replaced `invoice_lines`, the dunning transition, the entitlement change and the
  outbox entry ride the same transaction. The invariant this protects is idempotency by
  construction: a redelivery collides with the unique constraint *inside* the transaction that would
  otherwise apply the effect, so the effect cannot happen twice — no application-level "have I seen
  this?" check exists to be raced.
- `redeem_credit` performs the conditional claim (`update credit_codes set redeemed_at = now() where
  code_hash = $1 and redeemed_at is null`) and appends the `credit_ledger` entry in one
  `UnitOfWork`. The zero-row result of that update *is* the `already_redeemed` answer, so two
  concurrent redemptions of one code produce exactly one success and one `409`, without a lock the
  application has to remember to take.
- `apply_credit_to_invoice` appends the negative `application` ledger entry and updates the invoice's
  `credit_applied_cents` and `status` in one `UnitOfWork` at finalization, before any provider
  charge. The invariant: the balance is the sum of the ledger, so an application that committed
  without its invoice would make the balance disagree with what was actually settled.
- `record_usage` and `correct_usage` each write one append-only row plus the `usage.recorded.v1`
  entry in one `UnitOfWork`; there is no update path at all, and the database rules reject one, so
  the boundary here protects the *event*, not the row — a usage row must never be visible without its
  event, or an invoice rebuilt from the stream would disagree with the table.
- `advance_dunning` commits one `UnitOfWork` per tenant: the stage change, the entitlement
  suspension, the audit row and the F037 notification enlist together, so a tenant is never
  restricted without having been told.
- `get_subscription`, `preview_change`, `query_usage` and `list_invoices` are reads and take
  repositories, not a `UnitOfWork`. `preview_change` in particular takes no `UnitOfWork` at all,
  which is the enforcement of "`preview: true` writes nothing" — the code path has no transaction to
  write in.

### PostgreSQL/SQLx

- Migration `*_billing_*.sql` creates `subscriptions(id uuid pk, tenant_id uuid not null unique references tenants(id) on delete restrict, plan text not null default 'free' check (plan in ('free','team','enterprise')), status text not null default 'active' check (status in ('trialing','active','past_due','restricted','suspended','canceled')), provider text not null default 'stripe' check (provider in ('stripe')), provider_customer_id text, provider_subscription_id text, current_period_start timestamptz, current_period_end timestamptz, cancel_at_period_end boolean not null default false, trial_ends_at timestamptz, scheduled_plan text check (scheduled_plan is null or scheduled_plan in ('free','team','enterprise')), scheduled_effective_at timestamptz, dunning_stage smallint not null default 0, dunning_entered_at timestamptz, dunning_next_action_at timestamptz, version bigint not null default 1, created_by uuid references users(id) on delete restrict, created_at, updated_by uuid references users(id) on delete restrict, updated_at)`, `invoices(id uuid pk, tenant_id uuid not null references tenants(id) on delete restrict, provider_invoice_id text not null, number text, status text not null check (status in ('draft','open','paid','uncollectible','void')), currency char(3) not null, subtotal_cents bigint not null, tax_cents bigint not null default 0, total_cents bigint not null, amount_paid_cents bigint not null default 0, period_start timestamptz, period_end timestamptz, issued_at timestamptz, due_at timestamptz, paid_at timestamptz, attempt_count int not null default 0, created_at)`, `usage_records(id uuid pk, tenant_id uuid not null references tenants(id) on delete restrict, metric text not null check (metric in ('seats','storage_gb','automation_runs')), quantity numeric(20,4) not null, unit text not null check (unit in ('count','gigabyte')), kind text not null check (kind in ('sample','delta','adjustment')), period_date date not null, source_ref text not null, corrects_record_id uuid references usage_records(id) on delete restrict, reason text, recorded_by uuid references users(id) on delete restrict, recorded_at timestamptz not null default now())`, `billing_webhook_events(id uuid pk, provider text not null check (provider in ('stripe')), provider_event_id text not null, tenant_id uuid references tenants(id) on delete restrict, event_type text not null, signature_ts timestamptz not null, status text not null check (status in ('applied','duplicate','ignored','failed')), payload jsonb not null, attempts smallint not null default 0, error text, received_at timestamptz not null default now(), applied_at timestamptz)` — `event_type` stays an unconstrained `text` because the provider owns that vocabulary and an unrecognized value is stored `ignored` rather than rejected (FR-F064-09). Credit codes add `credit_codes(id uuid pk, batch_id uuid not null, code_hash bytea not null unique, amount_cents int not null check (amount_cents between 1 and 1000000), currency char(3) not null, expires_at timestamptz not null, new_tenants_only boolean not null default false, restricted_tenant_id uuid references tenants(id) on delete restrict, issued_by uuid not null references users(id) on delete restrict, issued_at timestamptz not null, redeemed_at timestamptz, redeemed_by_tenant_id uuid references tenants(id) on delete restrict, redeemed_by uuid references users(id) on delete restrict, note text, check ((redeemed_at is null) = (redeemed_by_tenant_id is null)))` and `credit_ledger(id uuid pk, tenant_id uuid not null references tenants(id) on delete restrict, kind text not null check (kind in ('redemption','application','expiry','adjustment')), amount_cents int not null, currency char(3) not null, credit_code_id uuid references credit_codes(id) on delete restrict, invoice_id uuid references invoices(id) on delete restrict, expires_at timestamptz, reason text, created_by uuid references users(id) on delete restrict, created_at timestamptz not null)`; the plaintext code has no column anywhere.
- Normalized sets (decision section 2, no array or document-shaped columns): `invoice_lines(invoice_id uuid not null references invoices(id) on delete cascade, tenant_id uuid not null references tenants(id) on delete restrict, line_no smallint not null, description text not null, metric text check (metric is null or metric in ('seats','storage_gb','automation_runs')), quantity numeric(20,4) not null, unit_amount_cents bigint not null, amount_cents bigint not null, primary key (invoice_id, line_no))` replaces `invoices.lines jsonb`, which the invoice DTO read by key and the reconciliation test in section 9 sums per metric; `subscription_payment_methods(subscription_id uuid primary key references subscriptions(id) on delete cascade, tenant_id uuid not null references tenants(id) on delete restrict, brand text not null, last4 char(4) not null check (last4 ~ '^[0-9]{4}$'), exp_month smallint not null check (exp_month between 1 and 12), exp_year smallint not null check (exp_year between 2020 and 2100), updated_at timestamptz not null)` replaces `subscriptions.payment_method jsonb`, whose four keys the API returns and whose presence FR-F064-02 and FR-F064-14 branch on (`enterprise` requires a method; a trial converts only with one), so the product constrains it and it cannot stay a document; `credit_code_plans(credit_code_id uuid not null references credit_codes(id) on delete cascade, plan text not null check (plan in ('free','team','enterprise')), primary key (credit_code_id, plan))` replaces the `plans` list inside `credit_codes.restrictions jsonb`, and the other two restriction keys become the typed `new_tenants_only` and `restricted_tenant_id` columns above, so redemption filters on rows and columns instead of reading `jsonb` keys. All three children cascade because a line, a payment-method summary, and a code restriction cannot outlive their parent row. The `SubscriptionResponse.payment_method` object, the `InvoiceResponse.lines` array, and the credit-code `restrictions` object keep their JSON shapes on the wire; `SubscriptionRepository`, `InvoiceRepository`, and `CreditCodeRepository` fan them out to rows on write and reassemble them on read, so no externally visible behaviour changes. The plan catalog stays a compiled-in `PlanCatalog` table in `crates/domain/src/billing/plan.rs` and has no database column at all, so its module list introduces no array.
- `jsonb` audit: `billing_webhook_events.payload` is the only `jsonb` column left in the module and stays one — it is the verbatim provider event body kept for signature re-verification, replay, and support, and the product never filters, joins, sorts, aggregates, or constrains on its contents; every query uses `provider`, `provider_event_id`, `event_type`, `status`, and `received_at`, and the adapter parses the body into domain types before any decision is made, so the payload is a snapshot and not a queried structure (decision section 2). `subscriptions.payment_method`, `invoices.lines`, and `credit_codes.restrictions` were all read by known key or summed and are now the three tables above; no `jsonb` column remains that the product reads by key.
- Invariants: `subscriptions(tenant_id)` unique so one tenant has at most one subscription; at most one `subscription_payment_methods` row per subscription by its primary key, and the row is deleted rather than blanked when the provider reports the method removed, so `payment_method: null` in FR-F064-01 means no row; `invoice_lines(invoice_id, line_no)` is the natural key, `line_no` starts at 1 and is contiguous per invoice, and `sum(amount_cents) = invoices.subtotal_cents` is asserted by `InvoiceRepository::upsert_from_provider` before commit and by the reconciliation test; `credit_code_plans` primary key blocks a duplicate plan restriction on one code and its `check` keeps the plan values inside the FR-F002-02 set; `check (plan in ('free','team','enterprise'))` matching FR-F002-02; `check (status in ('trialing','active','past_due','restricted','suspended','canceled'))`; `check (dunning_stage between 0 and 30)`; `check (trial_ends_at is null or status <> 'suspended')`; `invoices(provider_invoice_id)` unique; `billing_webhook_events(provider, provider_event_id)` unique — the replay guard; `usage_records` `check (kind in ('sample','delta','adjustment'))`, `check (kind <> 'adjustment' or (corrects_record_id is not null and char_length(reason) between 10 and 500))`, `check (kind = 'adjustment' or quantity >= 0)`, unique `(tenant_id, metric, period_date, kind, source_ref)`, and rules `usage_records_no_update` and `usage_records_no_delete` that raise an exception, making the table append-only in the database and not only in application code. `credit_codes(code_hash)` unique is the redemption lookup and the single-use claim is `update ... where redeemed_at is null`; `credit_ledger` rejects update and delete by rule as `usage_records` does, so the balance is only ever the sum of its rows.
- Indexes: `invoices(tenant_id, issued_at desc)`, `invoices(tenant_id, status)`, `invoice_lines(invoice_id, line_no)` from the primary key serving the list-page reassembly, `invoice_lines(tenant_id, metric) where metric is not null` for the per-metric invoice reconciliation, `subscription_payment_methods(tenant_id)`, `credit_code_plans(plan)` for the reverse "which codes apply to this plan" check at redemption, `usage_records(tenant_id, metric, period_date)`, `usage_records(corrects_record_id) where corrects_record_id is not null`, `billing_webhook_events(status, received_at) where status = 'failed'`, `subscriptions(dunning_next_action_at) where dunning_stage > 0`, `subscriptions(scheduled_effective_at) where scheduled_plan is not null`. `credit_codes(batch_id)`, `credit_codes(expires_at) where redeemed_at is null`, `credit_ledger(tenant_id, created_at desc)`, `credit_ledger(tenant_id) where expires_at is not null`.
- Audit events: `subscription.plan-changed`, `subscription.change-scheduled`, `subscription.canceled`, `subscription.trial-expired`, `billing.dunning-advanced`, `billing.portal-opened`, `billing.webhook-rejected`, `billing.webhook-applied`, `usage.corrected`, `entitlement.projected`.
- Retention, deletion, and large-table impact: `usage_records` is the only high-growth table at roughly three rows per tenant per day plus hourly deltas, is partitioned by `period_date` range per year, and is kept 25 months to cover a full year-over-year comparison plus the F027 audit window; `billing_webhook_events` payloads are kept 90 days and then reduced to a header-only row so the replay guard survives the payload purge; `invoices` and `invoice_lines` are never deleted while a tenant exists; rollback drops the nine tables and the usage partitions in dependency order, children (`invoice_lines`, `subscription_payment_methods`, `credit_code_plans`) before parents.

### React/TypeScript

- Routes `/admin/billing`, `/admin/billing/invoices`, `/admin/billing/usage` in `apps/web/src/features/billing/`; components `BillingPage`, `PlanCard`, `PlanChangeDialog`, `ProrationPreviewTable`, `CancelDialog`, `DunningBanner`, `UsageCards`, `UsageTable`, `UsageCorrectionRow`, `InvoiceTable`, `EntitlementSummary`, `PortalButton`.
- State: TanStack Query keys `['billing-subscription']`, `['billing-usage', metric, range, granularity]`, `['billing-invoices', filter, cursor]`, `['billing-preview', plan, apply]`; the preview query is disabled until a plan is selected and is invalidated on confirmation; `subscription.updated.v1` arriving over the F004 realtime channel invalidates the subscription and entitlement keys so the banner clears without a reload.
- API client: generated `BillingApi` with `getSubscription`, `changeSubscription`, `previewChange`, `getUsage`, `listInvoices`, `createPortalSession`; `EntitlementSummary` reads the F048 evaluate endpoint rather than any billing-local copy.
- Telemetry: `billing_plan_change_previewed`, `billing_plan_changed`, `billing_downgrade_scheduled`, `billing_portal_opened`, `billing_usage_viewed`, `billing_dunning_banner_shown` with `plan`, `apply`, and `dunning_stage`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F064-01 through FR-F064-15 and NFR-F064-01 through NFR-F064-04 in `testing/features/F064/requirements/cases.md`
- [ ] Failure and edge-case tests: webhook replay, bad signature, stale timestamp, unknown provider, unknown customer, provider proration mismatch, provider timeout mid-change, downgrade scheduled then canceled, trial expiry with and without a payment method, dunning recovery by a late payment, correction of a corrected day
- [ ] Permission-negative and tenant-isolation tests: a tenant-admin without `billing-admin` cannot change a plan or open the portal; a member sees the denied page; a foreign invoice id returns `not_found`; a body carrying another `tenant_id` returns `invalid`; a webhook for tenant A never touches tenant B
- [ ] Rust unit tests: `crates/domain/src/billing/` proration arithmetic and rounding, dunning ladder transitions, plan-to-module projection with a `manual` override present, usage effective-quantity folding over adjustments, signature verification with a rotated secret
- [ ] API contract and integration tests: all six routes with success and each mapped error code against the mock provider
- [ ] Database migration and constraint tests: the append-only rules, the webhook unique constraint, the one-subscription-per-tenant constraint, the usage uniqueness key, partition creation, rollback, and the child tables — `invoice_lines` rejects a duplicate `(invoice_id, line_no)` and cascades when its invoice is dropped, `subscription_payment_methods` rejects a second row for one subscription and an out-of-range `exp_month`, `credit_code_plans` rejects a duplicate plan and a plan outside the F002 set, and `billing_webhook_events.payload` is the only `jsonb` column in the module
- [ ] React component tests: `PlanChangeDialog`, `ProrationPreviewTable`, `DunningBanner`, `UsageCards`, `UsageCorrectionRow`, `InvoiceTable` states
- [ ] Browser E2E tests: upgrade with preview, schedule a downgrade, drive dunning to `restricted` and recover, open the portal against the mock
- [ ] Accessibility tests: axe on all three billing routes and the plan-change and cancel dialogs, live-region announcements for the preview and the dunning stage
- [ ] Performance and load tests: meter 10,000 tenants under 10 minutes, 13-month usage query under 800 ms, webhook handling p95 under 2 s

### Fast fanout configuration

- Test harness path: `testing/features/F064/`
- Feature flag: `F064_FEATURE`
- Fixture and seed factory: `testing/fixtures/billing.rs` builds tenants A and B, a `billing-admin`, a `tenant-admin` without billing rights, a member, one subscription per status, 18 months of daily usage across the three metrics, 24 invoices, a `manual` F048 entitlement on `bridge` for the override case, and a mock payment provider server
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC everywhere, fixed period bounds `2026-09-01`–`2026-10-01`, fixed prices `team 2900` and `enterprise 9900` cents, fixed webhook signing secret and rotation pair
- Mock and stub contracts: the mock provider in `testing/harness/providers/billing/` implements the seven `PaymentProvider` operations, signs webhooks with the fixture secret, and can be told to return a proration mismatch, a timeout, a `429`, or a duplicate event; no test opens a network connection to a real payment provider and no live key exists in any fixture; the F048 entitlement service and the F037 notifier are in-memory doubles that record calls
- Parallel isolation: one schema per test worker, one tenant per test, one mock provider port per worker
- Targeted command: `cargo xtask test-feature F064`
- Full command: `cargo xtask test-all`
- CI artifact and evidence: `testing/evidence/F064/`

## 6. Acceptance criteria

```gherkin
Feature: Subscription lifecycle, metering, and dunning

Scenario: Upgrade previews proration and unlocks modules through F048
  Given a tenant on team with a period from 2026-09-01 to 2026-10-01 and a payment method
  When a billing-admin previews and confirms a change to enterprise on 2026-09-16
  Then the preview credit, charge, and net match the provider line items to the cent
  And subscription.updated.v1 is published and the F048 entitlements for bridge and workapps become active with source plan

Scenario: A replayed webhook does not double-apply
  Given a signed invoice.payment_failed event that has already been applied
  When the provider delivers the same provider_event_id again
  Then the response is 200 with status duplicate, the dunning stage is unchanged, and no second invoice.payment-failed.v1 is published

Scenario: Dunning degrades in order and never removes data access silently
  Given a tenant whose invoice failed on day 0
  When the dunning job runs through day 7 and day 14
  Then the tenant is notified at every stage with the next step and its date
  And on day 7 only plan-sourced entitlements are suspended while sheets stay editable
  And on day 14 the tenant is read-only with export still permitted and no data is deleted

Scenario: A usage correction is appended, never overwritten
  Given a seats sample of 42 recorded for 2026-09-10
  When an operator corrects it to 39 with a reason
  Then a new adjustment row of -3 referencing the original is written, the original row is unchanged, and a direct UPDATE on usage_records is rejected by the database

Scenario: A tenant-admin without billing-admin cannot change the plan
  Given a tenant-admin who holds no billing-admin role
  When they PUT /api/v1/billing/subscription with plan enterprise
  Then the response is 403 denied and the subscription version is unchanged
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F002 (`tenants.plan` values, tenant and user state, seat source of truth); F048 (the single entitlement store and its `source: plan` field, module slugs, and limit schemas); F037 for dunning and trial notifications; F004 for the secret manager, outbox, scheduler, and realtime channel; F003 for the `billing-admin` role binding and audit rows; F017 and F019 as the storage and automation-run counters; decisions sections 2, 3, 4, 7, 9; contracts row F064
- Blocks: F065
- Conflicts with: none (disjoint owned paths)
- External dependencies: one payment provider account with a hosted customer portal and signed webhooks; a mock server stands in for every automated test
- Risks and mitigations: a second entitlement source of truth, mitigated by owning no entitlement table and asserting in tests that F064 only ever calls the F048 service with `source: plan`; provider drift in proration arithmetic, mitigated by the pure `proration.rs` comparison that rejects a mismatch before writing; webhook double-application, mitigated by the unique constraint inside the applying transaction rather than an application-level check; a metering bug silently overcharging, mitigated by the append-only table, the reproducible daily samples, and a reconciliation test that rebuilds an invoice from history; a lapsed card destroying access, mitigated by the notified ladder, export preserved through suspension, and no deletion path in this feature at all; provider secret rotation, mitigated by accepting either of two signing secrets during the rotation window
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F002 and F048 accepted and archived, and the F048 entitlement service exposes `upsert_entitlement` with a `source` argument
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F064/`
- [ ] Migration file name and owned paths claimed; `billing-admin` added to the F003 role catalog
- [ ] Mock payment provider available in `testing/harness/providers/billing/` with signing, portal, proration, and webhook replay support
- [ ] Human approval recorded for the billing and migration change classes per the protected-changes rule

## 9. Exit criteria — accepted and releasable

- [ ] All FR and NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit, API, database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit rows and outbox events verified for every plan change, webhook application, dunning transition, and usage correction
- [ ] A rebuilt invoice from `usage_records` history matches the stored invoice line for the same period
- [ ] No provider type appears outside `adapters/stripe.rs` and no test reaches a real provider
- [ ] All changed files at most 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F064_FEATURE`, run the down migration on an empty tenant, and confirm F048 entitlements with `source: manual` survive
- [ ] `finished_at` recorded and the file moved to `work/archived/`

## 10. Release notes

- Billing administrators can see their subscription, preview and apply a plan change with proration, schedule a downgrade for the end of the period, cancel with access to the period end, manage payment details in the provider-hosted portal, watch metered seats, storage, and automation runs, and download invoices. Plan changes now drive F048 entitlements automatically instead of an operator edit, and a failed payment follows a notified ladder that pauses premium modules before it restricts writes and never removes read or export access without notice.
- Migration adds `subscriptions`, `subscription_payment_methods`, `invoices`, `invoice_lines`, `usage_records`, `billing_webhook_events`, `credit_codes`, `credit_code_plans`, and `credit_ledger`; `usage_records` and `credit_ledger` are append-only and `usage_records` is partitioned by period date; rollback drops all nine, children before parents. Feature is off by default behind `F064_FEATURE`.
