# F059 requirements cases

Feature: Publishing/embedding. Flag `F059_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F059-REQ-001` | FR-F059-01 | api | publisher publishes dashboard with link access → 201, version 1, plaintext token once |
| `F059-REQ-002` | FR-F059-02 | api, database | token stored as SHA-256 only; rotate → new token, old valid 10 min then 404 |
| `F059-REQ-003` | FR-F059-03 | api | publisher loses access → render `error` with `publisher_access_lost` and no data |
| `F059-REQ-004` | FR-F059-04 | api | payload has no hidden columns, comments, attachments, tenant links; writes with token → 403 |
| `F059-REQ-005` | FR-F059-05 | api, frontend | refresh failure → `stale: true`, `X-OpsHub-Stale: true`, banner when `show_freshness` |
| `F059-REQ-006` | FR-F059-06 | api | tenant access without session → login; other tenant session → 404 |
| `F059-REQ-007` | FR-F059-07 | api, e2e | embed carries `frame-ancestors`; unlisted origin → denied state; disabled → 404 |
| `F059-REQ-008` | FR-F059-08 | api, e2e | revoke → `publication.revoked.v1`; public and embed 404 within 5 s |
| `F059-REQ-009` | FR-F059-09 | api | PATCH stale `If-Match` → 409; expiry 31 days → 400 |
| `F059-REQ-010` | FR-F059-10 | api, database | 10 renders in a minute → 1 view row; `publication.viewed.v1` once per 5 min |
| `F059-REQ-011` | FR-F059-11 | api | list filtered by readable targets with `view_count_7d`; foreign tenant → 404 |
| `F059-REQ-012` | FR-F059-12 | api, performance | 61st request in a minute → 429 with `Retry-After` |
| `F059-REQ-013` | FR-F059-13 | frontend, e2e | dialog reveals token and snippet once; list shows status and counts |
| `F059-REQ-014` | FR-F059-14 | api | token on every `/api/v1` route → 403; public page has no app links for link access |
| `F059-NFR-001` | NFR-F059-01 | performance | 12-widget render p95 < 500 ms; 10k-row refresh < 10 s |
| `F059-NFR-002` | NFR-F059-02 | api, database | hashed tokens, salted client hash, no tenant id in HTML |
| `F059-NFR-003` | NFR-F059-03 | accessibility | axe serious = 0 on public, embed, dialog; freshness as text |
| `F059-NFR-004` | NFR-F059-04 | api, performance | refresh idempotent per schedule; 3 retries then dead letter; metrics emitted |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F059/`.
