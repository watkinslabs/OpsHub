---
id: S103
type: story
status: planned
parent_epic: E008
parent_feature: F052
depends_on: [F010, F048]
owned_paths: [crates/domain/src/data-shuttle/**, crates/persistence/src/data-shuttle/**, services/api/src/data-shuttle/**, services/worker/src/data-shuttle/**, services/api/migrations/*_data-shuttle_*.sql, testing/features/F052/**]
feature_flag: F052_FEATURE
branch: s103-scheduled-file-flows
started_at: null
finished_at: null
---

# S103 — Scheduled file flows

## Identity

- Parent feature: `F052` Data Shuttle
- Owner: platform
- Branch: `s103-scheduled-file-flows`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 7, 10; `docs/capability-contracts.md` row F052

## Vertical slice

As a data administrator, I want to define an import or export flow with a file location, sheet, mapping, validation, and cron schedule, and have a worker pick up the file on time, validate it, write it through the F010 job path, and archive it, so that recurring extracts land in sheets without manual imports.

Out of this slice: run history browsing, replay, archive download UI, and the flow editor screens (S104); connector authentication (F029); sheet-to-sheet sync (F053).

## Requirements

- **SR-S103-01:** `POST /api/v1/data-shuttle/flows` and `PATCH /api/v1/data-shuttle/flows/{id}` persist `direction`, `location`, `sheet_id`, `mapping`, `validation`, `schedule`, and `archive_policy` through `ShuttleFlowRepository` and `ShuttleScheduleRepository` in one `UnitOfWork` — the flow row plus one `shuttle_flow_column_maps` row per mapped column, one `shuttle_flow_key_columns` row per key, one `shuttle_flow_required_columns` row per required column, and the `shuttle_schedules` row for a cron flow — return `FlowResponse` with the JSON `mapping`/`validation`/`location` objects reassembled from those rows plus `version` and `next_run_at`, and reject invalid mapping, coercion, and schedule with `400 invalid` and typed `field_errors` (covers FR-F052-01, FR-F052-02, FR-F052-03).
- **SR-S103-02:** Creating a flow past the `max_flows` limit from the F048 entitlement returns `409 conflict` with `field_errors.flows = "limit_reached"`; every route is behind `RequireModule(ModuleSlug::DataShuttle)` (FR-F052-05, FR-F052-12).
- **SR-S103-03:** `POST /api/v1/data-shuttle/flows/{id}/run` returns `202` with a `queued` run within 2 seconds and returns `409 conflict` with `field_errors.run = "already_active"` while a run is queued or running (FR-F052-06, NFR-F052-01).
- **SR-S103-04:** The scheduler claims due `shuttle_schedules` rows every 60 seconds through `ShuttleScheduleRepository::claim_due_schedules`, which issues the `for update skip locked` select inside the tick transaction, enqueues one run per flow, recomputes `next_run_at` in the flow timezone, and records `skipped_reason = overlap` when a run is already active (FR-F052-03, FR-F052-06).
- **SR-S103-05:** The worker fetches the file, computes SHA-256, enforces `max_file_mb` and `max_rows_per_run`, streams rows through the mapping read from `shuttle_flow_column_maps`, `shuttle_flow_key_columns`, and `shuttle_flow_required_columns` into an F010 job, applies the duplicate strategy, records counts and one `shuttle_run_rejections` row per rejected source row through `ShuttleRunRepository`, and finishes `succeeded`, `partial`, or `failed` per `on_error`; a checksum already succeeded for the flow finishes with `skipped_reason = duplicate_file` (FR-F052-04, FR-F052-05, FR-F052-07).
- **SR-S103-06:** Every processed file is archived to `shuttle/{tenant_id}/{flow_id}/{run_id}` with checksum and `retain_until`; the nightly purge removes expired archives and marks runs `archive_purged` (FR-F052-08).
- **SR-S103-07:** Runs publish `shuttle-run.started.v1` and `shuttle-run.completed.v1` or `shuttle-run.failed.v1`; flow mutations and run requests require `Idempotency-Key`, honour `If-Match`, and write audit rows; run rows carry the owner actor and `source = data_shuttle`, and a run fails with `sheet_denied` when the owner lost edit rights (FR-F052-11, FR-F052-13).
- **SR-S103-08:** Runs are JetStream jobs with per-tenant quota, three retries for transient storage errors, 30-minute timeout, and dead-letter state; metrics and spans per NFR-F052-04.

## Surfaces

- Infrastructure/container: MinIO bucket prefix `shuttle/` from the F004 compose baseline; JetStream subject `data-shuttle.run`
- Rust service/API: `crates/domain/src/data-shuttle/{mod.rs, flow.rs, mapping.rs, schedule.rs, run.rs, archive.rs, errors.rs, service.rs}`; `services/api/src/data-shuttle/{mod.rs, routes.rs, handlers_flow.rs, handlers_run.rs, dto.rs}`; `services/worker/src/data-shuttle/{mod.rs, scheduler.rs, consumer.rs, fetcher.rs, importer.rs, exporter.rs, archiver.rs, purge.rs}`
- Data/migration: `services/api/migrations/<ts>_data-shuttle_create_tables.sql` creating `shuttle_flows`, `shuttle_schedules`, `shuttle_runs`, `shuttle_archives` with the indexes from ticket section 4
- React/UI: none in this story (S104 covers the flow editor and run history)
- Mocks/fixtures: `testing/fixtures/data_shuttle.rs` tenants A/B, data-admin, editor, viewer, active entitlement with limits, `Budget` sheet, sample CSV/XLSX in MinIO; recorded connector `download` stub; injectable scheduler clock; in-memory outbox recorder

## TDD harness

- Test path: `testing/features/F052/api/`, `testing/features/F052/database/`, `testing/features/F052/performance/`
- Feature flag: `F052_FEATURE`
- Targeted command: `cargo xtask test-feature F052`
- Full command: `cargo xtask test-all`
- First failing tests: `flow_create_returns_next_run_at`, `flow_mapping_rejects_foreign_column`, `flow_schedule_rejects_under_15_minutes`, `run_request_conflicts_while_active`, `scheduler_claims_due_flow_once`, `worker_run_applies_update_strategy`, `worker_duplicate_checksum_skips`, `worker_abort_writes_nothing`

## Exit criteria

- [ ] Requirement tests SR-S103-01 through SR-S103-08 written first and failing
- [ ] Tasks T205 and T206 complete and wired through `services/api` router and `services/worker` consumer registry
- [ ] Unit, API, database, worker, permission, and performance tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/data-shuttle/routes.rs` mounted in `services/api/src/router.rs` behind `RequireModule(ModuleSlug::DataShuttle)`; `services/worker/src/data-shuttle/consumer.rs` registered in `services/worker/src/main.rs`
- [ ] Handoff evidence recorded in the F052 ticket
