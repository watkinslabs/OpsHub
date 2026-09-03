# F010 requirements cases

Feature: Search/import/export. Flag `F010_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F010-REQ-001` | FR-F010-01 | api | search `q=kickoff&limit=10` → ranked hits with `<mark>` snippets and cursor; empty `q` → 400 `field_errors.q` |
| `F010-REQ-002` | FR-F010-02 | api | viewer of `Plan` searches → `Payroll` row omitted; foreign `sheet_id` → empty page |
| `F010-REQ-003` | FR-F010-03 | api, database | row.updated.v1 → document upserted; older `source_version` → no change; `search.indexed.v1` emitted |
| `F010-REQ-004` | FR-F010-04 | api | comment and attachment documents hold metadata only; file body never opened |
| `F010-REQ-005` | FR-F010-05 | api | 51 MB file or `broken.xlsx` → 400 `field_errors.file_id`; valid file → job `created` |
| `F010-REQ-006` | FR-F010-06 | api | preview `plan.csv` → 50 rows, detected types, proposed mapping, duplicates on `Task ID` |
| `F010-REQ-007` | FR-F010-07 | api, database | dry run → `import_rows` 980 valid / 20 invalid, report stored, sheet row count unchanged |
| `F010-REQ-008` | FR-F010-08 | api | commit → 202 in < 2 s; chunks of 1,000 with `Idempotency-Key <id>:<n>`; started and completed events |
| `F010-REQ-009` | FR-F010-09 | api, performance | worker killed after chunk 2 → resume from cursor; exactly N rows; unique `target_row_id` |
| `F010-REQ-010` | FR-F010-10 | api | skip leaves matches; update patches with `If-Match`; append duplicates; skip without key → 400 |
| `F010-REQ-011` | FR-F010-11 | api, e2e | cancel during commit → `cancelled` after chunk, rows kept, `import.failed.v1 reason=cancelled`; cancel completed → 409 |
| `F010-REQ-012` | FR-F010-12 | api, e2e | status fields present; three worker failures → `failed` with dead-letter reason |
| `F010-REQ-013` | FR-F010-13 | api | export → 202 < 2 s; worker records storage_key, checksum, row_count, requested_by; `export.completed.v1` |
| `F010-REQ-014` | FR-F010-14 | api, e2e | denied column absent in CSV/XLSX/PDF; PDF header repeats; `export.download` audit on download |
| `F010-REQ-015` | FR-F010-15 | api | download → 302 signed URL 15 min; running → 409; expired → 404; other user → 403 |
| `F010-REQ-016` | FR-F010-16 | frontend, e2e | palette, results page, wizard, status panel, export dialog; viewer has no import entry |
| `F010-NFR-001` | NFR-F010-01 | performance | search p95 < 500 ms at 1M docs; lag p95 < 5 s; 100k import < 10 min; 100k CSV export < 60 s |
| `F010-NFR-002` | NFR-F010-02 | api, database | tenant predicate on every query; export objects under tenant prefix; signed URL expiry |
| `F010-NFR-003` | NFR-F010-03 | accessibility | axe serious = 0 on palette, wizard, dialog; combobox and progress announcements |
| `F010-NFR-004` | NFR-F010-04 | api, performance | chunk idempotency, three retries then dead letter, metrics and spans carry job and tenant IDs |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F010/`.
