---
id: T058
type: task
status: planned
parent_epic: E003
parent_feature: F015
parent_story: S029
depends_on: [T057]
owned_paths: [crates/domain/src/templates/**, crates/persistence/src/templates/**, services/api/src/templates/**, services/worker/src/templates/**, apps/web/src/features/templates/**, testing/features/F015/api/**, testing/features/F015/frontend/**, testing/features/F015/performance/**]
feature_flag: F015_FEATURE
branch: t058-provisioning-job
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 6, 7
- Capability contract: `docs/capability-contracts.md` row F015

# T058 — Provisioning job

## Identity

- Parent story: `S029` Project template
- Owner: platform
- Branch: `t058-provisioning-job`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 6, 7; `docs/capability-contracts.md` row F015

## Objective

Implement the provision request route, the JetStream provisioning job with ordered idempotent steps, retry and rollback, the run polling route, and the catalog, provision dialog, and run status UI.

## Specification

- Owned paths: `crates/domain/src/templates/{provisioning.rs, service_provision.rs}`, `crates/persistence/src/templates/{mod.rs, provisioning_run_repository.rs}`, `services/api/src/templates/handlers_provision.rs`, `services/worker/src/templates/{mod.rs, provision_job.rs, steps.rs, rollback.rs}`, `apps/web/src/features/templates/{TemplateCatalogPage.tsx, TemplateCard.tsx, CategoryFilter.tsx, TemplateDetail.tsx, ManifestSummary.tsx, VersionHistory.tsx, ProvisionDialog.tsx, RoleAssignmentPicker.tsx, ProvisioningStatus.tsx, StepList.tsx, api.ts, hooks.ts, routes.ts}`
- Contract/input: `ProvisionRequest { version_id, workspace_id, project_name, start_date, role_assignments, options: { include_forms, include_views } }`; job message `templates.provision { run_id, tenant_id, correlation_id }`; `GET /api/v1/provisioning-runs/{id}`.
- Output/behavior: `POST /api/v1/project-templates/{id}/provision` requires `portfolio-admin` plus `workspace-admin` on the target, rejects draft versions, inserts the run and its `pending` `provisioning_run_steps` rows through `ProvisioningRunRepository`, enqueues the job, and returns `202 ProvisioningRunResponse` under 2 s; the worker runs steps `sheets`, `columns`, `rows`, `schedule_settings`, `dependencies`, `views`, `forms`, `roles` through the F006, F007, F011, F012, F013, F014 domain services, holding no SQL of its own: it calls `claim_step(run_id, step)` to take the step row and `record_artifact(run_id, step, item_key, object)` for every object created, so `unique (run_id, step, item_key)` makes replay idempotent, and each step's writes run in one `UnitOfWork`; default-row dates resolve with `add_working_days(start_date, offset)`; unknown modules are step rows set to `skipped` with reason `module_unavailable`; three retries with exponential backoff increment `attempt`, then `rollback_run` reads `list_artifacts_for_rollback(run_id)` (ordered `created_at desc`), soft-deletes those objects in that order, marks the step rows `rolled_back`, and emits `provisioning.failed.v1`; completion emits `project.provisioned.v1` with `created_ids` grouped by `object_kind` from the artifact rows; `GET /api/v1/provisioning-runs/{id}` renders the step rows and the same grouped `created_ids`; UI polls the run every 2 s, announces step progress, and offers `Open project` or `Retry provisioning`; telemetry `template_provision_requested`, `provisioning_completed`, `provisioning_failed`.
- Dependencies: T057 tables and services; F004 JetStream transport and worker consumer registry; F005 workspace membership check.
- Feature flag: `F015_FEATURE` gates the route, the consumer registration, and the web routes.

## TDD

- Failing test first: `testing/features/F015/api/provision_tests.rs::provision_returns_202_within_budget`, `::provision_rejects_draft_version`, `::provision_editor_denied`, `::provision_run_completes_all_steps`, `::provision_step_is_idempotent_on_replay`, `::provision_artifact_key_is_unique_per_step`, `::provision_failure_rolls_back`, `::provision_records_skipped_modules`, `::run_poll_cross_workspace_not_found`; `testing/features/F015/frontend/ProvisionDialog.test.tsx::submits_with_workspace_start_date_roles`, `ProvisioningStatus.test.tsx::announces_step_progress`, `::shows_failed_run_with_rollback_badge`; `testing/features/F015/performance/provision_bench.rs::provision_500_rows_under_60s`
- Targeted command: `cargo xtask test-feature F015`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: in-process worker runner from `testing/harness/worker.rs`; failing-dependency manifest; MSW handlers for the run polling states

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Consumer registered in `services/worker/src/consumers.rs` behind the flag; p95 and completion targets from NFR-F015-01 met
- [ ] Owned-path check passes
- [ ] File limit, lint, and `cargo xtask check-persistence` gates pass
- [ ] Handoff evidence recorded in S029
- [ ] `finished_at` recorded
