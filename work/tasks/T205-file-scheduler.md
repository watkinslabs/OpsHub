---
id: T205
type: task
status: planned
parent_epic: E008
parent_feature: F052
parent_story: S103
depends_on: [S103]
owned_paths: [services/api/migrations/*_data-shuttle_*.sql, crates/domain/src/data-shuttle/**, services/api/src/data-shuttle/**, services/worker/src/data-shuttle/**, testing/features/F052/database/**, testing/features/F052/api/**]
feature_flag: F052_FEATURE
branch: t205-file-scheduler
started_at: null
finished_at: null
---

# T205 — File scheduler

## Identity

- Parent story: `S103` Scheduled file flows
- Owner: platform
- Branch: `t205-file-scheduler`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 7; `docs/capability-contracts.md` row F052

## Objective

Create the four Data Shuttle tables, the flow domain model with schedule computation, the flow and run-request routes, and the worker scheduler that claims due flows exactly once.

## Specification

- Owned paths: `services/api/migrations/<ts>_data-shuttle_create_tables.sql`, `services/api/migrations/<ts>_data-shuttle_create_tables.down.sql`, `crates/domain/src/data-shuttle/{mod.rs, flow.rs, schedule.rs, run.rs, errors.rs, service.rs, schema.rs}`, `services/api/src/data-shuttle/{mod.rs, routes.rs, handlers_flow.rs, handlers_run.rs, dto.rs}`, `services/worker/src/data-shuttle/{mod.rs, scheduler.rs}`
- Contract/input: DDL per F052 ticket section 4 (single-active-run partial unique index, checksum uniqueness, schedule and retention indexes); `CreateFlowRequest { name, direction, location, sheet_id, mapping, validation, schedule, archive_policy }`, `UpdateFlowRequest` with `If-Match`; `Idempotency-Key` on every mutation; `Schedule::Cron { expression, timezone }` validated by `min_interval_ok` (five-field cron, no slot closer than 15 minutes) and `compute_next_run(now, tz)`; scheduler tick every 60 seconds on an injectable clock.
- Output/behavior: `GET/POST /api/v1/data-shuttle/flows`, `PATCH /api/v1/data-shuttle/flows/{id}`, `POST /api/v1/data-shuttle/flows/{id}/run` return `FlowResponse` / `202 RunRequestResponse`; limit checks read `max_flows` from the F048 entitlement; run request inserts a `queued` run (partial index turns a concurrent second insert into `409 already_active`) and publishes a `data-shuttle.run` job; scheduler selects `shuttle_schedules where next_run_at <= now() for update skip locked`, enqueues, records `overlap` skips, and writes `next_run_at`; `sqlx migrate run` and `revert` apply cleanly.
- Dependencies: F048 `RequireModule(ModuleSlug::DataShuttle)` and entitlement limits; F003 authz and audit writer; F004 outbox and JetStream publisher; F006 sheet lookup for `sheet_id`; F007 column types for later mapping validation.
- Feature flag: `F052_FEATURE` gates router mounting and the scheduler loop (idle when off).
- Large-table note: `shuttle_runs` grows per run; the `(flow_id, created_at desc)` index backs the history list.

## TDD

- Failing test first: `testing/features/F052/database/migration_tests.rs::shuttle_tables_exist_with_constraints`, `::second_active_run_rejected`, `::schedule_index_used_for_due_query`, `::rollback_drops_tables`; `testing/features/F052/api/flow_tests.rs::flow_create_returns_next_run_at`, `::flow_schedule_rejects_under_15_minutes`, `::flow_limit_reached_conflicts`, `::flow_no_entitlement_denied_by_guard`, `testing/features/F052/api/run_tests.rs::run_request_conflicts_while_active`, `::run_request_acks_under_2s`; `testing/features/F052/api/scheduler_tests.rs::scheduler_claims_due_flow_once`, `::scheduler_records_overlap_skip`, `::next_run_crosses_dst_correctly`
- Targeted command: `cargo xtask test-feature F052`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: schema-per-worker database from `testing/harness/db.rs`; `testing/fixtures/data_shuttle.rs` tenants and entitlement; in-memory outbox recorder; two scheduler instances against one schema for the exactly-once test

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; router mounted in `services/api/src/router.rs` behind the guard; scheduler registered in `services/worker/src/main.rs`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S103
- [ ] `finished_at` recorded
