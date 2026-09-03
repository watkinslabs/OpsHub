# F036 requirements cases

Feature: Sharing, guests, and links. Flag `F036_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F036-REQ-001` | FR-F036-01 | api | owner grants `dana` commenter on sheet → 201, version 1, `share.granted.v1` |
| `F036-REQ-002` | FR-F036-02 | api | same pair again → 409 `already_shared`; PATCH role with `If-Match` → `share.updated.v1` |
| `F036-REQ-003` | FR-F036-03 | api, database | revoke the only owner → 409 `last_owner`; revoke second owner → 200 |
| `F036-REQ-004` | FR-F036-04 | api | deny on dashboard beats workspace editor; sheet viewer narrows workspace editor; no grant → deny |
| `F036-REQ-005` | FR-F036-05 | api | list shows direct and inherited with `inherited_from`; `effect=deny` filter; editor → 403 |
| `F036-REQ-006` | FR-F036-06 | api | invite viewer 7 days → `accept_url` returned, `guest.invited.v1`; invite owner → 400 |
| `F036-REQ-007` | FR-F036-07 | api, database | accept → `guest_users` row, grant, session, `guest.accepted.v1`; expired token → 404 |
| `F036-REQ-008` | FR-F036-08 | api, e2e | guest lists only granted workspace; other sheet → 404 |
| `F036-REQ-009` | FR-F036-09 | api, database | link 14 days → URL once, `share-link.created.v1`; 31 days → 400 `max_30_days` |
| `F036-REQ-010` | FR-F036-10 | api | revoke → `share-link.revoked.v1`; resolve after → 404 |
| `F036-REQ-011` | FR-F036-11 | api | resolve → scoped token 15 min, `use_count` +1; 61st call in a minute → 429 |
| `F036-REQ-012` | FR-F036-12 | api, e2e | scoped token reads target; workspaces, search, row PATCH → 403 |
| `F036-REQ-013` | FR-F036-13 | api | grant with past `expires_at` ignored; sweeper emits `share.revoked.v1 reason expired` |
| `F036-REQ-014` | FR-F036-14 | frontend, e2e | dialog, invite form, link section, landing page render and act |
| `F036-REQ-015` | FR-F036-15 | api, database | each mutation → audit and outbox rows; tenant B → 404; editor → 403 |
| `F036-NFR-001` | NFR-F036-01 | performance | evaluation overhead p95 ≤ 5 ms; 200-grant list < 500 ms; resolve < 300 ms |
| `F036-NFR-002` | NFR-F036-02 | api, database | tokens stored as SHA-256 only; constant-time compare; traces redact tokens |
| `F036-NFR-003` | NFR-F036-03 | accessibility | axe serious = 0; role select keyboard; copy announced; focus trap |
| `F036-NFR-004` | NFR-F036-04 | api | evaluation error → `denied`; sweeper replay idempotent; metrics exported |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F036/`.
