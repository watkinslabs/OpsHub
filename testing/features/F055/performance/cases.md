# F055 performance cases

File: `testing/features/F055/performance/` (criterion plus k6 against the seeded tenant). Flag `F055_FEATURE`.

- `events_window_p95_under_500ms` — NFR-F055-01: 31-day window over 20 sources totalling 100,000 rows, 50 virtual users, p95 < 500 ms with the typed date index in the plan.
- `ics_feed_5000_events_under_2s` — NFR-F055-01: 5,000-event feed streams fully in under 2 s and holds under 64 MiB resident.
- `normalize_event_and_ics_encode_benchmarks` — FR-F055-05, FR-F055-08: criterion benchmarks over DST fixtures guard against regressions above 10% on the pure functions.
- `token_rate_limit_holds_under_burst` — NFR-F055-02: 600 requests in one minute on one token yield 60 successes and 540 `429`s with no extra database load.
- `telemetry_present_under_load` — NFR-F055-04: `calendar_events_duration_seconds` and `calendar_ics_requests_total{result}` are populated and spans carry `source_count` and `hidden_sources`.

Evidence: k6 summaries, criterion reports, and metric scrapes under `testing/evidence/F055/performance/`.
