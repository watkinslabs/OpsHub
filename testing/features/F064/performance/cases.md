# F064 performance cases

File: `testing/features/F064/performance/{meter_bench.rs,usage_bench.rs,read_bench.rs,webhook_bench.rs}`. Runs against a seeded database with the mock payment provider. Flag `F064_FEATURE`.

- `meter_10000_tenants_under_10_minutes` — NFR-F064-01, FR-F064-11: one daily run over 10,000 tenants writes three metrics each and finishes in under 10 minutes with the unique key preventing duplicates.
- `thirteen_month_usage_query_under_800ms` — NFR-F064-01: a 13-month, three-metric, day-granularity query over 18 months of seeded rows returns in under 800 ms p95 with partition pruning confirmed.
- `subscription_read_p95_under_300ms` — NFR-F064-01: 500 subscription reads including the allowance and seat computation stay under 300 ms p95.
- `invoice_list_p95_under_500ms` — NFR-F064-01: 200 requests at `limit=50` over 24 seeded invoices stay under 500 ms p95 with the adapter mock answering `hosted_url` in batch.
- `webhook_handling_p95_under_2s` — NFR-F064-01, NFR-F064-04: 1,000 signed events including 200 replays are handled under 2 s p95 excluding adapter latency, and the replays add no write amplification.
- `dunning_ladder_scan_bounded` — FR-F064-13: 10,000 subscriptions with 500 in dunning; the daily ladder scan uses the partial index and completes in under 500 ms.
- `usage_write_amplification_bounded` — FR-F064-12: recording one month of usage for one tenant writes at most 93 rows for the three metrics plus the hourly deltas, keeping the 25-month retention footprint predictable.

Evidence: criterion summaries and query plans under `testing/evidence/F064/performance/`.
