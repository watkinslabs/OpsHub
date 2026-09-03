# F029 database cases

File: `testing/features/F029/database/{migration_tests.rs,constraint_tests.rs}`. Flag `F029_FEATURE`.

- `integrations_tables_exist_with_constraints` — T113: `integration_connections`, `oauth_tokens`, `oauth_states`, `integration_events`, `calendar_bindings`, `calendar_event_links` exist with tenant, version, and audit columns where specified.
- `one_token_row_per_connection` — FR-F029-04: second `oauth_tokens` row for a connection violates the primary key.
- `oauth_tokens_cascade_on_connection_delete` — FR-F029-06: deleting the connection row removes its token row.
- `refresh_failures_bounded` — FR-F029-05: `refresh_failures 4` violates the check constraint.
- `one_active_binding_per_sheet` — FR-F029-10: second `active` binding on the same sheet rejected; allowed when the first is `paused`.
- `event_link_unique_per_binding_row` — FR-F029-10: duplicate `(binding_id, row_id)` rejected; lookup by `external_event_id` uses its index.
- `events_index_used_for_connection_log` — NFR-F029-04: `EXPLAIN` on the last 50 events uses `integration_events(connection_id, occurred_at desc)`.
- `expired_states_cleaned` — FR-F029-02: nightly cleanup removes `oauth_states` past `expires_at`.
- `rollback_drops_integrations_tables` — T113: `sqlx migrate revert` removes the six tables and indexes.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F029/database/`.
