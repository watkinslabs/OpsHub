# F045 performance cases

File: `testing/features/F045/performance/document_bench.rs`. Runs against a seeded workspace with a 10,000-child folder and 100,000 indexed documents with fixed seed. Flag `F045_FEATURE`.

- `document_list_10k_children_p95` — NFR-F045-01: 200 sequential `GET /api/v1/documents?parent_id=...&limit=100` requests; p95 < 500 ms warm.
- `revision_save_1mb_p95` — NFR-F045-01: 100 revision posts of a 1 MB body against the in-memory object store; p95 < 800 ms including checksum and search upsert.
- `document_search_100k_p95` — NFR-F045-01: 200 `q=` searches over 100,000 documents with mixed terms; p95 < 500 ms and GIN index scan confirmed.
- `subtree_move_40_descendants_bounded` — FR-F045-03: moving a folder with 40 descendants completes in under 400 ms; 5,000 descendants under 3 s using the `path` GIN index.
- `access_walk_cached_per_request` — FR-F045-10: listing 100 children at depth 32 issues one grant query and completes under 150 ms of authz time.

Evidence: criterion/k6 summaries under `testing/evidence/F045/performance/`.
