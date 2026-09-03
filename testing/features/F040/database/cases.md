# F040 database cases

File: `testing/features/F040/database/{migration_tests.rs,constraint_tests.rs,index_tests.rs}`. Flag `F040_FEATURE`.

- `ai_insights_tables_exist_with_constraints` — T157: `ai_insights`, `ai_insight_evidence`, `ai_actions`, `ai_action_runs` exist with tenant, version, and audit columns where specified.
- `evidence_count_check_rejects_zero` — FR-F040-03: inserting an insight with `evidence_count = 0` violates the check; an evidence-less insight is unrepresentable.
- `confidence_bounded_zero_to_one` — FR-F040-07: `confidence 1.01` violates the check; `0.00` and `1.00` are accepted.
- `open_fingerprint_unique_per_tenant` — FR-F040-05: a second `open` insight with the same `(tenant_id, fingerprint)` is rejected; allowed once the first is `dismissed`.
- `evidence_unique_per_source_and_column` — FR-F040-03: duplicate `(insight_id, source_kind, source_id, column_id)` rejected.
- `evidence_cascades_on_insight_delete` — FR-F040-03: deleting the insight removes its evidence rows.
- `action_target_count_bounded_one_to_twenty_five` — FR-F040-09: `target_count 0` and `26` violate the check.
- `confirmed_action_requires_confirmed_by` — FR-F040-11: setting `status = 'confirmed'` with a null `confirmed_by` violates the check.
- `action_run_idempotency_key_unique_per_tenant` — NFR-F040-04: a replayed key is rejected; `(action_id, attempt)` is also unique.
- `runs_cascade_on_action_delete` — FR-F040-13: deleting the action removes its run rows.
- `insight_list_index_used` — NFR-F040-01: `EXPLAIN` for the default list uses `ai_insights(tenant_id, status, severity desc, last_seen_at desc)`.
- `suppression_lookup_uses_partial_index` — FR-F040-08: `EXPLAIN` for the suppression check uses the partial index on `suppressed_until`.
- `rollback_drops_ai_insights_tables` — T157: `sqlx migrate revert` removes the four tables and their indexes.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F040/database/`.
