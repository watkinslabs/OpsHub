---
id: T253
type: task
status: planned
parent_epic: E006
parent_feature: F064
parent_story: S127
depends_on: [S127]
owned_paths: [services/api/migrations/*_billing_*.sql, crates/domain/src/billing/**, crates/persistence/src/billing/**, testing/features/F064/database/**, testing/features/F064/api/**]
feature_flag: F064_FEATURE
branch: t253-billing-schema-and-provider-adapter
started_at: null
finished_at: null
---

# T253 — Billing schema and provider adapter

## Identity

- Parent story: `S127` Subscription and plan lifecycle
- Owner: platform
- Branch: `t253-billing-schema-and-provider-adapter`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 7; `docs/capability-contracts.md` row F064

## Objective

Create the `billing` schema — `subscriptions`, `subscription_payment_methods`, `invoices`, `invoice_lines`, `usage_records`, `billing_webhook_events`, `credit_codes`, `credit_code_plans`, `credit_ledger` — with the append-only, replay-guard, foreign-key, and enum `check` constraints, create the six repositories that own them, and implement the `PaymentProvider` port with its single Stripe-shaped adapter plus the pure proration and signature-verification code the rest of the feature builds on.

## Specification

- Owned paths: `services/api/migrations/<ts>_billing_create_tables.sql` and `.down.sql`; `crates/domain/src/billing/{mod.rs, plan.rs, subscription.rs, invoice.rs, usage.rs, provider.rs, proration.rs, webhook.rs, errors.rs, adapters/{mod.rs, stripe.rs}}`; `crates/persistence/src/billing/{mod.rs, subscription_repository.rs, invoice_repository.rs, usage_repository.rs, webhook_event_repository.rs, credit_code_repository.rs, credit_ledger_repository.rs}`
- Contract and input: the `PaymentProvider` trait with `ensure_customer`, `change_subscription`, `preview_proration`, `create_portal_session`, `fetch_invoice`, `verify_webhook`, `parse_event`, exchanging only `ProviderCustomerRef`, `ProviderSubscriptionRef`, `ProrationPreview`, `PortalSession`, `ProviderInvoice`, and `WebhookEnvelope`; secret manager keys `billing/<provider>/api_key` and `billing/<provider>/signing_secret` with a rotation pair.
- Output and behavior: DDL for the nine tables with `subscriptions(tenant_id)` unique, `check (plan in ('free','team','enterprise'))` matching FR-F002-02, `check (status in ('trialing','active','past_due','restricted','suspended','canceled'))`, `invoices(provider_invoice_id)` unique, `billing_webhook_events(provider, provider_event_id)` unique as the replay guard, `usage_records` unique `(tenant_id, metric, period_date, kind, source_ref)` plus the adjustment check constraints, the `usage_records_no_update` and `usage_records_no_delete` rules, yearly range partitions on `period_date`, the child tables `invoice_lines(invoice_id, line_no)`, `subscription_payment_methods(subscription_id)`, and `credit_code_plans(credit_code_id, plan)` that replace the former `invoices.lines`, `subscriptions.payment_method`, and `credit_codes.restrictions.plans` documents with cascading foreign keys, the declared foreign keys to `tenants(id)` and `users(id)` with `on delete restrict`, the `check (col in (...))` constraints on `plan`, `status`, `provider`, `metric`, `unit`, `kind`, and webhook `status`, and the indexes in ticket section 4; `proration.rs` computes credit, charge, and net as `unit_price * remaining_seconds / period_seconds` rounded half-up to the minor unit and is provider-independent; `webhook.rs` verifies HMAC-SHA256 over `t=<unix>.<raw body>` against either secret in the rotation window and rejects a skew above 300 seconds; `stripe.rs` is the only file naming provider JSON fields and maps every provider error to a `BillingError` variant.
- Data access: `crates/persistence/src/billing/` is created here with `SubscriptionRepository` (`subscriptions`, `subscription_payment_methods`), `InvoiceRepository` (`invoices`, `invoice_lines`), `UsageRecordRepository` (`usage_records`), `WebhookEventRepository` (`billing_webhook_events`), `CreditCodeRepository` (`credit_codes`, `credit_code_plans`), and `CreditLedgerRepository` (`credit_ledger`), each implementing the shared `Repository` contract plus the named queries in ticket section 4 and no generic query method; `SubscriptionRepository::save_payment_method`, `InvoiceRepository::upsert_from_provider`, and `CreditCodeRepository::insert_code_batch` replace a parent's child rows in one `delete`/`insert` statement pair inside the caller's `UnitOfWork`. `crates/domain/src/billing/` and the adapter hold no `sqlx::query*` call, no SQL string, and no connection; `proration.rs` and `webhook.rs` stay pure (decision section 2.1).
- Dependencies: F002 tenant rows for the `tenant_id` foreign key and the plan value set; F004 secret manager and migration runner; F003 audit table for `billing.webhook-rejected`.
- Feature flag: `F064_FEATURE` gates the adapter construction and the routes that use it; the migration runs regardless.

## TDD

- Failing test first: `testing/features/F064/database/migration_tests.rs::billing_tables_exist_with_constraints`, `::usage_records_reject_update_and_delete`, `::webhook_event_id_unique_per_provider`, `::one_subscription_per_tenant`, `::usage_partition_created_for_period_year`, `::invoice_line_number_unique_per_invoice`, `::invoice_lines_cascade_with_invoice`, `::one_payment_method_row_per_subscription`, `::credit_code_plan_row_unique`, `::billing_foreign_keys_declared_restrict`, `::rollback_drops_billing_tables_children_first`; `testing/features/F064/api/proration_tests.rs::mid_period_upgrade_credit_and_charge_round_half_up`, `::equal_plans_net_zero`, `::preview_mismatch_rejected_before_write`; `testing/features/F064/api/adapter_tests.rs::webhook_signature_verified_against_rotated_secret`, `::stale_timestamp_rejected`, `::provider_error_maps_to_billing_error`, `::no_provider_type_outside_adapter`
- Targeted command: `cargo xtask test-feature F064`
- Full command: `cargo xtask test-all`
- Fixtures and mocks: `testing/fixtures/billing.rs`; the mock payment provider in `testing/harness/providers/billing/` signing with the fixture secret pair; fixed clock `2026-09-03T00:00:00Z`, fixed period `2026-09-01`–`2026-10-01`, fixed prices `team 2900` and `enterprise 9900` cents

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18 with the partitions created and dropped, children dropped before parents
- [ ] `cargo xtask check-persistence` passes: every billing table is written by exactly one repository and no SQL exists outside `crates/persistence/src/billing/`
- [ ] The append-only rules and the replay-guard unique constraint proven by database-level tests, not application assertions
- [ ] Owned-path check passes and no provider type name appears outside `adapters/stripe.rs`
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S127
- [ ] `finished_at` recorded
