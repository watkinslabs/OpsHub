# F073 performance cases

File: `testing/features/F073/performance/{list_bench.rs,audience_bench.rs,article_bench.rs}`. Runs against the seeded tenants. Flag `F073_FEATURE`.

- `list_p95_under_150ms_with_200_announcements` — NFR-F073-01: 200 published announcements in scope with 40 target rows each and 120 dismissals for the caller; 500 list requests complete with p95 under 150 ms and one query per request.
- `list_issues_no_per_target_round_trip` — NFR-F073-01, FR-F073-04: the statement counter shows target evaluation folded into the visible-announcement query rather than one lookup per target row.
- `audience_resolution_50k_under_3s` — NFR-F073-01, FR-F073-05: publishing an announcement targeting a 50,000-user tenant computes `audience_size` in under 3 s and does not hold the publish transaction open across the count.
- `article_read_p95_under_80ms_warm` — NFR-F073-01: 500 warm reads of an eight-article bundle across two locales with p95 under 80 ms; the matching `If-None-Match` path returns 304 in under 15 ms.
- `panel_adds_no_request_to_first_paint` — NFR-F073-01: the route's own data resolves before the panel query is issued, so the announcement list never sits on the critical path.
- `budget_check_bounded_at_scale` — FR-F073-09, NFR-F073-01: 200,000 interruption ledger rows; the rolling 24-hour and 7-day counts complete in under 20 ms using the user and `shown_at` index.
- `bundle_import_10k_translations_under_60s` — NFR-F073-04: a bundle of 500 articles across 20 locales imports in under 60 s, is resumable after a mid-run restart, and writes no duplicate version rows.

Evidence: criterion summaries and statement counts under `testing/evidence/F073/performance/`.
