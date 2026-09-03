# F057 database cases

File: `testing/features/F057/database/migration_tests.rs`. Flag `F057_FEATURE`.

- `asset_tables_exist_with_constraints` — T225: five tables exist with tenant, version, audit, and archive columns.
- `duplicate_rendition_kind_rejected` — FR-F057-03: second `(asset_id, file_version_id, kind)` violates the unique index.
- `collection_depth_six_rejected` — FR-F057-08: `depth = 6` violates the check constraint.
- `duplicate_collection_name_per_parent_rejected` — FR-F057-08: case-insensitive duplicate under the same parent blocked while `deleted_at is null`.
- `search_vector_generated_and_indexed` — FR-F057-07: `EXPLAIN` on `q` filter uses the GIN index; tags are searchable.
- `rights_license_check_constraint` — FR-F057-05: `license = 'unknown'` rejected.
- `rendition_requires_existing_asset` — FR-F057-03: foreign key rejects orphan renditions; `on delete restrict` blocks hard delete.
- `archive_keeps_collection_items` — FR-F057-09: setting `archived_at` leaves `asset_collection_items` intact.
- `rollback_drops_tables` — T225: `sqlx migrate revert` removes the five tables and indexes.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F057/database/`.
