# F052 requirements cases

Feature: Data Shuttle. Flag `F052_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F052-REQ-001` | FR-F052-01 | api | data-admin creates cron import flow → 201, version 1, `next_run_at` in UTC |
| `F052-REQ-002` | FR-F052-02 | api, frontend | mapping to foreign column or `update` without keys → 400 `field_errors.mapping[i]` |
| `F052-REQ-003` | FR-F052-03 | api, database | cron `*/5 * * * *` → 400 `min_interval_15m`; valid cron stores `next_run_at` |
| `F052-REQ-004` | FR-F052-04 | api | 12 invalid rows with `max_errors 5`: `abort` → failed, 0 rows; `partial` → partial, valid rows written |
| `F052-REQ-005` | FR-F052-05 | api | 4th flow with `max_flows 3` → 409; 60 MB file → `file_too_large`; 250k rows → `too_many_rows` |
| `F052-REQ-006` | FR-F052-06 | api, performance | run request → 202 in < 2 s; second request → 409 `already_active`; scheduler records `overlap` |
| `F052-REQ-007` | FR-F052-07 | api | worker run → counts recorded; repeated checksum → `duplicate_file`, no writes |
| `F052-REQ-008` | FR-F052-08 | api, database | archive row with checksum and `retain_until`; purge deletes and marks `archive_purged` |
| `F052-REQ-009` | FR-F052-09 | api, e2e | replay → new run with `replay_of_run_id` and captured version; purged → 409 |
| `F052-REQ-010` | FR-F052-10 | api | 1,000 runs → pages of 100 newest first; detail carries 50 rejected rows and 15-min URLs |
| `F052-REQ-011` | FR-F052-11 | api, database | each run → started + completed/failed events; each mutation → audit row |
| `F052-REQ-012` | FR-F052-12 | api, e2e | tenant B without entitlement → 403 `field_errors.module`; flag off → scheduler idle |
| `F052-REQ-013` | FR-F052-13 | api | rows carry owner actor and `source = data_shuttle`; owner without edit → `sheet_denied` |
| `F052-REQ-014` | FR-F052-14 | frontend, e2e | list, editor with preview, run drawer; tenant B ids → 404 |
| `F052-NFR-001` | NFR-F052-01 | performance | 100k-row import < 10 min; ack < 2 s; run list p95 < 500 ms |
| `F052-NFR-002` | NFR-F052-02 | api | URLs expire at 15 min; credentials never in responses; rejected rows redacted |
| `F052-NFR-003` | NFR-F052-03 | accessibility | axe serious = 0; mapping table keyboard-operable; status has text |
| `F052-NFR-004` | NFR-F052-04 | api, performance | 3 retries then dead letter; metrics and spans carry tenant, flow, run, correlation |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F052/`.
