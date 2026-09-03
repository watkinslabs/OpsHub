# F020 requirements cases

Feature: Approvals and escalation. Flag `F020_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F020-REQ-001` | FR-F020-01 | api | editor posts row target, 2 users + 1 group, `count: 2` → 201, `pending`, expanded approvers ≤ 50; 21 approvers → 400 |
| `F020-REQ-002` | FR-F020-02 | api | create → `approval.requested.v1` and one `approval` notification per approver, none for requester |
| `F020-REQ-003` | FR-F020-03 | api, database | approver decides once → decision row; again → 409; non-approver → 403; reject without reason → 400 |
| `F020-REQ-004` | FR-F020-04 | api | `any`/`all`/`count` tables resolve as specified; one rejection → `rejected`; `approval.decided.v1` carries `outcome` |
| `F020-REQ-005` | FR-F020-05 | api | reassign Ben → Dee keeps Ana's decision, notifies Dee, audits; Dee without row access → 400 `field_errors.to_user_id` |
| `F020-REQ-006` | FR-F020-06 | api | cancel → `cancelled`, `approval.cancelled.v1`, timers voided; decide after cancel → 409 |
| `F020-REQ-007` | FR-F020-07 | api | PUT policy with `escalate_after_minutes: 3` → 400; valid policy → 200 with version |
| `F020-REQ-008` | FR-F020-08 | api, database | create with `standard` → reminder, escalate, expire timers; +61 min sweep → manager added at level 1, `approval.escalated.v1` |
| `F020-REQ-009` | FR-F020-09 | api | `auto_reject` past due → system decision `expired`, `rejected`; `none` → `overdue: true` |
| `F020-REQ-010` | FR-F020-10 | api | 300 approvals → cursor pages, `assigned_to_me`, `requested_by_me`, `overdue`, sort by `due_at`; detail has decisions and trail |
| `F020-REQ-011` | FR-F020-11 | api | user with neither target access nor membership → 404; approver without target ACL → 200 |
| `F020-REQ-012` | FR-F020-12 | api, database, e2e | each decision, reassignment, escalation, expiry, cancel → append-only audit row with reason and `correlation_id` |
| `F020-REQ-013` | FR-F020-13 | frontend, e2e | inbox lists assigned approvals with due badges; approve/reject/reassign for approvers; read-only otherwise |
| `F020-REQ-014` | FR-F020-14 | api | stale `If-Match` → 409 with current version; same key replay → original response |
| `F020-NFR-001` | NFR-F020-01 | performance | create/decide p95 < 800 ms; inbox p95 < 500 ms over 100,000; 10,000 timers per sweep < 60 s |
| `F020-NFR-002` | NFR-F020-02 | api | group edited after creation adds no approver; guest not listed → 404; tenant B → 404 |
| `F020-NFR-003` | NFR-F020-03 | accessibility | axe serious = 0; due state text+icon; reject reason error receives focus |
| `F020-NFR-004` | NFR-F020-04 | api, database | two sweepers fire each timer once; metrics exported; spans carry approval ids |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F020/`.
