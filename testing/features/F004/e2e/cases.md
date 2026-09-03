# F004 e2e cases

File: `testing/features/F004/e2e/{stack.spec.rs,restore_drill.spec.rs}`. Boots the real compose stack in the `ci` profile. Flag `F004_FEATURE`.

- `compose_stack_healthy_within_120s` — FR-F004-01: `make up` on a clean runner reaches healthy for all eight services; `/readyz` returns 200 with every component `ok`.
- `compose_services_non_root_read_only` — FR-F004-04, NFR-F004-02: `docker inspect` shows uid 65532 and `ReadonlyRootfs = true` for api, worker, realtime, web.
- `event_round_trip_api_to_worker` — FR-F004-05, FR-F004-06: `POST /api/v1/tenants` → outbox row → JetStream message on `events.<tenant>.tenant.created.v1` consumed by the worker within 2 s.
- `worker_sigkill_redelivers_within_30s` — FR-F004-10: `docker kill -s KILL` the worker mid-job; a second worker receives `attempt = 2` within 30 s; one side effect.
- `worker_sigterm_drains_and_exits_zero` — FR-F004-10: `docker stop` with an in-flight 10 s job → job completes, exit code 0 within 30 s.
- `metrics_unreachable_through_proxy` — FR-F004-13: `GET http://web/metrics` and `http://api:8080/metrics` → 404; `http://api:9464/metrics` on the internal network → 200.
- `backup_then_restore_drill_matches_manifest` — FR-F004-15: `make backup-now`, insert rows, `make restore-drill --target-time` before the insert → counts match the manifest, exit 0.
- `restore_to_timestamp_excludes_later_rows` — FR-F004-15, NFR-F004-04: rows inserted after the target timestamp are absent from the scratch database.

Evidence: compose logs, `docker inspect` output, and restore-drill transcript under `testing/evidence/F004/e2e/` and `testing/evidence/F004/restore-drill/`.
