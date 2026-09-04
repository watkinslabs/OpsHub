# F002 requirements cases

Feature: Tenant, users, and groups. Flag `F002_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F002-REQ-001` | FR-F002-01 | api, database | operator creates tenant "acme" → 201, version 1, admin user active in same transaction |
| `F002-REQ-002` | FR-F002-02 | api | slug "Ac me", plan "gold", region "eu-west" → 400 with three `field_errors`; taken slug → 409 |
| `F002-REQ-003` | FR-F002-03 | api | PATCH own tenant with stale `If-Match` → 409 `current_version`; other tenant id → 404 |
| `F002-REQ-004` | FR-F002-04 | api, e2e | suspend → `tenant.suspended.v1`; next `POST /api/v1/groups` → 403 reason `tenant_suspended` |
| `F002-REQ-005` | FR-F002-05 | api, database | invite "Ops@Acme.test" twice → second is 409 `field_errors.email` |
| `F002-REQ-006` | FR-F002-06 | api | 450 users → `limit=200` three pages; `status`, `email` prefix, `group_id` filters; sort by `email` |
| `F002-REQ-007` | FR-F002-07 | api | `invited → suspended` → 400 `field_errors.status`; member editing own email → 403 |
| `F002-REQ-008` | FR-F002-08 | api | deactivate member → memberships gone, `SessionRevoker` called; last admin → 400 `last_admin` |
| `F002-REQ-009` | FR-F002-09 | api, database | group "finance" then "Finance" → 409; rename emits `group.updated.v1` |
| `F002-REQ-010` | FR-F002-10 | api | replace with 2 kept + 4 new → 6 members, event lists added 4 and removed 1; foreign id → 400 |
| `F002-REQ-011` | FR-F002-11 | api | same key twice → one row, same body; different body → 409 `idempotency_mismatch` |
| `F002-REQ-012` | FR-F002-12 | api, database | each mutation → one audit row and one outbox event; outbox failure rolls back |
| `F002-REQ-013` | FR-F002-13 | api | tenant B admin hits all 12 routes with tenant A ids → 404 |
| `F002-REQ-014` | FR-F002-14 | frontend, e2e | admin manages users and groups; member sees denied state on `/admin/*` |
| `F002-NFR-001` | NFR-F002-01 | performance | 100k-user list p95 < 500 ms; 5,000-member replace p95 < 800 ms |
| `F002-NFR-002` | NFR-F002-02 | api | tenant predicate bound from context; email redacted in logs; negative suite green |
| `F002-NFR-003` | NFR-F002-03 | accessibility | axe serious = 0 on three admin pages; keyboard toggles; live region announces |
| `F002-NFR-004` | NFR-F002-04 | api | span carries tenant, actor, correlation; `tenant_mutations_total` increments |

| `F002-REQ-020` | FR-F002-20 | api | a 500-user bulk deactivate returns a per-user result and writes 500 audit rows and events; a mismatched confirmation count is refused; 501 users is rejected; deactivating the last tenant-admin returns 409 `last_admin`; a replayed idempotency key applies once |

| `F002-REQ-015` | FR-F002-15 | api | a 500-user bulk deactivate returns a per-user result and writes 500 audit rows and events; a mismatched confirmation count is refused; 501 users is rejected; deactivating the last tenant-admin returns 409 `last_admin`; a replayed idempotency key applies once |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F002/`.
