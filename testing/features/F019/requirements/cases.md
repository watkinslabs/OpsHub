# F019 requirements cases

Feature: Workflow runtime. Flag `F019_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F019-REQ-001` | FR-F019-01 | api | `row.updated.v1` on a sheet with 2 matching published workflows → 2 `queued` runs, each pinned to its version, `workflow-run.queued.v1` x2 |
| `F019-REQ-002` | FR-F019-02 | api, database | same event delivered twice → one run row, second delivery returns existing id |
| `F019-REQ-003` | FR-F019-03 | api | clock advanced 3 windows past a 5-minute schedule → one catch-up run; `next_fire_at` advanced; DST in `America/New_York` handled |
| `F019-REQ-004` | FR-F019-04 | api | inbound webhook: valid HMAC → 202 with `run_id`; bad HMAC → 403; replayed delivery id → 200 same `run_id`; 61st request → 429 |
| `F019-REQ-005` | FR-F019-05 | api, database | 3-step run → 3 step rows in order; failing step 2 with `continue_on_error` → `skipped_error`, run completes |
| `F019-REQ-006` | FR-F019-06 | api | failing webhook action → delays 10 s, 20 s, 40 s, 80 s, 160 s (+jitter); after attempt 5 → `dead_lettered` and event |
| `F019-REQ-007` | FR-F019-07 | api | executor sleeping 31 s → `error.code: timeout`, attempt incremented |
| `F019-REQ-008` | FR-F019-08 | api, performance | 150 simultaneous runs → 100 running, 50 queued; second tenant still dequeued; overflow metric and audit row |
| `F019-REQ-009` | FR-F019-09 | api | each of 12 action kinds invokes its executor once with `(run_id, index, attempt)` |
| `F019-REQ-010` | FR-F019-10 | api | workflow updating its own trigger column → runs at depth 1..5, sixth rejected `loop_detected` |
| `F019-REQ-011` | FR-F019-11 | api | 500 runs → cursor pages, `filter[status]=failed`, `started_after`; detail returns ordered steps |
| `F019-REQ-012` | FR-F019-12 | api | retry `dead_lettered` → `queued` from failed step; cancel `completed` → 409 |
| `F019-REQ-013` | FR-F019-13 | api | `workflow.disabled.v1` mid-run → run cancelled after current step, `workflow_disabled`; history readable |
| `F019-REQ-014` | FR-F019-14 | api, frontend, e2e | each transition → event + audit row; editor retries in UI; viewer read-only |
| `F019-NFR-001` | NFR-F019-01 | performance | start latency p95 < 2 s at 1,000 events/min; list p95 < 500 ms over 1M runs; 10,000 triggers/tick < 30 s |
| `F019-NFR-002` | NFR-F019-02 | api | service actor cannot write outside sheet scope; tenant B run → 404; signature compared constant-time; body redacted |
| `F019-NFR-003` | NFR-F019-03 | accessibility | axe serious = 0; status has text+icon; dialogs trap focus |
| `F019-NFR-004` | NFR-F019-04 | api, database | ack only after commit; metrics exported; spans carry run ids; crash mid-run resumes from last committed step |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F019/`.
