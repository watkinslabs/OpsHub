# F054 api cases

File: `testing/features/F054/api/{flow_tests.rs,run_tests.rs,retry_tests.rs,failure_tests.rs}`. Flag `F054_FEATURE`.

- `flow_create_requires_single_trigger` — FR-F054-01: zero or two `trigger` steps → 400 `invalid`, `field_errors.steps`.
- `flow_rejects_51_steps` — FR-F054-01: 51 steps → 400; 50 steps → 201.
- `flow_schedule_interval_under_5_minutes_invalid` — FR-F054-02: cron every 4 minutes → 400 `field_errors.steps[0].config.schedule`.
- `flow_publish_denies_foreign_connection` — FR-F054-03: connection owned by another user without ACL → 403 with `field_errors.steps[1].config.connection_id`.
- `flow_publish_rejects_cycle` — FR-F054-04: last step `next` = step 2 → 409 `field_errors.steps = cycle`, no version row.
- `flow_transform_over_500_nodes_invalid` — FR-F054-04: 501-node expression → 400.
- `flow_publish_creates_immutable_version` — FR-F054-05: publish twice → versions 1 and 2; patching the draft does not change snapshot 2.
- `flow_limit_exceeded_conflicts` — FR-F054-13: 11th flow with `max_flows 10` → 409 `field_errors.limit`.
- `bridge_route_denied_without_entitlement` — FR-F054-13: suspended entitlement → every route 403 `field_errors.module = suspended`.
- `run_enqueue_is_idempotent_by_key` — FR-F054-06: same `idempotency_key` twice → same `run_id`, one row.
- `run_unpublished_flow_conflicts` — FR-F054-06: draft-only flow → 409.
- `run_quota_exceeded_rate_limited` — FR-F054-06: 101st run in a day with `max_runs_per_day 100` → 429.
- `executor_runs_five_steps_in_order` — FR-F054-07, FR-F054-12: seeded flow → five `succeeded` step rows, events in order.
- `executor_retries_rate_limited_then_fails_step` — FR-F054-07: mock returns `rate_limited` four times → attempts 3, step `failed`, run `failed`, `bridge-run.failed.v1`.
- `executor_redacts_secrets_in_snapshots` — FR-F054-08: `authorization` and `api_token` keys → `***` in `bridge_run_steps` and event payload.
- `executor_truncates_large_snapshot` — NFR-F054-02: 300 KB output → stored 256 KB with `truncated: true`.
- `branch_follows_matching_condition` — FR-F054-04: `priority = high` → Jira path; otherwise → Slack path.
- `wait_approval_resumes_on_decision` — FR-F054-09: run `waiting`; `approval.decided.v1` approved → resumes and completes.
- `step_rechecks_connection_access` — NFR-F054-02: connection revoked after publish → step `denied`, run `failed`.
- `retry_step_resumes_downstream` — FR-F054-10: retry failed Slack step → succeeded, downstream update-field step runs.
- `retry_non_failed_step_conflicts` — FR-F054-10: retry a `succeeded` step → 409.
- `retry_viewer_denied` — FR-F054-14: viewer retry and run → 403.
- `run_list_filters_by_status_and_flow` — FR-F054-11: 200 runs, `status=failed&flow_id` → only matching, cursor pages of 50.
- `run_cross_tenant_not_found` — FR-F054-14: tenant B GET run and retry → 404.
- `step_timeout_marks_failed` — NFR-F054-04: step with `timeout_secs 5` and hanging mock → `failed` with `error_code timeout`.
- `quota_exhaustion_dead_letters_run` — NFR-F054-04: tenant quota zero → run in F019 dead letters, `bridge-run.failed.v1`.
- `redelivered_message_creates_no_duplicate_steps` — NFR-F054-04: same JetStream message twice → one step row per attempt.
- `run_span_carries_ids_and_metrics` — NFR-F054-04: span has `run_id`, `step_id`; `bridge_step_retry_total{action="slack.post_message"}` incremented.

Evidence: JUnit output and request logs under `testing/evidence/F054/api/`.
