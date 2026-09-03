# F019 api cases

File: `testing/features/F019/api/{queue_tests.rs,idempotency_tests.rs,retry_tests.rs,run_query_tests.rs}`. Flag `F019_FEATURE`. Worker runs in-process against embedded JetStream.

- `row_event_enqueues_one_run` — FR-F019-01: `row.updated.v1` changing `Status` → one `queued` run pinned to `workflow_version_id`, `workflow-run.queued.v1` published.
- `non_matching_event_creates_no_run` — FR-F019-01: event changing `Due` for a `field_changed(Status)` workflow → zero runs.
- `duplicate_event_delivery_creates_no_second_run` — FR-F019-02: same `trigger_event_id` twice → one row, same id returned.
- `schedule_tick_fires_due_trigger_once` — FR-F019-03: clock past three 5-minute windows → one run; `next_fire_at` moves forward.
- `date_reached_offset_fires_before_due` — FR-F019-03: `Due` = tomorrow 09:00, `offset_minutes: -60` → run at 08:00 local time.
- `inbound_webhook_bad_signature_denied` — FR-F019-04: wrong `X-OpsHub-Signature` → 403 `denied`, no run.
- `inbound_webhook_replayed_delivery_returns_original_run` — FR-F019-04: same `X-OpsHub-Delivery-Id` → 200 with the first `run_id`.
- `inbound_webhook_rate_limited_after_sixty` — FR-F019-04: 61st request in a minute → 429 `rate_limited`.
- `inbound_webhook_body_over_256kb_invalid` — FR-F019-04: 257 KB body → 400 `invalid`.
- `run_executes_steps_in_order` — FR-F019-05: 3 steps → step rows `index` 0..2 with `completed`, `workflow-run.started.v1` then `workflow-run.completed.v1`.
- `continue_on_error_records_skipped_step` — FR-F019-05: step 2 fails with `continue_on_error: true` → `skipped_error`, run `completed`.
- `backoff_schedule_caps_at_fifteen_minutes` — FR-F019-06: attempts 1..5 delays within `[base, base*1.2]` and never above 15 min.
- `fifth_failure_dead_letters_run` — FR-F019-06: 5 failures → `dead_lettered`, `workflow-run.dead-lettered.v1`.
- `step_timeout_counts_as_failed_attempt` — FR-F019-07: executor sleeps 31 s → `timeout`, `attempt: 1`, retry scheduled.
- `run_timeout_aborts_after_120s` — FR-F019-07: 5 steps of 30 s → aborted after 120 s with `timeout`.
- `quota_holds_excess_runs_queued` — FR-F019-08: 150 runs → 100 `running`, 50 `queued`; tenant B run dequeued meanwhile.
- `executor_attempt_key_prevents_double_side_effect` — FR-F019-09: executor invoked twice for `(run, 0, 1)` → one row update.
- `nested_run_depth_six_loop_detected` — FR-F019-10: self-triggering workflow → depth 5 allowed, depth 6 `loop_detected`.
- `run_list_filters_by_status_and_window` — FR-F019-11: 500 runs, `limit=100`, `filter[status]=failed`, `started_after`.
- `run_detail_returns_ordered_steps` — FR-F019-11: detail includes steps by `index` with `output` and `error`.
- `retry_dead_lettered_run_requeues_from_failed_step` — FR-F019-12: retry → `queued`, steps before the failure not re-run.
- `cancel_running_run_stops_at_step_boundary` — FR-F019-12: cancel during step 1 → step 1 completes, step 2 never starts, `cancelled`.
- `cancel_completed_run_conflicts` — FR-F019-12: cancel on `completed` → 409 `conflict`.
- `disable_cancels_running_run_after_step` — FR-F019-13: `workflow.disabled.v1` mid-run → `cancelled` with `workflow_disabled`; new events create no runs.
- `transitions_emit_events_and_audit` — FR-F019-14: each transition → one `workflow-run.*.v1` and one audit row with both actors.
- `reaper_fails_stale_heartbeat_run` — NFR-F019-04: run with no heartbeat for 5 min → failed attempt and retry scheduled.
- `service_actor_scope_denied_outside_sheet` — NFR-F019-02: `update_fields` on another sheet → step `denied`, run `failed`.
- `run_cross_tenant_not_found` — NFR-F019-02: tenant B on every run route → 404.
- `viewer_retry_denied` — FR-F019-14: workflow viewer retry/cancel → 403 `denied`.
- `ack_after_commit_survives_crash` — NFR-F019-04: worker killed between commit and ack → redelivery creates no second run.

Evidence: JUnit output and JetStream consumer info under `testing/evidence/F019/api/`.
