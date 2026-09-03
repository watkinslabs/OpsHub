---
id: T216
type: task
status: planned
parent_epic: E008
parent_feature: F054
parent_story: S108
depends_on: [T215]
owned_paths: [testing/features/F054/**]
feature_flag: F054_FEATURE
branch: t216-failure-tests
started_at: null
finished_at: null
---

# T216 — Failure tests

## Identity

- Parent story: `S108` Run operations
- Owner: platform
- Branch: `t216-failure-tests`
- Decision references: `docs/architecture-decisions.md` sections 4, 7, 9; `docs/capability-contracts.md` row F054

## Objective

Complete the F054 harness with failure, recovery, E2E, accessibility, and load suites so every async path in a Bridge run has a tested retry, dead-letter, cancel, or resume outcome.

## Specification

- Owned paths: `testing/features/F054/api/failure_tests.rs`, `testing/features/F054/e2e/bridge.spec.ts`, `testing/features/F054/accessibility/bridge.a11y.spec.ts`, `testing/features/F054/performance/{run_bench.rs, run_list_bench.rs}`, `testing/features/F054/requirements/cases.md` (final traceability), `testing/features/F054/README.md`
- Contract/input: seeded tenant A (editor, viewer), tenant B, entitlement with `max_runs_per_day 100`; scripted connector mocks that can return `unavailable`, `rate_limited`, `denied`, timeouts, and 300 KB payloads; F019 dead-letter inspection helper; Playwright sessions per role; 100,000-run generator.
- Output/behavior: failure suite proves step timeout at the configured limit, 3 retries then `failed` with `bridge-run.failed.v1`, dead-lettering when the tenant quota is exhausted, connection revoked between publish and run yields per-step `denied`, snapshot truncation at 256 KB, cancel during `waiting`, resume after worker restart for `waiting` runs, and idempotent redelivery of the same JetStream message producing no duplicate step rows; E2E covers build → publish → run → fail → retry → succeed, cancel, viewer read-only, not-entitled panel; accessibility covers axe on builder and console, timeline keyboard navigation, live region; performance covers enqueue p95 < 2 s, 10-step run < 30 s, run list p95 < 500 ms at 100,000 runs; the requirements table maps FR-F054-01..15 and NFR-F054-01..04 to case IDs with lanes.
- Dependencies: T215 console and retry; F004 `two-api` compose profile for worker restart; F019 dead-letter tables.
- Feature flag: `F054_FEATURE` on for the suite; one E2E case runs with the flag off and asserts routes are absent and the worker consumer is not registered.

## TDD

- Failing test first: `testing/features/F054/api/failure_tests.rs::step_timeout_marks_failed`, `::quota_exhaustion_dead_letters_run`, `::redelivered_message_creates_no_duplicate_steps`, `::waiting_run_resumes_after_worker_restart`, `::cancel_during_wait_marks_cancelled`; `testing/features/F054/e2e/bridge.spec.ts::build_publish_run_retry_flow`, `::viewer_is_read_only`; `testing/features/F054/accessibility/bridge.a11y.spec.ts::builder_and_console_have_no_serious_axe_violations`; `testing/features/F054/performance/run_list_bench.rs::run_list_100k_p95`
- Targeted command: `cargo xtask test-feature F054`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: scripted `ActionInvoker`; in-process queue with redelivery control; Playwright against the real API; k6 script for enqueue and list

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Failure, E2E, accessibility, and performance lanes pass; evidence stored under `testing/evidence/F054/`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S108
- [ ] `finished_at` recorded
