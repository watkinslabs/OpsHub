---
id: T202
type: task
status: planned
parent_epic: E008
parent_feature: F051
parent_story: S101
depends_on: [T201]
owned_paths: [crates/domain/src/workapps/**, crates/persistence/src/workapps/**, services/api/src/workapps/**, testing/features/F051/api/**, testing/features/F051/requirements/**]
feature_flag: F051_FEATURE
branch: t202-embedded-surfaces
started_at: null
finished_at: null
---

# T202 — Embedded surfaces

## Identity

- Parent story: `S101` App composition
- Owner: platform
- Branch: `t202-embedded-surfaces`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 10; `docs/capability-contracts.md` row F051

## Objective

Implement the real `SourceResolver` against the sheet, view, form, report, dashboard, and dynamic view read services and the transactional publish with versioned snapshots and rollback.

## Specification

- Owned paths: `crates/domain/src/workapps/{sources.rs, version.rs, service_publish.rs}`, `crates/persistence/src/workapps/version_repository.rs`, `services/api/src/workapps/handlers_publish.rs`
- Contract/input: `SourceResolver::resolve(tenant_id, workspace_id, kind, source_id) -> Result<SourceRef, SourceError>` backed by F006 `get_sheet`, F013 `get_view`, F014 `get_form` (published only), F021 `get_report`, F023 `get_dashboard`, F050 `get_view`; `PublishRequest { note?, version_number? }` with `If-Match`.
- Output/behavior: `PUT /pages` now rejects a missing source, a soft-deleted source, a source from another workspace, or a kind mismatch with `400 invalid` `field_errors.pages[n].source_id` naming the reason (`missing`, `deleted`, `other_workspace`, `kind_mismatch`); `POST /api/v1/workapps/{id}/publish` snapshots the draft into `workapp_versions` as `version_number = max + 1` together with its `workapp_version_pages`, `workapp_version_roles`, `workapp_version_page_roles`, and `workapp_version_role_members` rows copied from the draft's `workapp_pages`, `workapp_page_roles`, `workapp_roles`, and `workapp_role_members`, sets `workapps.published_version` and `status: published` in the same transaction, returns `PublishResponse { version_number, warnings }` with warnings for roles without members, rejects empty pages or roles with `400 invalid`, republishes an earlier `version_number` as a new version when given (unknown number → `404 not_found`), and emits `workapp.published.v1`; a failure after snapshot insert rolls back so `published_version` never advances; audit `workapp.publish` records note and version.
- Data access: `WorkAppVersionRepository` in `crates/persistence/src/workapps/version_repository.rs` owns `workapp_versions` and the four `workapp_version_*` tables and exposes `insert_version_snapshot`, `copy_version_as_new_number`, `load_version_manifest`, and `list_version_summaries`; `service_publish.rs`, `version.rs`, `sources.rs`, and `handlers_publish.rs` contain no SQL, and one `UnitOfWork` spans the snapshot inserts, the `set_published_version` update on `WorkAppRepository`, the audit row, and the outbox row so a failure leaves no partial version (decision section 2.1).
- Dependencies: T201 schema, repositories, and routes; read services of F006, F013, F014, F021, F023, F050 exposed through `crates/domain`.
- Feature flag: `F051_FEATURE`.

## TDD

- Failing test first: `testing/features/F051/api/manifest_tests.rs::pages_reject_source_of_wrong_kind`, `::pages_reject_source_from_other_workspace`, `::pages_reject_soft_deleted_source`, `::pages_reject_unpublished_form`; `testing/features/F051/api/publish_tests.rs::publish_snapshots_manifest_and_increments_version`, `::publish_rejects_empty_manifest`, `::publish_restores_earlier_version_as_new_number`, `::publish_unknown_version_not_found`, `::publish_failure_does_not_advance_published_version`, `::publish_writes_audit_and_outbox`, `::publish_copies_page_visibility_and_role_member_rows`, `::snapshot_rows_are_immutable_after_publish`
- Targeted command: `cargo xtask test-feature F051`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: fixture sheet, draft form, published form, report, dashboard, dynamic view; fault injector on the outbox insert for the rollback case

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Publish route mounted in `services/api/src/workapps/routes.rs`; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S101
- [ ] `finished_at` recorded
