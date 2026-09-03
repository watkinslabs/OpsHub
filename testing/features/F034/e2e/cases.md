# F034 e2e cases

File: `testing/features/F034/e2e/{balancing_spec.ts,time_entry_spec.ts,reconcile_spec.ts,effort_spec.ts,permission_spec.ts}` driving the real API, worker, and database. Flag `F034_FEATURE`.

- `manager_shifts_allocation_and_conflict_resolves` — FR-F034-01, FR-F034-02, FR-F034-03, FR-F034-13: manager opens `/w/{id}/workload`, sees Ana's `Over 137.5%` cell for the week of 2026-10-12, opens `Conflicts`, applies `Shift "Design API"`, and after the recompute the conflict shows `resolved` and the cell drops to `ok`.
- `manager_reassigns_to_candidate_with_remaining_hours` — FR-F034-03, FR-F034-13: `Reassign to Ben (12 h remaining)` moves the allocation through the F033 API and Ben's cell rises while Ana's conflict closes.
- `engineer_records_six_hours_on_a_task` — FR-F034-04, FR-F034-11: engineer opens `/w/{id}/time`, enters 6 h on `Design API` for today, saves, sees the toast, and the entry appears with `source: native` and an audit row.
- `engineer_cannot_edit_an_entry_past_the_lock_window` — FR-F034-05: a 31-day-old entry is read-only with the lock hint and the API returns `denied` when forced.
- `admin_imports_then_reconciles_pending_entry` — FR-F034-06, FR-F034-07, FR-F034-08: admin imports a timesheet with one colliding row, the queue shows one pending entry, `Accept external` with reason `Timesheet system is authoritative` supersedes the native entry, and the queue clears.
- `repeat_import_updates_instead_of_duplicating` — FR-F034-06: re-uploading the same file leaves the entry count unchanged and reports `updated`.
- `planned_versus_actual_visible_on_task_row` — FR-F034-09, FR-F034-10: the `Effort` tab on `Design API` shows planned, actual, pending external, remaining, and variance, and refreshes within 60 s of the new entry.
- `viewer_sees_workload_without_import_or_costs` — FR-F034-12, NFR-F034-02: a `resource-viewer` reaches the heatmap and conflicts but has no import or reconcile entry point and no cost columns.
- `non_viewer_sees_only_their_own_workload_row` — FR-F034-12: a plain member loads `/w/{id}/workload` and sees one row, their own.
- `cross_tenant_effort_read_returns_not_found` — FR-F034-12: a tenant B user requesting a tenant A row effort URL lands on the not-found view.
- `heatmap_and_queue_recover_after_worker_restart` — NFR-F034-04: the detector is restarted mid-span and the heatmap converges with no duplicate conflicts or events.

Evidence: traces, screenshots, and API logs under `testing/evidence/F034/e2e/`.
