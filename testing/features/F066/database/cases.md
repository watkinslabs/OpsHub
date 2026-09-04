# F066 database cases

F066 adds no migration, no table, and no query. This lane is therefore a set of negative controls that keep it that way: the gate must stay a file-and-metrics reader, and the only durable state it produces must remain the two files named in the ticket. File: `testing/features/F066/database/no_persistence_tests.rs`. Flag `F066_FEATURE`.

- `no_slo_migration_file_exists` — NFR-F066-02: `services/api/migrations/` contains no `*_slo_*.sql` file, and `cargo xtask check-migrations` reports the same file count before and after the feature branch.
- `verify_slo_opens_no_database_connection` — NFR-F066-02: static and `--budget` runs execute with `OPSHUB_DATABASE_URL` unset and with a loopback listener bound on the configured PostgreSQL port that fails the test if it accepts a connection.
- `no_domain_table_is_referenced` — NFR-F066-02: `automation/xtask/src/slo.rs` contains no SQL string, no `sqlx` import, and no reference to `outbox_events`, `job_runs`, or `dead_letters`; the objectives read metric names only.
- `durable_state_is_two_files_only` — FR-F066-14: after a full `--budget` run in a temporary tree, the only changed paths are `infra/slo/exceptions.yml` (when an exception is edited) and `testing/evidence/F066/slo-report.json`.
- `report_carries_no_tenant_or_user_identifier` — NFR-F066-02: `slo-report.json` from every window fixture is scanned for UUIDs, email addresses, and `tenant_id`; none are present, because the recording rules aggregate them away.
- `exceptions_file_round_trips_without_a_store` — NFR-F066-05: an exception written by hand is read back with owner, ticket, reason, and expiry intact; there is no database row, cache, or shadow registry behind it.
- `evidence_directory_is_the_only_write_target` — NFR-F066-02: a run with `infra/` mounted read-only still succeeds in `--budget` mode and fails with exit 2 in `--write-rules` mode, proving the write set is exactly the declared one.

Evidence: file-system diffs, the migration count, and connection-attempt logs under `testing/evidence/F066/database/`.
