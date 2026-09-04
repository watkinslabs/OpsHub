---
id: S128
type: story
status: planned
parent_epic: E006
parent_feature: F064
depends_on: [F002, F048]
owned_paths: [crates/domain/src/billing/**, crates/persistence/src/billing/**, services/api/src/billing/**, services/worker/src/billing/**, apps/web/src/features/billing/**, testing/features/F064/**]
feature_flag: F064_FEATURE
branch: s128-usage-metering-and-invoicing
started_at: null
finished_at: null
---

# S128 — Usage metering and invoicing

## Identity

- Parent feature: `F064` Billing and subscriptions
- Owner: platform
- Branch: `s128-usage-metering-and-invoicing`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 7, 9; `docs/capability-contracts.md` row F064

## Vertical slice

As a billing administrator, I want seats, storage, and automation runs metered on a schedule I can audit, corrections appended rather than rewritten, and every invoice reproducible from that history, so that I can explain any line on any invoice months later and challenge one without anybody editing the past.

## Requirements

- **SR-S128-01:** The worker job `billing.meter` records exactly three metrics — `seats` from active F002 users holding an F003 role binding, `storage_gb` from non-deleted F017 `file_versions.size_bytes`, and `automation_runs` from terminal F019 `workflow_runs` — as a daily `sample` at 00:05 UTC for the first two and an hourly `delta` for the third, and meters nothing else because churning object counts would make an invoice irreproducible (covers FR-F064-11).
- **SR-S128-02:** `usage_records` is append-only in the database, not only in code: a correction is a new `adjustment` row carrying a signed `quantity`, `corrects_record_id`, and a 10–500 character `reason`, while `UPDATE` and `DELETE` on the table raise a database exception; every read and write goes through `UsageRecordRepository::{append_sample, append_delta, append_adjustment}`, which expose no update or delete method at all (FR-F064-12).
- **SR-S128-03:** `GET /api/v1/billing/usage?metric=&from=&to=&granularity=day|month` folds samples, deltas, and adjustments into an effective quantity with `adjustments_applied` and `as_of`, rejects a range beyond 400 days or an inverted range with `400 invalid`, and reports usage over the plan allowance as `overage` without ever blocking work (FR-F064-12).
- **SR-S128-04:** Each recorded row publishes `usage.recorded.v1` with `metric`, `kind`, `period_date`, and `quantity`, and each meter run is idempotent by `(tenant_id, metric, period_date, kind, source_ref)` so a re-run after a restart writes nothing new (FR-F064-12, NFR-F064-04).
- **SR-S128-05:** `invoice.finalized` upserts `invoices` and publishes `invoice.issued.v1`, `invoice.paid` clears dunning and restores `active` with plan entitlements, and `invoice.payment_failed` publishes `invoice.payment-failed.v1` with `attempt` and `next_retry_at` and hands off to the dunning ladder (FR-F064-10, FR-F064-13).
- **SR-S128-06:** `GET /api/v1/billing/invoices` pages newest first with `status`, `from`, and `to` filters and fetches `hosted_url` from the adapter on read rather than persisting it; `InvoiceRepository::list_with_lines` reads the page's `invoice_lines` rows in one query and reassembles them into the `lines` array in `line_no` order, so the DTO still returns totals in minor units with per-line `metric` and `quantity` (FR-F064-15).
- **SR-S128-07:** An invoice rebuilt from `usage_records` history for the same period reconciles to the stored `invoice_lines` rows per metric and to `invoices.subtotal_cents`, and the reconciliation runs as a test rather than a manual check (FR-F064-11, FR-F064-12).
- **SR-S128-08:** The usage view renders three metric cards with numeric labels beside every bar, a daily table, and a corrected day showing the original value, the adjustment, the reason, and the actor; the 13-month query stays under 800 ms p95 and the meter covers 10,000 tenants in under 10 minutes (NFR-F064-01, NFR-F064-03).
- **SR-S128-09:** Usage and invoice routes require `billing-admin`, foreign invoice ids return `not_found`, usage rows are always filtered by the gateway tenant context, and a failed webhook application is retried 5 times and then dead-lettered with an operator alert (NFR-F064-02, NFR-F064-04).

- **SR-S128-11:** A platform operator mints one-time credit codes in batches; each plaintext is returned once and only its SHA-256 hash is stored, so a lost code is reissued rather than recovered; batch restrictions are stored as the typed `new_tenants_only` and `restricted_tenant_id` columns plus one `credit_code_plans` row per allowed plan, and `CreditCodeRepository` reassembles the `restrictions` object for the operator response (FR-F064-16, NFR-F064-02).
- **SR-S128-12:** Redemption is atomic and single-use — the conditional claim and the ledger entry commit in one transaction, concurrent attempts yield exactly one winner, failure reasons are distinguished without revealing a code, and attempts are rate limited per tenant; `not_applicable` is decided by joining `credit_code_plans` and comparing the typed restriction columns, never by reading a document key (FR-F064-17).
- **SR-S128-13:** Credit is an append-only ledger whose sum is the balance; it applies at invoice finalization before any provider charge, partially or in full, carries forward, expires with a warning, is never refundable, and a covered failure keeps the tenant out of the dunning ladder (FR-F064-18, FR-F064-13).

## Surfaces

- Data access: `crates/persistence/src/billing/{usage_repository.rs, invoice_repository.rs, credit_code_repository.rs, credit_ledger_repository.rs}` hold every SQL statement in this slice — `UsageRecordRepository` owns `usage_records` and its partitions, `InvoiceRepository` owns `invoices` and `invoice_lines`, `CreditCodeRepository` owns `credit_codes` and `credit_code_plans`, `CreditLedgerRepository` owns `credit_ledger`; the meter job, the invoice sync job, the usage and invoice handlers, and the credit routes call those traits and hold no SQL, and a redemption or a credit application runs in one `UnitOfWork` (decision section 2.1)
- Infrastructure and container: the F004 scheduler entries for `billing.meter` daily at 00:05 UTC and hourly, and the JetStream consumer for the F019 workflow-run stream that feeds automation-run deltas
- Rust service and API: `crates/domain/src/billing/{metering.rs, usage.rs, invoice.rs, allowances.rs}`; `services/api/src/billing/{handlers_usage.rs, handlers_invoices.rs}`; `services/worker/src/billing/{meter.rs, invoice_sync.rs}`
- Data and migration: `usage_records`, `invoices`, `invoice_lines`, `credit_codes`, `credit_code_plans`, and `credit_ledger` from the S127 migration, plus the yearly range partitions on `usage_records(period_date)` and the `usage_records_no_update` and `usage_records_no_delete` rules
- React and UI: `apps/web/src/features/billing/{UsageCards.tsx, UsageTable.tsx, UsageCorrectionRow.tsx, InvoiceTable.tsx, usageApi.ts}`
- Mocks and fixtures: `testing/fixtures/billing.rs` seeding 18 months of daily usage across the three metrics, 24 invoices, and a corrected day; the mock payment provider emitting signed `invoice.finalized`, `invoice.paid`, and `invoice.payment_failed` events on demand

## TDD harness

- Test path: `testing/features/F064/{api,database,frontend,performance}/`
- Feature flag: `F064_FEATURE`
- Targeted command: `cargo xtask test-feature F064`
- Full command: `cargo xtask test-all`
- First failing tests: `credit_redemption_is_single_use`, `concurrent_redemption_yields_exactly_one_winner`, `credit_covers_invoice_without_provider_charge`, `credit_covering_failure_prevents_dunning`, `meter_records_three_metrics_only`, `meter_rerun_is_idempotent_by_source_ref`, `usage_update_and_delete_rejected_by_database`, `adjustment_requires_reason_and_target`, `usage_query_folds_adjustments`, `overage_reported_without_blocking`, `invoice_finalized_publishes_invoice_issued`, `invoice_lines_replaced_on_refinalize`, `credit_code_plan_restriction_blocks_wrong_plan`, `invoice_rebuilt_from_usage_matches_stored_lines`, `invoice_list_filters_and_pages_newest_first`

## Exit criteria

- [ ] Requirement tests SR-S128-01 through SR-S128-09 written first and observed failing
- [ ] Tasks T255 and T256 complete and wired through `services/api` router and `services/worker` registry
- [ ] Unit, API, database, React, performance, and permission tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/billing/{handlers_usage.rs, handlers_invoices.rs}` mounted by `services/api/src/billing/routes.rs`; `services/worker/src/billing/{meter.rs, invoice_sync.rs}` registered in `services/worker/src/registry.rs`
- [ ] The invoice reconciliation test passes against 18 months of seeded history including a corrected day
- [ ] Handoff evidence recorded in the F064 ticket
