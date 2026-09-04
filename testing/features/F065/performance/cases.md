# F065 performance cases

File: `testing/features/F065/performance/{signup_bench.rs,provision_bench.rs,sweep_bench.rs}`. Runs against a seeded platform with the stub bot check and mail sender. Flag `F065_FEATURE`.

- `signup_latency_stays_in_constant_time_band` — NFR-F065-01, FR-F065-02: 2,000 submissions across the accept, existing-user, taken-slug, and suppressed paths all land between 250 ms and 600 ms p95, with the four distributions overlapping.
- `availability_and_token_reads_under_budget` — NFR-F065-01: 1,000 availability calls p95 < 150 ms and 1,000 token reads p95 < 200 ms with the seeded 240 reservations and 10,000 live requests.
- `provisioning_p95_under_three_seconds` — NFR-F065-01: 200 completions including the F002 tenant transaction, the entitlement writes, and the F064 trial subscription complete under 3 s p95.
- `sweep_100k_requests_under_five_minutes` — NFR-F065-01, FR-F065-14: 100,000 requests spread over 60 days are abandoned, scrubbed, and deleted in 1,000-row batches in under 5 minutes.
- `burst_from_one_network_is_contained` — NFR-F065-05: 10,000 attempts from one `/24` over 10 minutes create at most 20 rows and 20 mails per hour.
- `burst_does_not_degrade_authenticated_routes` — NFR-F065-05: during that burst, p95 on `GET /api/v1/users` for a seeded tenant stays within 10 percent of its quiet baseline.
- `trial_lifecycle_scan_bounded` — NFR-F065-04: 10,000 trial tenants are scanned hourly in under 500 ms using the entitlement `trial_ends_at` index, with no duplicate reminders on a repeat run.

Evidence: criterion summaries and latency histograms under `testing/evidence/F065/performance/`.
