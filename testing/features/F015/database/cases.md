# F015 database cases

File: `testing/features/F015/database/{migration_tests.rs,baseline_tests.rs}`. Flag `F015_FEATURE`.

- `template_tables_exist_with_constraints` — T057: `project_templates`, `template_versions`, `provisioning_runs`, `baselines`, `baseline_rows` exist with tenant, version, audit, and soft-delete columns.
- `published_version_update_raises` — FR-F015-04: `UPDATE template_versions SET manifest = ...` on a published row raises from `template_versions_immutable`; drafts update normally.
- `version_number_unique_per_template` — FR-F015-02: duplicate `(template_id, version_number)` rejected.
- `manifest_bytes_check_constraint` — FR-F015-03: `manifest_bytes = 2097153` rejected.
- `builtin_seed_has_ten_published_templates` — FR-F015-05: reserved tenant holds exactly ten `is_builtin` templates, each with one published version and `current_version_id` set.
- `duplicate_template_name_rejected` — FR-F015-01: case-insensitive duplicate blocked while `deleted_at is null`.
- `baseline_rows_cascade_with_baseline` — FR-F015-11: hard delete of a baseline removes its `baseline_rows`; `sheets` restrict blocks sheet hard delete while baselines exist.
- `active_runs_partial_index_used` — NFR-F015-04: `EXPLAIN` on `status in ('queued','running')` uses `provisioning_runs_active_idx`.
- `audit_and_outbox_rows_written_in_transaction` — FR-F015-13: failing outbox insert rolls back the baseline capture.
- `rollback_drops_tables_and_trigger` — T057: `sqlx migrate revert` removes the five tables, indexes, trigger, and seed rows.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F015/database/`.
