# F061 database cases

File: `testing/features/F061/database/{migration_tests.rs,constraint_tests.rs}`. Flag `F061_FEATURE`.

- `update_request_tables_exist_with_constraints` — T241: `update_requests`, `update_request_recipients`, `update_request_responses`, and `reminder_schedules` exist with tenant, version, and audit columns and the status check constraints.
- `token_hash_unique_where_present` — FR-F061-02: a duplicate `token_hash` is rejected; two recipients with null `token_hash` after revocation coexist.
- `recipient_unique_per_party` — FR-F061-01: the same `user_id` twice on one request is rejected, and so is the same email in different letter case.
- `scope_bounds_enforced_by_check` — FR-F061-01: `row_ids` of length 0 or 201 and `column_ids` of length 21 violate the array-length checks.
- `expiry_after_due_date_enforced` — FR-F061-02: `expires_at <= due_at` violates the check constraint.
- `responses_append_only_trigger_blocks_payload_update` — FR-F061-06: updating `payload` or `received_at` raises; `received → applied` with `cells_applied` succeeds; `applied → received` raises.
- `response_idempotency_unique_per_request` — FR-F061-06: a second row with the same `(tenant_id, request_id, idempotency_key)` is rejected.
- `reminder_sequence_unique_per_recipient` — FR-F061-10: a duplicate `(recipient_id, sequence)` is rejected, which is what makes the job safe to re-run.
- `pending_reminder_index_used_for_claim` — NFR-F061-01: `EXPLAIN` on the claim query uses `reminder_schedules(state, next_run_at) where state = 'pending'`.
- `recipients_and_responses_cascade_on_request_delete` — FR-F061-12: deleting the request removes its recipients, responses, and schedules.
- `rollback_drops_update_request_tables` — T241: `sqlx migrate revert` removes the four tables, their indexes, and the append-only trigger.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F061/database/`.
