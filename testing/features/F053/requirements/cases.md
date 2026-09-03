# F053 requirements cases

Feature: DataMesh. Flag `F053_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F053-REQ-001` | FR-F053-01 | api | data-admin creates mapping with 1 key and 2 field maps → 201, version 1; same sheet → 400 |
| `F053-REQ-002` | FR-F053-02 | api, frontend | incompatible pair, 201-node expression, transform on bidirectional → 400 `field_errors.field_maps[i]` |
| `F053-REQ-003` | FR-F053-03 | api, database | 2 ambiguous keys → no match rows, 2 `ambiguous_match` conflicts; target row matched once |
| `F053-REQ-004` | FR-F053-04 | api, performance | preview → matched 840, unmatched_source 12, would_update 96, conflicts 2; nothing written; < 30 s at 100k×100k |
| `F053-REQ-005` | FR-F053-05 | api | sync → 202 in < 2 s; second → 409 `already_active`; repeated cursor → succeeded, 0 writes |
| `F053-REQ-006` | FR-F053-06 | api, e2e | run writes 96 cells with `datamesh` links; `if_empty` skips filled; `create` adds rows; `clear` empties |
| `F053-REQ-007` | FR-F053-07 | api | target-only change written back; both changed → `both_changed` conflict, no writes |
| `F053-REQ-008` | FR-F053-08 | api, frontend | conflicts page by kind/status; resolve `keep_target` applies; moved row → 409 |
| `F053-REQ-009` | FR-F053-09 | api | 5 source edits in 10 s → one run after 60 s debounce; own writes ignored; cron fires |
| `F053-REQ-010` | FR-F053-10 | api | 6th mapping with `max_mappings 5` → 409; 60k changed rows → `too_many_rows` |
| `F053-REQ-011` | FR-F053-11 | api, database | mutations → audit + `mapping.updated.v1`; run → `mapping.synced.v1`; conflict → `mapping-conflict.detected.v1` |
| `F053-REQ-012` | FR-F053-12 | api, e2e | tenant B without entitlement → 403 `field_errors.module`; flag off → listener idle |
| `F053-REQ-013` | FR-F053-13 | api | owner demoted → `sheet_denied`, no writes; tenant B ids → 404 |
| `F053-REQ-014` | FR-F053-14 | frontend, e2e | four tabs render; preview markers; conflicts side by side with resolve |
| `F053-NFR-001` | NFR-F053-01 | performance | preview < 30 s; 10k-row sync < 2 min; conflicts list p95 < 500 ms; ack < 2 s |
| `F053-NFR-002` | NFR-F053-02 | api | preview and conflicts redact unreadable columns; owner permission re-checked at run |
| `F053-NFR-003` | NFR-F053-03 | accessibility | axe serious = 0; markers and kinds have text; keyboard resolve |
| `F053-NFR-004` | NFR-F053-04 | api, performance | 3 retries then dead letter; metrics and spans carry tenant, mapping, run, correlation |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F053/`.
