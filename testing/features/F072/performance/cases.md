# F072 performance cases

File: `testing/features/F072/performance/{ingest_bench.rs,apply_bench.rs,log_bench.rs,refusal_bench.rs}`. Runs against a seeded tenant with the mock inbound provider. Flag `F072_FEATURE`.

- `sustains_twenty_messages_per_second` — NFR-F072-01: the mock posts 12,000 deliveries over 10 minutes across three addresses; the ingest job keeps queue depth bounded and drops none.
- `webhook_ack_p95_under_400ms` — NFR-F072-01: 2,000 accepted deliveries; acknowledgement p95 below 400 ms excluding the refusal timing floor.
- `apply_p95_under_fifteen_seconds` — NFR-F072-01: 200 messages of 5 MB with three attachments each; end-to-end delivery-to-row p95 below 15 s including F017 uploads.
- `log_paging_p95_under_500ms` — NFR-F072-01: 100,000 messages in one tenant; 200 cursor pages of the log and 200 address list reads, both p95 below 500 ms.
- `refusal_timing_within_measured_floor` — FR-F072-07, NFR-F072-02: 1,000 refusals across the five reasons; every elapsed time sits inside the 250 ms floor band and the reasons are statistically indistinguishable.
- `rate_window_check_is_single_row` — FR-F072-08: at 600 addresses the limit check reads one `inbound_rate_windows` row and stays under 5 ms p99.
- `retention_sweep_bounded` — FR-F072-16: 50,000 expired raw objects are deleted in batches with a bounded rate and no table lock longer than one second.

Evidence: criterion summaries and queue-depth samples under `testing/evidence/F072/performance/`.
