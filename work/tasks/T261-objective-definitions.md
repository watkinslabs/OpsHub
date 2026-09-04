---
id: T261
type: task
status: planned
parent_epic: E001
parent_feature: F066
parent_story: S131
depends_on: [S131]
owned_paths: [infra/slo/objectives.yml, automation/xtask/src/slo.rs, testing/fixtures/slo/**, testing/features/F066/requirements/**, testing/features/F066/api/**]
feature_flag: F066_FEATURE
branch: t261-objective-definitions
started_at: null
finished_at: null
---

# T261 — Objective definitions

## Identity

- Parent story: `S131` Objectives and measurement
- Owner: platform
- Branch: `t261-objective-definitions`
- Decision references: `docs/architecture-decisions.md` sections 1, 9; `docs/capability-contracts.md` row F066

## Objective

Write `infra/slo/objectives.yml` and the typed model that reads it: the route class registry, the four service level objectives over F004's `http_request_duration_seconds`, the rolling 28-day window with its budget arithmetic, and the exposition check that asserts the histogram buckets the objectives depend on.

## Specification

- Owned paths: `infra/slo/objectives.yml`, the model half of `automation/xtask/src/slo.rs`, `testing/fixtures/slo/{objectives,expositions}/`
- Contract/input: `objectives.yml` with `version: 1`, `window: 28d`, `classes`, `objectives`, `burn_alerts`, `policy { guarded_below: 0.25, exception_max_days: 14 }`; a Prometheus text exposition read from `--metrics <file|url>`, default `http://127.0.0.1:9464/metrics`.
- Classes: `core_read` (`GET`, `HEAD`) over `/api/v1/tenants/{id}`, `/api/v1/users`, `/api/v1/users/{id}`, `/api/v1/groups`, `/api/v1/groups/{id}`, `/api/v1/roles`, `/api/v1/sessions`, `/api/v1/api-tokens`, `/api/v1/audit-events`; `core_write` (`POST`, `PUT`, `PATCH`, `DELETE`) over `/api/v1/tenants`, `/api/v1/tenants/{id}`, `/api/v1/users`, `/api/v1/users/{id}`, `/api/v1/groups`, `/api/v1/groups/{id}/members`, `/api/v1/roles`, `/api/v1/resources/{kind}/{id}/acl`, `/api/v1/sessions/{id}`, `/api/v1/api-tokens`; `async_ack` over the 202 responders `/api/v1/tenants/{id}/suspend`, `/api/v1/reports/{id}/refresh`, `/api/v1/metrics/{id}/recompute`, `/api/v1/webhook-deliveries/{id}/replay`; excluded `analytics`, `integration`, and `exempt` (`/healthz`, `/readyz`, `/metrics`, `/auth/oidc/start`, `/auth/oidc/callback`). Classes are disjoint per `(route, method)`.
- Output/behavior: `Objectives::load` returns `slo.schema` findings with line numbers for unknown keys, targets outside `0 < target < 1`, duplicate ids, and unreferenced classes; `Objectives::classify(route, method)` returns the class or `slo.route_unclassified`; `Budget::minutes(objective)` yields 201.6 for `availability_core`, 2,016 for each latency objective, and 403.2 for `ack_async` from 40,320 window minutes; `Budget::remaining_ratio(ratio, target)` is `1 - (1 - ratio) / (1 - target)`, clamped at -1 only for display; `check_exposition` reports `slo.bucket_missing` for an absent exact `le` series at 0.5, 0.8, or 2, `skipped: metrics sample absent` when no sample is given, and never opens a socket unless `--metrics` is a URL.
- Dependencies: F004's `/metrics` exporter and its `http_request_duration_seconds` histogram; F041's `support::OutputFormat` and finding reporter; `serde_yaml` from the existing workspace dependencies.
- Feature flag: `F066_FEATURE` gates the CI step; the module itself is always compiled so `cargo xtask verify-slo` remains runnable locally.

## TDD

- Failing test first: `testing/features/F066/api/objectives_tests.rs::objectives_schema_rejects_unknown_key`, `::target_of_one_rejected`, `::duplicate_objective_id_rejected`, `::unreferenced_class_rejected`, `::class_overlap_on_route_and_method_rejected`, `::classify_returns_core_read_for_get_users`, `::classify_returns_async_ack_only_for_202_responders`, `::unclassified_route_names_the_route`, `::analytics_and_integration_are_excluded_from_denominators`; `testing/features/F066/api/budget_tests.rs::budget_minutes_are_201_6_for_availability_core`, `::latency_budget_is_2016_minutes`, `::ack_budget_is_403_2_minutes`, `::remaining_ratio_is_negative_when_overspent`; `testing/features/F066/api/exposition_tests.rs::missing_le_0_8_bucket_reports_bucket_missing`, `::non_histogram_metric_rejected`, `::absent_sample_is_skipped_not_failed`
- Targeted command: `cargo xtask test-feature F066`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/slo/objectives/{valid,overlap,bad_target,duplicate_id}.yml`, `testing/fixtures/slo/expositions/{healthy,missing_bucket,unclassified_route,no_histogram}.txt`; fixed clock `2026-09-03T00:00:00Z`; no network and no database

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] `infra/slo/objectives.yml` committed and loading cleanly; every M1 route of F002, F003, F038, and F004 classified
- [ ] Owned-path check passes and no path overlaps F004's `infra/**` claim while F004 is active
- [ ] File limit and lint gates pass; `automation/xtask/src/slo.rs` stays under 500 lines
- [ ] Handoff evidence recorded in S131
- [ ] `finished_at` recorded
