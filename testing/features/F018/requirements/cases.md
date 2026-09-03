# F018 requirements cases

Feature: Workflow builder. Flag `F018_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F018-REQ-001` | FR-F018-01 | api | editor posts trigger + 2 actions → 201, `state: draft`, version 1, `published_version: null` |
| `F018-REQ-002` | FR-F018-02 | api | each of 8 trigger kinds accepted; cron `*/2 * * * *` → 400 `field_errors.trigger.cron`; kind `foo` → 400 |
| `F018-REQ-003` | FR-F018-03 | api | `all`/`any` depth 4 accepted; depth 5 → 400; `Amount starts_with` → 400 with leaf path |
| `F018-REQ-004` | FR-F018-04 | api | 12 action kinds validate params; `call_webhook` with `http://` or inline secret → 400 |
| `F018-REQ-005` | FR-F018-05 | api | `{{row.<unknown>}}` → 400 `field_errors.actions[1].params` naming the placeholder |
| `F018-REQ-006` | FR-F018-06 | api, database | PATCH published workflow → draft changes, `workflow_versions` row byte-identical |
| `F018-REQ-007` | FR-F018-07 | api, database | publish → `version_no` 1 then 2, `workflow.published.v1`, invalid definition → 400 with all errors |
| `F018-REQ-008` | FR-F018-08 | api | disable → `state: disabled`, `workflow.disabled.v1`; publish again → `version_no` +1 and `published` |
| `F018-REQ-009` | FR-F018-09 | api | test with `row_id` → `trigger_matched`, `condition_result`, `action_plan`; no outbox action rows |
| `F018-REQ-010` | FR-F018-10 | api | 120 workflows → cursor pages of 50, filter by `state=published`, `trigger_kind=schedule` |
| `F018-REQ-011` | FR-F018-11 | api | delete → 404 on GET/PATCH; version readable by ID through the versions reader |
| `F018-REQ-012` | FR-F018-12 | api | 101st published workflow on a sheet → 409 `field_errors.limit` |
| `F018-REQ-013` | FR-F018-13 | api, database | each mutation → one audit row with definition diff and one outbox row |
| `F018-REQ-014` | FR-F018-14 | frontend, e2e | builder validates live, `Publish` disabled until valid, viewer read-only, foreign id not-found |
| `F018-NFR-001` | NFR-F018-01 | performance | validate 25-action depth-4 p95 < 200 ms; test p95 < 2 s; list 5,000 p95 < 500 ms |
| `F018-NFR-002` | NFR-F018-02 | api | secrets stored as references only; tenant B → 404; formula leaf on hidden sheet → 400 |
| `F018-NFR-003` | NFR-F018-03 | accessibility | axe serious = 0 on list and builder; tree levels announced; errors linked by `aria-describedby` |
| `F018-NFR-004` | NFR-F018-04 | api, database | span carries tenant, workflow, correlation; publish and outbox in one transaction; metrics emitted |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F018/`.
