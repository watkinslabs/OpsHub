---
id: T272
type: task
status: planned
parent_epic: E001
parent_feature: F068
parent_story: S136
depends_on: [S136]
owned_paths: [testing/features/F068/**, testing/fixtures/persistence/**]
feature_flag: F068_FEATURE
branch: t272-persistence-harness
started_at: null
finished_at: null
---

# T272 — Persistence harness

## Identity

- Parent story: `S136` Normalization and access gate
- Owner: platform
- Branch: `t272-persistence-harness`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, and 9 (feature-gated suites, isolated fixtures, fixed clocks); `docs/capability-contracts.md` row F068

## Objective

Build the seven-lane harness for `F068`, including the `trybuild` compile-fail lane, the throwaway PostgreSQL 18 database lane with one database per worker, the conformance suite that runs the same eight cases against every registered `RepositorySpec`, and the honest negative controls for the lanes this feature has no surface in.

## Specification

- Owned paths: `testing/features/F068/{README.md, feature.toml}`, `testing/features/F068/{requirements,api,database,frontend,e2e,accessibility,performance}/`, `testing/fixtures/persistence/**`
- Requirements lane: one row per `FR-F068-01` through `FR-F068-16` and `NFR-F068-01` through `NFR-F068-05` naming the lane that proves it
- API lane: `trybuild` expectations under `api/ui/` for the sealed trait, a specification returning SQL, a foreign `Column`, two live handles on one `UnitOfWork`, use after `commit`, and a `PurgeCtx` without a grant; plus statement-shape and mapping unit tests that need no connection
- Database lane: one `postgres:18` container per test session, database `opshub_f068_w{worker}` per worker, F002 `*_tenants_*.sql`, F003 `*_authz_*.sql`, and F004 `*_runtime_*.sql` applied at setup and dropped at teardown; a session that cannot reach Docker fails the lane rather than skipping it
- Conformance suite: `database/conformance_tests.rs` iterates the link-time registry of `RepositorySpec` implementations and runs cross-tenant read, cross-tenant write, soft-delete filter, version conflict, audit row present, outbox row present, rollback atomicity, and cursor rejection against each, writing a per-specification matrix to evidence
- Frontend lane: this feature ships no component and no client, so the lane holds the gate's two renderings — sorted `BLOCKED:` text and the single `--json` object — plus the control that `apps/web/` and `openapi/v1.json` are unchanged on this branch
- E2E lane: the gate over whole fixture repository trees and the crate over a real database; no browser is started
- Accessibility lane: ASCII-only output, findings carrying path and line, JSON structural equivalence, and the heading and table structure of `crates/persistence/README.md`
- Performance lane: gate under 2 seconds over the repository, page 2,000 as cheap as page 2 over 100,000 users, no extra round trip per mutation, and no `offset` in any generated statement
- Fixtures: `testing/fixtures/persistence/seed.rs` (tenants A and B, 3 and 100,000 users, fixed UUIDv7 sequence, fixed clock `2026-09-03T00:00:00Z`, fixed cursor HMAC key), `trees/`, `migrations/`, `catalog/`, `baseline.json`
- Evidence: `testing/evidence/F068/` holding the gate JSON, the `trybuild` expectations, the conformance matrix, and the pagination timings
- Dependencies: T269 and T270 for the crate under test; T271 for the gate under test; Docker with `postgres:18`; `trybuild`
- Feature flag: `F068_FEATURE` selects the suite; `cargo xtask test-all` enables every suite

## TDD

- Failing test first: `testing/features/F068/api/ui/hand_written_repository.rs::hand_written_repository_impl_does_not_compile`, `testing/features/F068/database/conformance_tests.rs::every_registered_spec_passes_the_eight_case_suite`, `::spec_without_catalog_table_is_reported`; `testing/features/F068/frontend/output_tests.rs::text_and_json_findings_carry_the_same_fields`, `::web_app_and_openapi_are_unchanged`; `testing/features/F068/database/no_migration_tests.rs::feature_adds_no_migration_file`; `testing/features/F068/accessibility/output_a11y_tests.rs::output_is_ascii_only`; `testing/features/F068/performance/gate_bench.rs::gate_completes_under_two_seconds`
- Targeted command: `cargo xtask test-feature F068`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: as listed above; one temporary tree per static case, one database per worker, one tenant id per test, no shared port

## Exit criteria

- [ ] Every lane has a `cases.md` listing its test names and the requirement ids they prove, with no lane duplicating another feature's file
- [ ] `requirements/cases.md` names every FR and NFR id declared in the F068 ticket
- [ ] Compile-fail lane runs without Docker; database lane runs against a throwaway PostgreSQL 18 in parallel without cross-talk
- [ ] Conformance matrix written to `testing/evidence/F068/` with one row per registered specification
- [ ] Every file ≤ 500 lines; `cargo xtask validate-tickets` passes
- [ ] Handoff evidence recorded in S136
- [ ] `finished_at` recorded
