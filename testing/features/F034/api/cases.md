# F034 api cases

File: `testing/features/F034/api/{workload_tests.rs,conflict_tests.rs,time_entry_tests.rs,import_tests.rs,reconcile_tests.rs,effort_tests.rs,negative_tests.rs}`. Flag `F034_FEATURE`.

- `workload_rows_carry_utilization_and_status` — FR-F034-01: 16 available and 22 allocated → `utilization_pct` 137.5 and `status: over`; 10 of 16 → `ok`; 4 of 16 → `under`.
- `utilization_is_null_when_available_is_zero` — FR-F034-01: no capacity in the period → `utilization_pct: null`, `status: no_capacity`.
- `workload_range_over_182_days_is_invalid` — FR-F034-01: 183-day range → 400 `invalid` from `WorkloadError::RangeTooLarge`; 182 days succeeds.
- `workload_over_500_resources_is_invalid` — FR-F034-01: 501 resolved resources → 400 `invalid`; 500 succeeds.
- `workload_row_reports_stale_when_source_event_queued` — FR-F034-10: unprocessed `allocation.updated.v1` → row carries `stale: true`.
- `capacity_event_opens_conflict_with_over_hours` — FR-F034-02: `capacity.computed.v1` → `workload_conflicts` row with `over_hours` 6 and the two contributing `allocation_ids`, `workload-conflict.detected.v1` published once.
- `conflict_detection_is_idempotent_per_source_version` — NFR-F034-04: replayed event → one row, no second event.
- `resolved_period_sets_resolved_at_and_stops_publishing` — FR-F034-02: capacity raised to 24 h → `status: resolved`, `resolved_at` set, no new event.
- `conflict_lists_shift_and_reassign_suggestions` — FR-F034-03: `Design API` float 4 d → `shift_within_float`; Ben with 12 h remaining → `reassign_to`.
- `reassign_candidates_capped_at_three_by_remaining_hours` — FR-F034-03: five matching resources → the three with the largest `remaining_hours`, descending.
- `time_entry_create_stores_native_source_and_cost_snapshot` — FR-F034-04: 6 h on `Design API` → 201, `source: native`, `cost_snapshot` from the effective rate, `time-entry.recorded.v1`.
- `time_entry_rejects_non_quarter_hours_and_future_dates` — FR-F034-04: 6.1 h → 400 `invalid`; tomorrow in the tenant zone → 400 `invalid` from `TimeEntryError::FutureDate`.
- `time_entry_daily_cap_rejects_over_24_hours` — FR-F034-04: 20 h recorded then 5 h → 400 `invalid` with `field_errors.hours`.
- `time_entry_patch_requires_if_match` — FR-F034-05: stale `If-Match` → 409 `conflict` from `TimeEntryError::StaleVersion`.
- `locked_entry_denies_owner_but_allows_admin` — FR-F034-05: entry 31 days old → owner 403 `denied`, `resource-admin` 200.
- `patch_of_external_entry_returns_external_entry_conflict` — FR-F034-05: → 409 `conflict` with `code_detail: external_entry`.
- `import_is_idempotent_per_external_id` — FR-F034-06: same `(source_system, external_id)` twice → `created` 1 then `updated` 1, one row.
- `import_rejects_bad_rows_by_index_only` — FR-F034-06, NFR-F034-02: foreign-tenant `resource_id` at index 7 → that index in `rejected`, the rest created.
- `imported_entry_colliding_with_native_is_pending` — FR-F034-07: 8 external hours over Ana's 6 native hours → `pending`, `actual_hours` stays 6, `pending_external_hours` 8.
- `import_never_mutates_native_entries` — FR-F034-07: native row version and hours unchanged after import.
- `accept_external_supersedes_native_and_audits` — FR-F034-08, FR-F034-14: native `superseded` with `superseded_by`, external `accepted`, `actual_hours` 8, audit and `time-entry.reconciled.v1` carry `resolution` and `reason`.
- `keep_native_rejects_external_and_sum_counts_both` — FR-F034-08: `keep_native` → external `rejected`, actuals 6; `sum` → actuals 14.
- `reconcile_reason_must_be_ten_to_thousand_chars` — FR-F034-08: 9 characters → 400 `invalid`.
- `reconcile_on_accepted_entry_is_conflict` — FR-F034-08: non-pending entry → 409 `conflict` from `TimeEntryError::NotPending`.
- `row_effort_returns_planned_actual_and_variance` — FR-F034-09: planned 40, actual 8 → `remaining_hours` 32, `variance_hours` −32, `by_resource` populated; `include_children=true` adds descendants.
- `effort_costs_hidden_for_non_admin` — FR-F034-09, NFR-F034-02: viewer response has no `planned_cost` or `actual_cost`.
- `mutation_without_idempotency_key_is_invalid` — FR-F034-11: create, patch, delete, import, and reconcile without the header → 400 `invalid`.
- `viewer_cannot_import_or_reconcile` — FR-F034-12: `resource-viewer` POST import and reconcile → 403 `denied`, no rows change.
- `user_cannot_patch_another_users_entry` — FR-F034-12: → 403 `denied`.
- `foreign_tenant_time_entry_is_not_found` — FR-F034-12: tenant B entry, conflict, and row effort ids → 404 `not_found`.
- `time_entry_note_absent_from_log_fields` — NFR-F034-02: captured log records contain `time_entry_id` but never the note text.

Evidence: JUnit output and outbox recordings under `testing/evidence/F034/api/`.
