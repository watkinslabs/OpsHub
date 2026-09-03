---
id: T178
type: task
status: planned
parent_epic: E004
parent_feature: F045
parent_story: S089
depends_on: [T177]
owned_paths: [crates/domain/src/documents/**, services/api/src/documents/**, testing/features/F045/api/**, testing/features/F045/performance/**]
feature_flag: F045_FEATURE
branch: t178-folder-tree-search
started_at: null
finished_at: null
---

# T178 — Folder tree/search

## Identity

- Parent story: `S089` Document library
- Owner: platform
- Branch: `t178-folder-tree-search`
- Decision references: `docs/architecture-decisions.md` sections 2, 3; `docs/capability-contracts.md` row F045

## Objective

Implement the folder hierarchy operations (path maintenance, move with cycle and depth checks, paged child listing) and the full-text search index maintenance and query that back the library's tree, list, and search box.

## Specification

- Owned paths: `crates/domain/src/documents/{path.rs, search.rs, service_tree.rs}`, `services/api/src/documents/{handlers_tree.rs, handlers_search.rs}`
- Contract/input: `MoveDocumentRequest { parent_id }` with `If-Match`; list query `{ parent_id?, cursor?, limit? ≤ 100, kind?, deleted?, archived?, q?, sort? }`; search text is the first 64 KB of extracted revision text plus the title.
- Output/behavior: `POST /api/v1/documents/{id}/move` rewrites `path` and `depth` on the node and every descendant in one transaction using the `path` GIN index, rejects self or descendant targets with `400 invalid` `field_errors.parent_id = "cycle"`, rejects depth above 32 with `"too_deep"`, and emits `document.moved.v1` with `old_parent_id` and `new_parent_id`; `GET /api/v1/documents` pages children by opaque cursor in `title` or `updated_at` order; with `q` it runs `document_search.tsv @@ websearch_to_tsquery(...)`, ranks with `ts_rank_cd`, returns `ts_headline` snippets, and filters hits through the effective-access walk before paging; `add_revision` and title updates upsert `document_search` in the same transaction.
- Dependencies: T177 schema and node service; F049 tenant locale configuration for `tsv` when present, otherwise `simple`.
- Feature flag: `F045_FEATURE`

## TDD

- Failing test first: `testing/features/F045/api/tree_tests.rs::document_move_into_descendant_rejected`, `::document_move_depth_33_rejected`, `::document_move_rewrites_descendant_paths`, `::document_list_pages_children_by_title`; `testing/features/F045/api/search_tests.rs::document_search_returns_snippets`, `::document_search_updates_on_revision`; `testing/features/F045/performance/document_bench.rs::document_list_10k_children_p95`, `::document_search_100k_p95`
- Targeted command: `cargo xtask test-feature F045`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: seeded 4-folder/25-document tree; 10,000-child and 100,000-document generators with fixed seed and known body text

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] p95 targets from NFR-F045-01 for listing and search met in the performance lane
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S089
- [ ] `finished_at` recorded
