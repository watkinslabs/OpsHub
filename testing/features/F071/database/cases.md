# F071 database cases

File: `testing/features/F071/database/{migration_tests.rs,constraint_tests.rs,index_tests.rs}`. Flag `F071_FEATURE`.

- `migration_tables_exist_with_constraints` — T281: `migrations`, `migration_sheets`, `migration_column_maps`, and `migration_issues` exist with tenant, version, and audit columns where ticket section 4 specifies them.
- `source_kind_check_rejects_unknown_source` — FR-F071-02: a fifth `source_kind` violates the check constraint.
- `inferred_type_check_admits_exactly_twelve_types` — FR-F071-05: each of the twelve F007 types inserts; a thirteenth is rejected on both `inferred_type` and `target_type`.
- `confidence_bounded_between_zero_and_one` — FR-F071-06: `confidence` of 1.5 violates the check constraint.
- `overridden_map_requires_target_type` — FR-F071-09: `state = 'overridden'` with a null `target_type` is rejected.
- `column_map_unique_per_sheet_and_index` — FR-F071-05: a second row for the same `(sheet_map_id, source_index)` violates the unique key.
- `sheet_unique_per_migration_ordinal_and_source_name` — FR-F071-04: duplicate `ordinal` or duplicate `source_name` within a migration is rejected.
- `issue_kind_check_rejects_unknown_kind` — FR-F071-15: a kind outside the twenty listed is rejected; `severity` outside the three is rejected.
- `sheets_and_maps_and_issues_cascade_on_migration_delete` — FR-F071-11: deleting the `migrations` row removes its sheet, column map, and issue rows.
- `attempt_bounded_to_three` — NFR-F071-04: `attempt = 4` violates the check constraint.
- `cursor_never_exceeds_row_count` — FR-F071-11: `cursor_row_number` above `row_count` is rejected.
- `committed_sheet_count_matches_committed_rows` — FR-F071-10: after each tab flips, the counter equals the count of `committed` sheet rows in the same transaction.
- `blocking_issue_count_recomputed_on_waive` — FR-F071-03: waiving the last blocking issue drops the counter to 0 in the same transaction.
- `resume_claim_uses_committing_partial_index` — FR-F071-11, NFR-F071-01: `EXPLAIN` on the resume claim uses `migration_sheets(state) where state = 'committing'`.
- `issue_panel_query_uses_severity_index` — FR-F071-15: `EXPLAIN` on the grouped panel query uses `migration_issues(migration_id, severity, ordinal)`.
- `concurrency_quota_uses_partial_index` — FR-F071-03: `EXPLAIN` on the in-flight count uses `migrations(tenant_id) where status in ('analyzing','committing')`.
- `expiry_sweep_uses_terminal_index` — NFR-F071-02: `EXPLAIN` on the cleanup sweep uses `migrations(expires_at)` restricted to terminal statuses.
- `rollback_drops_migration_tables` — T281: `sqlx migrate revert` removes the four tables and their indexes.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F071/database/`.
