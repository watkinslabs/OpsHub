---
id: T037
type: task
status: planned
parent_epic: E002
parent_feature: F010
parent_story: S019
depends_on: [S019]
owned_paths: [crates/domain/src/dataio/**, services/api/src/dataio/**, services/worker/src/dataio/**, services/api/migrations/*_dataio_*.sql, testing/features/F010/database/**, testing/features/F010/api/**]
feature_flag: F010_FEATURE
branch: t037-full-text-index
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 7, 9
- Capability contract: `docs/capability-contracts.md` row F010

# T037 — Full-text index

## Identity

- Parent story: `S019` Search
- Owner: platform
- Branch: `t037-full-text-index`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 7, 9; `docs/capability-contracts.md` row F010

## Objective

Create the nine `dataio` tables, the outbox-driven search indexer, and the ACL-filtered `GET /api/v1/search` route so tenant-scoped full-text search works before any import or export code exists.

## Specification

- Owned paths: `services/api/migrations/<ts>_dataio_create_tables.sql`, `services/api/migrations/<ts>_dataio_create_tables.down.sql`, `crates/domain/src/dataio/{mod.rs, errors.rs, schema.rs, search/mod.rs, search/indexer.rs, search/query.rs, search/acl_filter.rs}`, `services/api/src/dataio/{mod.rs, routes.rs, handlers_search.rs, dto.rs}`, `services/worker/src/dataio/{mod.rs, index_consumer.rs}`
- Contract/input: `SearchQuery { q: String (1–256), kind: Option<DocKind>, workspace_id, sheet_id, cursor, limit (1–100, default 25) }`; consumer subscriptions `sheet.created.v1`, `sheet.updated.v1`, `sheet.deleted.v1`, `sheet.restored.v1`, `row.created.v1`, `row.updated.v1`, `row.deleted.v1`, `row.restored.v1`, `cell.updated.v1`, `cells.bulk-updated.v1`, `comment.created.v1`, `file.uploaded.v1`; `index_event(event) -> IndexOutcome::{Upserted, Removed, Stale}`.
- Output/behavior: migration creates `search_documents`, `search_document_principals`, `import_jobs`, `import_column_mappings`, `import_rows`, `import_row_errors`, `export_jobs`, `export_job_columns`, and `export_job_filters` with the check constraints, primary keys, GIN indexes on `body` and `body_simple`, and the secondary indexes from ticket section 4 — no `acl_snapshot`, `mapping`, `cursor`, `report`, `errors`, `filter`, or `columns` `jsonb` column exists, their contents being rows and typed columns instead; the indexer builds `title` and `body` per kind (row body is the concatenation of text-like cell display values, comment body is a 200-char prefix plus author, attachment body is filename plus MIME plus size), upserts through `SearchDocumentRepository::upsert_document` (`on conflict ... where source_version < excluded.source_version`) together with the document's `search_document_principals` rows in the same statement, deletes on soft delete, and emits `search.indexed.v1`; `SearchDocumentRepository::search_ranked` joins `english` and `simple` `to_tsquery` with prefix matching on the last term, ranks by `ts_rank_cd`, snippets with `ts_headline`, and prefilters by joining `search_document_principals` against the actor and its groups; the query module then calls the F003 policy engine per hit and drops denied hits before paging; every statement lives in `crates/persistence/src/dataio/`; response `SearchResponse { hits, next_cursor }`; foreign-tenant filters return an empty page.
- Dependencies: F004 outbox consumer registry and job runs; F003 `authz::check_many(actor, resources)`; F006 `sheets`/`rows`/`cells` tables; F016 comment and F017 file events consumed when present, tolerated as absent.
- Feature flag: `F010_FEATURE` gates router mounting and consumer registration; migration runs regardless.
- Large-table note: `search_documents` and `search_document_principals` grow to millions of rows; the GIN indexes are created with `fastupdate = off` and the consumer batches upserts in groups of 500.

## TDD

- Failing test first: `testing/features/F010/database/migration_tests.rs::dataio_tables_exist_with_constraints`, `::search_body_gin_index_used`, `::stale_source_version_upsert_is_noop`, `::document_principals_replaced_with_document`, `::document_principals_cascade_on_document_delete`, `::rollback_drops_tables`; `testing/features/F010/api/search_tests.rs::search_returns_ranked_hits_with_snippets`, `::search_omits_unreadable_sheet_rows`, `::search_cross_tenant_returns_empty`, `::search_empty_query_invalid`, `::indexer_upserts_and_ignores_stale_version`, `::indexer_removes_soft_deleted_source`, `::indexer_never_reads_file_bodies`
- Targeted command: `cargo xtask test-feature F010`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: schema-per-worker database from `testing/harness/db.rs`; `testing/fixtures/dataio.rs` sheets `Plan` and `Payroll` with seeded comment and attachment metadata; in-memory outbox recorder driving the consumer directly

## Exit criteria

- [ ] Tests written before the migration, indexer, and route and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; consumer registered behind the flag
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S019
- [ ] `finished_at` recorded
