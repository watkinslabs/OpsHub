# F057 performance cases

File: `testing/features/F057/performance/asset_bench.rs`. Runs against the 200,000-asset generator with fixed seed and MinIO. Flag `F057_FEATURE`.

- `library_list_200k_p95` — NFR-F057-01: 200 sequential `GET /assets?limit=50` with `q` and `usable` filters; p95 < 500 ms warm.
- `thumbnail_ready_within_60s` — NFR-F057-01: 20 uploads of 50 MB images; thumbnail ready p95 < 60 s.
- `rendition_url_redirect_p95` — FR-F057-04: 500 rendition URL requests; p95 < 200 ms.
- `collection_replace_5000_items` — FR-F057-08: replacing 5,000 members completes under 2 s.
- `video_consumer_concurrency_bounded` — NFR-F057-04: 10 queued videos; at most 2 in flight; none exceed the 10-minute timeout.

Evidence: criterion/k6 summaries under `testing/evidence/F057/performance/`.
