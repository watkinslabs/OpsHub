# F052 api cases

File: `testing/features/F052/api/{flow_tests.rs,run_tests.rs,scheduler_tests.rs,worker_tests.rs,replay_tests.rs}`. Flag `F052_FEATURE`.

- `flow_create_returns_next_run_at` — FR-F052-01: POST cron flow in `America/New_York` → 201, `version: 1`, `next_run_at` converted to UTC.
- `flow_mapping_rejects_foreign_column` — FR-F052-02: `column_id` from another sheet → 400 `field_errors.mapping[0].column_id`.
- `flow_mapping_coerce_mismatch_invalid` — FR-F052-02: `coerce: number` onto a `date` column → 400 `field_errors.mapping[1].coerce`.
- `flow_update_requires_keys_invalid` — FR-F052-02: `duplicate_strategy: update` with empty `key_column_ids` → 400.
- `flow_schedule_rejects_under_15_minutes` — FR-F052-03: `*/5 * * * *` → 400 `field_errors.schedule.expression = min_interval_15m`.
- `flow_limit_reached_conflicts` — FR-F052-05: fourth flow with `max_flows 3` → 409 `field_errors.flows = limit_reached`.
- `flow_no_entitlement_denied_by_guard` — FR-F052-12: tenant B admin GET flows → 403 `field_errors.module = not_entitled`, handler never ran.
- `flow_editor_without_data_admin_denied` — NFR-F052-02: sheet editor POST flow and run → 403 `denied`.
- `run_request_conflicts_while_active` — FR-F052-06: second run request during `queued` → 409 `field_errors.run = already_active`.
- `run_request_acks_under_2s` — NFR-F052-01: 50 run requests, each 202 in under 2 s.
- `scheduler_claims_due_flow_once` — FR-F052-06: two scheduler instances, one due flow → exactly one run, `next_run_at` advanced.
- `scheduler_records_overlap_skip` — FR-F052-06: due flow with running run → no new run, `skipped_reason = overlap` logged on the schedule.
- `worker_run_applies_update_strategy` — FR-F052-07: 120-row file, 100 keys existing → `rows_updated 100`, `rows_inserted 20`.
- `worker_duplicate_checksum_skips` — FR-F052-07: same checksum → `succeeded`, `skipped_reason = duplicate_file`, row versions unchanged.
- `worker_abort_writes_nothing` — FR-F052-04: 12 rejects, `max_errors 5`, `abort` → `failed`, sheet row count unchanged.
- `worker_partial_commits_valid_rows` — FR-F052-04: same file with `partial` → `partial`, 108 rows written, report file created.
- `worker_file_too_large_fails_fast` — FR-F052-05: 60 MB file with `max_file_mb 50` → `failed`, `error_code = file_too_large`, no job created.
- `worker_sheet_denied_when_owner_lost_access` — FR-F052-13: owner demoted to viewer → run `failed` with `sheet_denied`.
- `worker_archives_with_retain_until` — FR-F052-08: archive row under `shuttle/{tenant}/{flow}/{run}` with `retain_until = completed_at + 30d`.
- `worker_publishes_started_and_completed` — FR-F052-11: outbox holds `shuttle-run.started.v1` then `shuttle-run.completed.v1` with counts.
- `worker_dead_letters_after_three_retries` — NFR-F052-04: storage stub fails four times → run dead-lettered with reason, `shuttle-run.failed.v1`.
- `run_list_pages_newest_first` — FR-F052-10: 1,000 runs, `limit 100`, ten pages, `status` and `since` filters applied.
- `run_detail_hides_urls_without_sheet_read` — NFR-F052-02: caller without sheet read → counts present, `archive_url` and `report_url` absent.
- `replay_purged_archive_conflicts` — FR-F052-09: purged archive → 409 `field_errors.archive = purged`.
- `run_cross_tenant_not_found` — FR-F052-14: tenant B GET run and replay → 404.
- `run_span_carries_ids` — NFR-F052-04: run span has `tenant_id`, `flow_id`, `run_id`, `correlation_id`; `shuttle_run_total{status}` incremented.

Evidence: JUnit output and request logs under `testing/evidence/F052/api/`.
