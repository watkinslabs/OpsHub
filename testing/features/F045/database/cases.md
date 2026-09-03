# F045 database cases

File: `testing/features/F045/database/migration_tests.rs`. Flag `F045_FEATURE`.

- `documents_tables_exist_with_constraints` — T177: `documents`, `document_revisions`, `document_search` exist with tenant, version, audit, soft-delete columns and the `kind` check.
- `sibling_title_duplicate_rejected` — FR-F045-02: `documents_sibling_title_idx` blocks case-insensitive duplicate under the same parent while `deleted_at is null`; allows after delete and under a different parent.
- `revision_number_unique_per_document` — FR-F045-07: second `(document_id, revision)` insert violates `document_revisions_doc_rev_idx`.
- `path_check_trigger_rejects_cycle` — FR-F045-03: direct update setting `parent_id` to a descendant or to `id` raises from `documents_path_check`.
- `depth_over_32_rejected` — FR-F045-03: insert with `depth = 33` violates the check constraint.
- `revision_row_requires_document` — FR-F045-07: foreign key rejects an orphan revision; `on delete restrict` blocks hard delete of a document with revisions.
- `search_row_cascades_with_document` — FR-F045-06: hard-deleting a document (purge path) removes its `document_search` row.
- `search_gin_index_used_for_query` — NFR-F045-01: `EXPLAIN` on `tsv @@ websearch_to_tsquery(...)` uses the GIN index on `document_search`.
- `path_gin_index_used_for_subtree` — NFR-F045-01: `EXPLAIN` on `where path @> array[folder_id]` uses the `path` GIN index.
- `subtree_soft_delete_restore_round_trip` — FR-F045-05: `deleted_at` set on 40 descendants and cleared; ids unchanged.
- `revision_and_search_written_in_transaction` — FR-F045-13, NFR-F045-04: failing outbox insert rolls back the revision, search upsert, and `current_revision` bump.
- `rollback_drops_tables` — T177: `sqlx migrate revert` removes the three tables, trigger, and indexes.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F045/database/`.
