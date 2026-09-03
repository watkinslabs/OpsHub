# F054 requirements cases

Feature: Bridge. Flag `F054_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F054-REQ-001` | FR-F054-01 | api | create with 5 typed steps → 201; 51 steps or missing trigger → 400 `field_errors.steps` |
| `F054-REQ-002` | FR-F054-02 | api | trigger kinds `row_event`, `schedule` (4-minute cron → 400), `inbound_webhook` token issued, `sync_event` |
| `F054-REQ-003` | FR-F054-03 | api | `jira.create_issue` with foreign connection → 403 `field_errors.steps[1].config.connection_id` |
| `F054-REQ-004` | FR-F054-04 | api | transform with 501 AST nodes → 400; `for_each` over 1,001 items → 400; cycle → 409 `cycle` |
| `F054-REQ-005` | FR-F054-05 | api, database | publish → `bridge_flow_versions` row version 1; second publish → version 2; draft patch leaves version 2 intact |
| `F054-REQ-006` | FR-F054-06 | api, performance | run → 202 under 2 s; same key → same `run_id`; unpublished → 409; 101st run today → 429 |
| `F054-REQ-007` | FR-F054-07 | api | `rate_limited` twice then success → step succeeded with 3 attempts; 4th failure → step and run `failed` |
| `F054-REQ-008` | FR-F054-08 | api | snapshot with `authorization` header → `***` in row, log, and event |
| `F054-REQ-009` | FR-F054-09 | api | `wait.delay` 10 min → status `waiting`, no worker slot; `wait.approval` resumes on decision |
| `F054-REQ-010` | FR-F054-10 | api, e2e | retry failed step → downstream resumes, `bridge-run.step-completed.v1`; retry succeeded step → 409 |
| `F054-REQ-011` | FR-F054-11 | api, performance | list filters by `status=failed` and `flow_id`; detail returns pinned version and ordered steps |
| `F054-REQ-012` | FR-F054-12 | api, database | five-step run → 1 started, 5 step-completed, 1 completed outbox rows; audit rows per mutation |
| `F054-REQ-013` | FR-F054-13 | api | suspended entitlement → 403 `field_errors.module`; 11th flow with `max_flows 10` → 409 `field_errors.limit` |
| `F054-REQ-014` | FR-F054-14 | api | tenant B reads run → 404; viewer POST run/retry → 403 |
| `F054-REQ-015` | FR-F054-15 | frontend, e2e | builder forms per kind; console timeline, redaction markers, retry, cancel, 5 s polling |
| `F054-NFR-001` | NFR-F054-01 | performance | enqueue p95 < 2 s; 10-step mocked run < 30 s; run list p95 < 500 ms at 100k runs |
| `F054-NFR-002` | NFR-F054-02 | api | connection revoked after publish → step `denied`; no code step kind exists; snapshots redacted |
| `F054-NFR-003` | NFR-F054-03 | accessibility | axe serious = 0; timeline keyboard navigable; live region announces status |
| `F054-NFR-004` | NFR-F054-04 | api | quota exhaustion dead-letters; redelivery idempotent; spans carry run and step IDs; metrics emitted |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F054/`.
