# F058 requirements cases

Feature: Mobile clients. Flag `F058_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F058-REQ-001` | FR-F058-01 | api, e2e | manifest has tenant name, icons, `start_url /m/home`, standalone; shell opens offline |
| `F058-REQ-002` | FR-F058-02 | api | register device → 201 bound to session; revoke other user's device → 404 |
| `F058-REQ-003` | FR-F058-03 | frontend | 500 queued ops → `Queue full` blocks edits; 8-day-old op dropped |
| `F058-REQ-004` | FR-F058-04 | api | batch of 4 ops → `applied` 4 with versions and new cursor |
| `F058-REQ-005` | FR-F058-05 | api | stale base_version on changed cell → `conflict` with `server_value`; downgraded user → `denied`; deleted row → `not_found` |
| `F058-REQ-006` | FR-F058-06 | api, database | replay `batch_id` → identical response, no second write |
| `F058-REQ-007` | FR-F058-07 | api | pull since cursor → changed and deleted rows; 8-day cursor → 400 `since = expired` |
| `F058-REQ-008` | FR-F058-08 | frontend, e2e | reconnect pushes then pulls; conflict card offers Keep mine and Take theirs |
| `F058-REQ-009` | FR-F058-09 | api, e2e | valid link → row route; bad signature → 404; unauthenticated → login then target |
| `F058-REQ-010` | FR-F058-10 | e2e | push tap opens `/m/rows/{id}` and marks notification read |
| `F058-REQ-011` | FR-F058-11 | frontend, e2e | no refresh token in localStorage; revoke wipes queue, cache, key within 5 s |
| `F058-REQ-012` | FR-F058-12 | frontend | six cell types editable; document read-only offline |
| `F058-REQ-013` | FR-F058-13 | api, database | each applied op → audit event with device id and `recorded_at` |
| `F058-REQ-014` | FR-F058-14 | api, frontend | flag off → sync and device routes 404; no install prompt |
| `F058-NFR-001` | NFR-F058-01 | performance | 100-op batch p95 < 2 s; 500-row pull p95 < 500 ms; shell < 1.5 s |
| `F058-NFR-002` | NFR-F058-02 | api | sync-time authorization; encrypted cache; deep link expires at 30 days |
| `F058-NFR-003` | NFR-F058-03 | accessibility | axe serious = 0; 44 px targets; offline state announced |
| `F058-NFR-004` | NFR-F058-04 | api, performance | batch and op idempotency; metrics emitted; shared `correlation_id` |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F058/`.
