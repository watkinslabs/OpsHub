# F011 database cases

File: `testing/features/F011/database/migration_tests.rs`. Flag `F011_FEATURE`.

- `schedule_tables_exist_with_constraints` — T041: `working_calendars`, `calendar_exceptions`, `sheet_schedule_settings` exist with tenant, version, audit, and soft-delete columns.
- `second_default_calendar_rejected` — FR-F011-03: inserting a second `is_default` calendar for a tenant violates `working_calendars_tenant_default_idx`.
- `duplicate_calendar_name_rejected` — FR-F011-02: case-insensitive duplicate name blocked while `deleted_at is null`; allowed after soft delete.
- `exception_date_unique_per_calendar` — FR-F011-04: duplicate `(calendar_id, date)` rejected; cascade delete removes exceptions with the calendar.
- `hours_per_day_check_constraint` — FR-F011-02: `0.25` and `25` rejected by the check constraint.
- `settings_restrict_calendar_delete` — FR-F011-03: hard delete of a calendar referenced by `sheet_schedule_settings` fails with `on delete restrict`.
- `exceptions_index_used_for_range_scan` — NFR-F011-01: `EXPLAIN` on a date-range query uses `calendar_exceptions_calendar_date_idx`.
- `audit_and_outbox_rows_written_in_transaction` — FR-F011-11: failing outbox insert rolls back the calendar write.
- `rollback_drops_tables` — T041: `sqlx migrate revert` removes the three tables and indexes.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F011/database/`.
