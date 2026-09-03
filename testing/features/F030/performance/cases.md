# F030 performance cases

File: `testing/features/F030/performance/{run_bench.rs,mapping_bench.rs,read_bench.rs}`. Runs against a seeded tenant with mock connectors. Flag `F030_FEATURE`.

- `ten_thousand_records_under_ten_minutes` — NFR-F030-01: a 10,000-record inbound Salesforce run at 200 records per page, with the mock returning `429` every 40th page, completes in under 10 minutes with per-sync concurrency 1.
- `sync_and_conflict_reads_p95_under_500ms` — NFR-F030-01: 200 requests each against `GET /api/v1/syncs` and `GET /api/v1/syncs/{id}/conflicts` with 200 syncs and 5,000 open conflicts; p95 < 500 ms.
- `run_enqueue_ack_under_two_seconds` — NFR-F030-01: 100 `POST /run` calls; p95 acknowledgement < 2 s while five runs execute concurrently.
- `mapping_preview_under_one_second` — NFR-F030-01: 100 previews of five records across 30 mappings including one `lookup`; p95 < 1 s.
- `transform_catalog_under_five_milliseconds` — NFR-F030-01: criterion over all twelve transforms; each stays under 5 ms per cell at the 99th percentile.
- `checkpoint_overhead_under_five_percent` — NFR-F030-04: the same 10,000-record run with checkpointing every 500 records costs under 5% more wall time than a single terminal checkpoint.
- `scheduler_scan_bounded` — FR-F030-08: 5,000 syncs across 200 tenants; the due-sync scan uses `syncs(tenant_id, state, connector)` and completes in under 500 ms per tick.
- `conflict_detection_scales_with_links` — NFR-F030-01: 100,000 `sync_record_links` rows; per-record conflict detection stays under 2 ms using the `(sync_id, external_id)` primary key.

Evidence: criterion summaries under `testing/evidence/F030/performance/`.
