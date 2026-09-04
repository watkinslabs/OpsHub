---
id: T255
type: task
status: planned
parent_epic: E006
parent_feature: F064
parent_story: S128
depends_on: [S128, T253]
owned_paths: [crates/domain/src/billing/**, crates/persistence/src/billing/**, services/api/src/billing/**, services/worker/src/billing/**, apps/web/src/features/billing/**, testing/features/F064/api/**, testing/features/F064/frontend/**, testing/features/F064/performance/**]
feature_flag: F064_FEATURE
branch: t255-usage-metering-and-invoices
started_at: null
finished_at: null
---

# T255 — Usage metering and invoices

## Identity

- Parent story: `S128` Usage metering and invoicing
- Owner: platform
- Branch: `t255-usage-metering-and-invoices`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 7, 9; `docs/capability-contracts.md` row F064

## Objective

Implement the three-metric meter, the append-only usage record with signed adjustments, the usage query and invoice list routes, invoice ingestion from provider events, and the usage and invoice surfaces.

## Specification

- Owned paths: `crates/domain/src/billing/{metering.rs, usage.rs, allowances.rs, invoice_sync.rs}`; the metering, invoice, and credit named queries added to `crates/persistence/src/billing/{usage_repository.rs, invoice_repository.rs, credit_code_repository.rs, credit_ledger_repository.rs}`; `services/api/src/billing/{handlers_usage.rs, handlers_invoices.rs}`; `services/worker/src/billing/{meter.rs, invoice_sync.rs}`; `apps/web/src/features/billing/{UsageCards.tsx, UsageTable.tsx, UsageCorrectionRow.tsx, InvoiceTable.tsx, usageApi.ts}`
- Contract and input: `UsageQuery { metric?, from, to, granularity }` with a range of at most 400 days; the correction call `correct_usage(record_id, delta, reason)` with a 10–500 character reason; invoice list query `{ status?, from?, to?, cursor?, limit? }` with `limit` 1–100; provider events `invoice.finalized`, `invoice.paid`, `invoice.payment_failed` arriving through the T254 webhook handler.
- Output and behavior: `meter.rs` writes a daily `sample` at 00:05 UTC for `seats` (active F002 users with an F003 role binding) and `storage_gb` (sum of non-deleted F017 `file_versions.size_bytes` divided by 2^30) and an hourly `delta` for `automation_runs` (terminal F019 `workflow_runs`), and meters nothing else; every write is idempotent by `(tenant_id, metric, period_date, kind, source_ref)` and publishes `usage.recorded.v1`; a correction appends an `adjustment` row with a signed quantity and `corrects_record_id` and never updates or deletes, which the database rules enforce; `GET /api/v1/billing/usage` folds samples, deltas, and adjustments into an effective quantity with `adjustments_applied` and `as_of`, and reports `overage` against the plan allowance without blocking any operation; `invoice_sync.rs` upserts the `invoices` header and replaces its `invoice_lines` rows from `ProviderInvoice` in one transaction and publishes `invoice.issued.v1`; `GET /api/v1/billing/invoices` pages newest first, reassembles each `lines` array from `invoice_lines` in `line_no` order so the DTO is unchanged, and fetches `hosted_url` on read without persisting it; both routes require `billing-admin` and filter by the gateway tenant context.
- Data access: `metering.rs`, `usage.rs`, `allowances.rs`, `invoice_sync.rs`, the two handlers, and the meter job hold no SQL. Usage rows are written by `UsageRecordRepository::{append_sample, append_delta, append_adjustment}` — the trait exposes no update or delete — and read by `sum_effective_quantity` and `list_daily_usage`; invoices by `InvoiceRepository::{upsert_from_provider, list_with_lines}`; credit by `CreditCodeRepository::{insert_code_batch, claim_by_hash, list_plan_restrictions}` and `CreditLedgerRepository::{append_ledger_entry, balance_for_tenant, list_ledger_entries, list_credit_expiring_before}`. A credit application against a finalizing invoice writes the ledger entry and the invoice update in one `UnitOfWork` (decision section 2.1).
- Dependencies: T253 for the `usage_records`, `invoices`, `invoice_lines`, `credit_codes`, `credit_code_plans`, and `credit_ledger` tables, their repositories, and the `PaymentProvider` port; T254 for the webhook entry point that delivers invoice events; F002, F017, and F019 as the three counter sources; F004 scheduler and outbox.
- Feature flag: `F064_FEATURE` gates the usage and invoice routes, the meter job, and the usage and invoice views.

## TDD

- Failing test first: `testing/features/F064/api/metering_tests.rs::meter_records_three_metrics_only`, `::meter_rerun_is_idempotent_by_source_ref`, `::seats_counts_active_users_with_role_binding`, `::storage_excludes_deleted_file_versions`, `::automation_runs_counted_at_terminal_status`; `testing/features/F064/api/usage_tests.rs::adjustment_requires_reason_and_target`, `::usage_query_folds_adjustments`, `::usage_range_over_400_days_invalid`, `::overage_reported_without_blocking`, `::usage_recorded_event_published`; `testing/features/F064/api/invoice_tests.rs::invoice_finalized_publishes_invoice_issued`, `::invoice_rebuilt_from_usage_matches_stored_lines`, `::invoice_list_filters_and_pages_newest_first`, `::invoice_lines_replaced_on_refinalize`, `::invoice_line_totals_match_subtotal`, `::hosted_url_fetched_on_read_not_persisted`; `testing/features/F064/performance/usage_bench.rs::thirteen_month_usage_query_under_800ms`
- Targeted command: `cargo xtask test-feature F064`
- Full command: `cargo xtask test-all`
- Fixtures and mocks: `testing/fixtures/billing.rs` seeding 18 months of daily usage across the three metrics, 24 invoices, and one corrected day; the mock payment provider emitting signed invoice events on demand; fixed clock `2026-09-03T00:00:00Z` and UTC period dates

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Meter job registered in `services/worker/src/registry.rs` and usage and invoice handlers mounted by `services/api/src/billing/routes.rs`
- [ ] The invoice reconciliation test passes against seeded history including the corrected day
- [ ] Owned-path check passes
- [ ] File limit, lint, and performance gates pass
- [ ] Handoff evidence recorded in S128
- [ ] `finished_at` recorded
