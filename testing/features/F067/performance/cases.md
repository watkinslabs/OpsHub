# F067 performance cases

The product's performance is what the profiles measure; this lane measures the harness itself, because a gate that costs hours or exhausts memory will be skipped by the people who need it.

File: `testing/features/F067/performance/{seed_budget_tests.rs,gate_budget_tests.rs,reporter_tests.rs}`. Flag `F067_FEATURE`. Fixtures: scaled `smoke` variants, a synthetic 8-hour stream of 2.9 million samples, reference machine profile of 16 vCPU and 64 GiB.

- `smoke_seed_under_ninety_seconds` — NFR-F067-01: the `smoke` dataset builds within its budget on the reference machine.
- `tier1_seed_within_twenty_five_minutes` — FR-F067-04: measured on the nightly runner and recorded in the manifest `duration_s`.
- `full_seed_within_four_hours` — FR-F067-04: the milestone dataset build stays inside its budget; the ≈4 million rows and ≈250 million cells are counted.
- `budget_overrun_exits_dataset_timeout` — FR-F067-04: a throttled fixture exceeding the budget → exit 2 `dataset.timeout` rather than an open-ended run.
- `cache_restore_of_tier1_under_twelve_minutes` — FR-F067-05: restoring from the archive beats regeneration by more than an order of magnitude.
- `dry_run_under_two_hundred_milliseconds` — NFR-F067-01: profile parse, dataset resolve, and plan print with no network call.
- `preflight_under_thirty_five_seconds` — NFR-F067-01: including a readiness probe that uses its full 30 s timeout.
- `evaluation_and_report_under_ten_seconds` — NFR-F067-01: threshold evaluation, comparison against the reference set, and report rendering for one run.
- `eight_hour_stream_renders_under_sixty_seconds` — NFR-F067-01: 2.9 million samples streamed from `metrics.ndjson.zst` under 256 MiB resident memory, never loaded whole.
- `rss_slope_regression_is_stable_on_flat_input` — FR-F067-08: a flat synthetic memory series yields a slope near zero with r² reported, so a soak does not fail on arithmetic noise.

Evidence: timing tables, memory high-water marks, and manifest durations under `testing/evidence/F067/performance/`.
