# F025 requirements cases

Feature: Export/drill-through. Flag `F025_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F025-REQ-001` | FR-F025-01 | api | row target returns one entry per source alias with `sheet_id`, `source_row_id`, `deep_link`, `cells`; unknown row → 404 `not_found`; `snapshot_id` pins a retained snapshot |
| `F025-REQ-002` | FR-F025-02 | api, e2e | `group:<base64url>` key pages contributing rows by cursor with `limit` 1..200 and `total` capped at 5,000; tampered tag → 400; unretained snapshot → 409 `snapshot_expired` |
| `F025-REQ-003` | FR-F025-03 | api | restricted sheet → `access: denied` with no cells and no query issued; hidden columns stripped and listed; owner policy adds `aggregate_scope` and `hidden_row_count` |
| `F025-REQ-004` | FR-F025-04 | api | every drill publishes `drill-through.opened.v1` with `denied_count` and `scope_key` and writes the `report.drill-through` audit row |
| `F025-REQ-005` | FR-F025-05 | api | report export → 202 `{ export_id, status, expires_at }` under 500 ms, row `queued` with the caller `scope_key`, `report-export.requested.v1`; `page` on csv → 400 |
| `F025-REQ-006` | FR-F025-06 | api, e2e | dashboard export with `refresh` waits up to 120 s; denied widget → title-only tile; still computing → "Not available" and `partial: true` |
| `F025-REQ-007` | FR-F025-07 | api, frontend | status returns progress, counts, size, `partial`, typed error; non-requester → 403; foreign tenant → 404 |
| `F025-REQ-008` | FR-F025-08 | api, e2e | download → 302 signed 15 minutes when completed; 409 while pending; 404 when failed or past `expires_at`; `report-export.download` audit row written |
| `F025-REQ-009` | FR-F025-09 | api, database | render claims the row, writes to a temporary key and moves on success, records `storage_key`, `checksum`, `byte_size`, `row_count`, `page_count`, publishes `report-export.completed.v1`; progress every 5 s or 10,000 rows |
| `F025-REQ-010` | FR-F025-10 | api | CSV BOM and RFC 4180 quoting; XLSX frozen typed header; PDF repeated headers, group headers, footer with page `n of m`; PNG 1440×1024 at DPR 2 |
| `F025-REQ-011` | FR-F025-11 | api, performance | 250,001 rows and a 201st column rejected; PDF over 200 pages fails `limit_exceeded`; 21st request in an hour and a 4th concurrent render → 429 with `Retry-After` |
| `F025-REQ-012` | FR-F025-12 | api | three retries then `failed` with a typed `error.code`, `report-export.failed.v1`, dead letter; repeated `Idempotency-Key` returns the same `export_id`; nightly sweep sets `expired` |
| `F025-REQ-013` | FR-F025-13 | frontend, e2e | drill panel, export dialog, and `/exports` center render loading, empty, error, denied, partial, and success states with `Download` and `Retry` |
| `F025-NFR-001` | NFR-F025-01 | performance | row drill p95 < 400 ms and group drill p95 < 900 ms on 100,000 rows; ack < 500 ms; status < 200 ms; 50,000-row CSV < 20 s; 250,000-row CSV < 120 s; 12-widget dashboard PDF < 45 s |
| `F025-NFR-002` | NFR-F025-02 | api | rendered under the requester `scope_key` with mismatch aborting; tenant-prefixed encrypted objects; 15-minute signed URLs; cross-tenant, share-link, hidden-column, and expired-download negatives |
| `F025-NFR-003` | NFR-F025-03 | accessibility | axe serious and critical = 0 on panel, dialog, and center; focus trapped and returned; progress announced; denied shown as text plus icon; PDF tagged |
| `F025-NFR-004` | NFR-F025-04 | api | renders idempotent by `(tenant_id, requested_by, idempotency_key)`, re-claim after restart leaves no partial object, metrics `report_export_duration_seconds`, `report_export_failures_total`, `drill_through_denied_total` emitted |

| `F025-REQ-016` | FR-F025-16 | frontend, api | the export centre lists a `queued`, `running`, `completed`, `failed` and `expired` job; the expired row shows its expiry and a `Re-run` action, and its download returns 404 `not_found` rather than a broken link |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F025/`.
