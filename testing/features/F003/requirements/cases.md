# F003 requirements cases

Feature: Authorization and audit. Flag `F003_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F003-REQ-001` | FR-F003-01 | database, api | new tenant → seven system roles with `is_system`; PATCH slug of `viewer` → 400 |
| `F003-REQ-002` | FR-F003-02 | api | create `reviewer` with 3 permissions → 201; `sheet:fly` → 400 `field_errors.permissions`; taken slug → 409 |
| `F003-REQ-003` | FR-F003-03 | api | ACL entry with `role_id` at workspace scope grants on child sheet; 501 entries → 400 |
| `F003-REQ-004` | FR-F003-04 | api | GET shows direct + inherited with `inherited_from`; PUT replaces, version 2, `acl.updated.v1` diff |
| `F003-REQ-005` | FR-F003-05 | api | deny on folder + allow on sheet → `denied`, reason `explicit_deny`, `matched_rule.scope` = folder |
| `F003-REQ-006` | FR-F003-06 | api | guest with only tenant-scoped `Everyone` binding → 404; with direct entry → 200 |
| `F003-REQ-007` | FR-F003-07 | api | admin checks another principal → 200; member with `principal` → 403 |
| `F003-REQ-008` | FR-F003-08 | api, performance | no read → 404; read but no edit → 403; second check served from cache; ACL change invalidates |
| `F003-REQ-009` | FR-F003-09 | api, database | `record_audit` in caller tx → row + `audit.recorded.v1`; failing insert aborts mutation |
| `F003-REQ-010` | FR-F003-10 | database | UPDATE/DELETE raise `audit_immutable`; four monthly partitions exist |
| `F003-REQ-011` | FR-F003-11 | api | filters by actor, resource, action prefix, correlation, time range; owner sees own resource only; member → 403 |
| `F003-REQ-012` | FR-F003-12 | api | role and ACL mutations → audit rows with entry diff; idempotent replay returns stored body |
| `F003-REQ-013` | FR-F003-13 | api | tenant B ids on every route → 404; audit query for tenant A resource → empty page |
| `F003-REQ-014` | FR-F003-14 | frontend, e2e | matrix editor, `AclEditor` drawer, audit page with diff and copy; member sees denied |
| `F003-NFR-001` | NFR-F003-01 | performance | cached check < 5 ms; uncached 4-level < 30 ms; audit write < 10 ms; 10M-row list < 500 ms |
| `F003-NFR-002` | NFR-F003-02 | api | negative matrix green for cross-tenant, role, guest, link, field-level; redacted fields absent |
| `F003-NFR-003` | NFR-F003-03 | accessibility | matrix is a labelled table; diff as text; axe serious = 0 |
| `F003-NFR-004` | NFR-F003-04 | api | `authz_checks_total` and `audit_events_written_total` increment; span carries `resource_kind` |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F003/`.
