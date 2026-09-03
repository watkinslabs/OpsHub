# F004 api cases

File: `testing/features/F004/api/{config_tests.rs,outbox_tests.rs,job_tests.rs,telemetry_tests.rs,metrics_tests.rs,health_tests.rs,retention_tests.rs}`. Flag `F004_FEATURE`.

- `secret_reference_resolved_and_redacted` — FR-F004-03: `secret://s3-secret` resolved by each backend; `format!("{:?}")` and captured logs show `[redacted]`.
- `nats_permissions_deny_api_consume` — NFR-F004-02: api credentials subscribing to `jobs.>` are rejected by the server.
- `outbox_enqueue_in_caller_transaction` — FR-F004-05: row invisible before commit, visible after; rollback leaves nothing.
- `invalid_event_name_rejected` — FR-F004-05: `tenant.changed` and `Tenant.Created.V1` → `OutboxError::InvalidName`.
- `relay_publishes_batch_and_marks_published` — FR-F004-06: 1,200 rows → three batches, `published_at` set, three `outbox.published.v1` with `batch_size`.
- `relay_survives_nats_outage` — FR-F004-06: publisher fault for 30 s → `attempts` incremented, `last_error` set, rows kept; recovery publishes once.
- `relay_publishes_once_with_two_instances` — FR-F004-07: two relays over 10,000 rows → JetStream sequence count 10,000, drained < 60 s.
- `enqueue_job_writes_run_and_publishes` — FR-F004-08: `job_runs` queued row and `jobs.<tenant>.sample` message in the same transaction.
- `job_retries_then_dead_letters_without_side_effect` — FR-F004-09: failing handler → attempts 1–5 at the backoff schedule, `dead` status, `dead_letters` row, zero side effects.
- `job_timeout_cancels_and_retries` — FR-F004-09: handler sleeping past timeout → cancelled, `error = timeout`, retried.
- `tenant_quota_limits_concurrency` — FR-F004-09: 150 jobs for one tenant → at most 100 running; 1,001st in a minute waits.
- `duplicate_delivery_is_idempotent` — FR-F004-10: same `job_id` delivered twice → one side effect keyed by `idempotency_key`.
- `enqueue_job_without_tenant_refused` — FR-F004-16: no `TenantScope` → `JobError::MissingTenant`, no row.
- `replay_reenqueues_once` — FR-F004-11: replay sets `replayed_at`, new run attempt 1; second replay → `AlreadyReplayed`.
- `correlation_id_honoured_and_echoed` — FR-F004-12: valid header echoed; missing → UUIDv7 generated and echoed.
- `span_log_and_metric_share_correlation` — FR-F004-12: one request → span, JSON log, and `http_request_duration_seconds` sample with the same id.
- `secrets_absent_from_span_fields` — NFR-F004-02: `RedactionLayer` strips resolved secrets from span fields and log text.
- `metrics_only_on_internal_port` — FR-F004-13: `:9464/metrics` → text; `:8080/metrics` → 404.
- `metric_families_present_after_traffic` — FR-F004-13: after 10 requests and 5 jobs all nine families have samples.
- `healthz_always_ok_while_serving` — FR-F004-14: `/healthz` 200 even with the database down.
- `readyz_reports_failing_component` — FR-F004-14: NATS disconnected → 503 with `components.nats.status = "error"` and reason.
- `readyz_honours_500ms_budget` — FR-F004-14: database check stalled → 503 within 600 ms, reason `timeout`.
- `readyz_bypasses_tenant_gate_and_rate_limit` — FR-F004-14: 100 unauthenticated calls in a second → all 200.
- `readyz_never_exposes_secrets` — NFR-F004-02: report contains no connection strings or keys.
- `sweeper_deletes_only_published_and_old_rows` — NFR-F004-04: unpublished 30-day-old rows survive; published 8-day-old rows deleted.
- `alert_rules_fire_on_pending_outbox` — NFR-F004-04: `promtool test rules` with `outbox_pending_events = 1500` for 5 m fires `OutboxBacklog`.

Evidence: JUnit output and captured logs under `testing/evidence/F004/api/`.
