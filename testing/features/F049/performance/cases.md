# F049 performance cases

File: `testing/features/F049/performance/{resolve_bench.rs,catalog_bench.rs,first_paint.spec.ts}`. Runs against seeded tenants with eight 2,000-key catalogs and fixed seed. Flag `F049_FEATURE`.

- `resolve_effective_locale_p95` — NFR-F049-01: 100,000 resolutions across 1,000 users with a warm cache; p95 < 1 ms; cache invalidation after `locale.updated.v1` observed within one request.
- `messages_2k_keys_p95` — NFR-F049-01: 200 sequential uncached `GET /api/v1/messages/de-DE`; p95 < 50 ms; `304` path p95 < 5 ms.
- `first_paint_with_catalog_p95` — NFR-F049-01: 20 cold loads of `/w/{workspace}` with `de-DE` catalog on the CI throttling profile; first contentful paint p95 < 500 ms.
- `format_datetime_throughput` — FR-F049-06: formatting 100,000 datetimes for `Europe/Berlin` including DST arithmetic completes under 200 ms.
- `grapheme_len_large_input` — FR-F049-07: `grapheme_len` on a 1 MB mixed-script string completes under 20 ms.

Evidence: criterion and Playwright timing summaries under `testing/evidence/F049/performance/`.
