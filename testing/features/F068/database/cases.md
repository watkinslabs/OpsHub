# F068 database cases

Everything a type cannot enforce is proved here against a throwaway PostgreSQL 18: one `postgres:18` container per test session, database `opshub_f068_w{worker}` per worker, F002 `*_tenants_*.sql`, F003 `*_authz_*.sql`, and F004 `*_runtime_*.sql` applied at setup and dropped at teardown. This feature adds no migration of its own; the last three cases are the negative controls that keep it that way. Files: `testing/features/F068/database/{scope_tests.rs,version_tests.rs,atomicity_tests.rs,pagination_tests.rs,purge_tests.rs,conformance_tests.rs,schema_expectations_tests.rs,no_migration_tests.rs}`. Flag `F068_FEATURE`.

- `get_across_tenants_is_not_found` — FR-F068-04, NFR-F068-02: tenant B's user id read with tenant A's `TenantCtx` returns `NotFound`, with the same error and the same shape as a missing id.
- `list_hides_soft_deleted_rows_by_default` — FR-F068-04: three of ten users soft-deleted; `list` returns seven, `Visibility::Deleted` returns three, `Visibility::Any` returns ten.
- `update_across_tenants_is_not_found_and_writes_nothing` — FR-F068-04, NFR-F068-02: a cross-tenant update leaves the row, its version, and both audit and outbox tables unchanged.
- `update_with_stale_version_conflicts_and_writes_nothing` — FR-F068-05: a user at version 4 updated with expected 3 yields `VersionConflict { expected: 3, actual: 4 }`; row counts in `users`, `audit_events`, and `outbox_events` are unchanged.
- `concurrent_updates_leave_exactly_one_conflict` — FR-F068-05: two tasks update the same row from version 4; one returns version 5, the other `VersionConflict`, under `read committed` with no explicit lock.
- `restore_requires_a_deleted_row_and_bumps_the_version` — FR-F068-05: restoring a live row is `NotFound`; restoring a deleted one clears `deleted_at` and returns the next version.
- `insert_writes_audit_and_outbox_rows_in_one_transaction` — FR-F068-06: one `insert` yields one `users` row, one `audit_events` row with `action` `user.create` and a `before` of null, and one `outbox_events` row with `user.created.v1` and the specification payload.
- `rollback_removes_write_audit_and_outbox_together` — FR-F068-06, NFR-F068-04: a `UnitOfWork` updates a user then inserts a group member that violates a constraint; after rollback all three tables hold their original counts and the publisher sees no event.
- `replayed_idempotency_key_returns_first_entity` — FR-F068-08: the same key submitted twice yields one `users` row, one outbox row, and the first entity returned both times.
- `purge_removes_children_and_audits_the_pre_image` — FR-F068-09: purge with a verified grant removes the row and its `CO_TABLES` children, writes one audit row carrying the full pre-image, and writes no outbox row.
- `purge_without_the_scope_is_forbidden` — FR-F068-09: `PurgeGrant::verify` without `purge:user` returns `Forbidden` and nothing is deleted.
- `unit_of_work_shares_one_transaction_across_two_repositories` — FR-F068-11: a user update and a group-member insert are visible to each other before commit and invisible to a second connection until commit.
- `pool_handle_commits_its_own_single_write` — FR-F068-12: a `Database::repo` write is durable without a `UnitOfWork`, and its audit and outbox rows land with it.
- `repository_never_begins_a_nested_transaction` — FR-F068-12: `pg_stat_activity` and a statement log show one `begin` per unit of work; the transaction handle issues none.
- `keyset_paging_is_stable_under_concurrent_insert` — FR-F068-10: paging 100,000 users at limit 50 while inserting returns no duplicate and skips no pre-existing row, because the predicate is `(display_name, id) > ($k, $id)`.
- `cursor_from_other_tenant_is_rejected` — FR-F068-10, NFR-F068-02: a cursor minted for tenant A presented with tenant B returns `InvalidCursor` and no row.
- `cursor_with_changed_filter_is_rejected` — FR-F068-10: the same cursor under `status = invited` instead of `status = active` returns `InvalidCursor` through the `filter_hash` mismatch.
- `every_registered_spec_passes_the_eight_case_suite` — NFR-F068-05: the link-time registry is iterated and each specification runs cross-tenant read, cross-tenant write, soft-delete filter, version conflict, audit row, outbox row, rollback atomicity, and cursor rejection; the per-specification matrix is written to evidence.
- `outbox_idempotency_index_exists` — FR-F068-08: `outbox_events_tenant_idempotency_idx` on `(tenant_id, idempotency_key)` is asserted, not created; its absence fails this feature rather than silently disabling idempotency.
- `feature_adds_no_migration_file` — FR-F068-14: `services/api/migrations/` contains no `*_persistence_*.sql`, and `cargo xtask check-migrations` reports the same file count before and after this branch.
- `gate_opens_no_database_connection` — NFR-F068-02: `check-persistence` runs with `OPSHUB_DATABASE_URL` unset and a loopback listener on the configured PostgreSQL port that fails the test if it accepts a connection.

Evidence: container logs, statement logs, the conformance matrix, and JUnit output under `testing/evidence/F068/database/`.
