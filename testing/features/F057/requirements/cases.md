# F057 requirements cases

Feature: DAM assets. Flag `F057_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F057-REQ-001` | FR-F057-01 | api | editor registers clean PNG with title, tags, metadata → 201, version 1, draft, pending |
| `F057-REQ-002` | FR-F057-02 | api | quarantined file → 400 `field_errors.file_id = not_scanned`; unreadable file → 404 |
| `F057-REQ-003` | FR-F057-03 | api | worker renders thumbnail/preview/web for PNG and poster/preview for MP4 → 3 and 2 `asset.rendition-ready.v1` |
| `F057-REQ-004` | FR-F057-04 | api | ready → 302 signed URL 15 min; unknown kind → 404; pending → 409 |
| `F057-REQ-005` | FR-F057-05 | api, database | rights with past `valid_until` → `rights_state: expired`; event published |
| `F057-REQ-006` | FR-F057-06 | api, e2e | approval requested → pending; decision approved → `usable: true` unless expired |
| `F057-REQ-007` | FR-F057-07 | api, database | `q=logo`, `usable=true`, `mime_prefix=image` → filtered page using GIN index |
| `F057-REQ-008` | FR-F057-08 | api, database | depth 6 collection → 400; 5,001 items → 400; unreadable asset in list → 404 |
| `F057-REQ-009` | FR-F057-09 | api | archive → hidden from lists and collections, membership rows retained |
| `F057-REQ-010` | FR-F057-10 | api | stale `If-Match` → 409; replay same key → original; audit diff and `asset.updated.v1` |
| `F057-REQ-011` | FR-F057-11 | api | unentitled tenant → 403 `entitlement: dam`; foreign tenant → 404 |
| `F057-REQ-012` | FR-F057-12 | api | number field given text → 400 `field_errors.metadata.budget` |
| `F057-REQ-013` | FR-F057-13 | frontend, e2e | grid badges, drawer renditions/rights/approvals, `Not usable` reason |
| `F057-REQ-014` | FR-F057-14 | api, frontend | 3 render failures → `failed` with `error_code`; editor sees Retry |
| `F057-NFR-001` | NFR-F057-01 | performance | 200k-asset list p95 < 500 ms; thumbnail ready < 60 s p95 |
| `F057-NFR-002` | NFR-F057-02 | api | signed URL absent from logs; entitlement, tenant, ACL negatives green |
| `F057-NFR-003` | NFR-F057-03 | accessibility | axe serious = 0; alt text from title; badges have text |
| `F057-NFR-004` | NFR-F057-04 | api, performance | render job idempotent, 3 retries then dead letter, metrics labelled |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F057/`.
