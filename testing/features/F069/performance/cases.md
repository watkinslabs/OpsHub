# F069 performance cases

File: `testing/features/F069/performance/{home_bench.rs,list_bench.rs,visit_bench.rs,prune_bench.rs}`. Runs against the seeded tenant with the three slots stubbed at a fixed 20 ms. Flag `F069_FEATURE`.

- `home_p95_under_400ms` — NFR-F069-01: 300 requests for a member with 200 favourites, 100 recents and five registered providers; p95 < 400 ms and p99 < 800 ms on a warm pool and a cold cache.
- `home_statement_count_is_thirteen_at_full_caps` — NFR-F069-01: the statement recorder counts thirteen — five providers plus one `resolve_readable` per distinct kind — and the count is unchanged when the item set is multiplied tenfold.
- `home_cost_flat_across_sheet_count` — NFR-F069-01: the same request against 5 and 500 readable sheets issues the same number of statements, proving no fan-out per sheet.
- `favorites_and_recents_p95_under_150ms` — NFR-F069-01: 300 requests each against the full caps stay under 150 ms p95 using the declared indexes.
- `visit_recording_under_1ms_p99` — NFR-F069-01, FR-F069-07: 10,000 observed reads measured with and without `RecentVisitLayer`; the added latency is under 1 ms at p99 and no request status changes.
- `flusher_batches_five_thousand_visits` — NFR-F069-04: 5,000 buffered visits drain in one 5 s window within the channel bound, with the drop counter at zero.
- `prune_ten_thousand_rows_under_thirty_seconds` — FR-F069-10: a 20,000-row backlog is processed 10,000 rows per run in 500-id batches, each run under 30 seconds.

Evidence: criterion summaries and statement traces under `testing/evidence/F069/performance/`.
