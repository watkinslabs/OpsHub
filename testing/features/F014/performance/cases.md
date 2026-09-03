# F014 performance cases

File: `testing/features/F014/performance/submission_bench.rs`. Runs against a published 40-field form with two file fields and four conditions, fixed seed. Flag `F014_FEATURE`.

- `public_schema_p95` — NFR-F014-01: 500 sequential `GET /public/forms/{token}` requests; p95 < 300 ms warm; cache hit ratio ≥ 0.95 after first request.
- `submission_accept_p95` — NFR-F014-01: 200 accepted submissions across 200 distinct IPs; p95 < 800 ms including intake event and row create.
- `rate_limiter_burst` — FR-F014-07: k6 burst of 300 requests in 10 s from one IP; first 60 accepted, rest 429 within 50 ms each; no database write for rejected requests.
- `schema_cache_invalidates_on_publish` — NFR-F014-01: publish version 2 then `GET` within 1 s returns version 2 fields.
- `submissions_list_index_scan` — FR-F014-17: 50,000 intake events on one form; `limit=200` page p95 < 300 ms using the received-at index.

Evidence: criterion/k6 summaries under `testing/evidence/F014/performance/`.
