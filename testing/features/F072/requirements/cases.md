# F072 requirements cases

Feature: Inbound email. Flag `F072_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F072-REQ-001` | FR-F072-01 | api, database | create address → 22-character local part over 110 CSPRNG bits, unique deployment-wide, no sheet or tenant substring; sixth active address on a sheet → 409 `address_limit` |
| `F072-REQ-002` | FR-F072-02 | api | list pages by cursor, filters by `sheet_id`, `status`, `sender_policy`, reassembles mappings, allow-list and 30-day counts; actor without `sheet-editor` sees no address string |
| `F072-REQ-003` | FR-F072-03 | api, e2e | DELETE revokes immediately; `rotate_from_id` mints a successor and gives the predecessor a 7-day grace with `rotated_source` tagging; a revoked local part is never reissued |
| `F072-REQ-004` | FR-F072-04 | api | forged, stale and previous-secret signatures → 403 `denied`, 403 `denied`, 200; the same `provider_message_id` twice → one message row, one sheet row, one event |
| `F072-REQ-005` | FR-F072-05 | api | `pass` → accepted path; `fail` → rejected under enforce and quarantined under quarantine; aligned `none` → accepted; unaligned `none` → rejected; `temperror` → quarantined under both; `anyone` policy still authenticates |
| `F072-REQ-006` | FR-F072-06 | api | `tenant_members` rejects an outsider; `allow_list` admits an exact address and a subdomain of a listed domain and rejects everything else with `sender_not_permitted` |
| `F072-REQ-007` | FR-F072-07 | api | unknown recipient, revoked address, DMARC failure, policy failure and rate limit produce byte-identical bounces and responses inside the measured timing floor; second bounce to the same sender within an hour is suppressed |
| `F072-REQ-008` | FR-F072-08 | api, performance | 61st message in an hour, 301st in a day, 11th from one sender and 2,001st in a tenant day → `rate_limited`; 30 MB message → `too_large` before parsing |
| `F072-REQ-009` | FR-F072-09 | api | `Auto-Submitted`, `Precedence: bulk`, `List-Id`, `List-Unsubscribe`, `X-Loop`, null return path, self-addressed sender and 26 `Received` headers → `loop_suspected` with no bounce; token past 20 uses → `thread_cap` |
| `F072-REQ-010` | FR-F072-10 | api, frontend | HTML-only body reduced to text with script, style and handlers dropped; remote image never fetched; body beginning `=` stored literally; 300 KB body truncated with `body_truncated` |
| `F072-REQ-011` | FR-F072-11 | api, e2e | accepted message → one row with subject, sanitised body, `received_at` and `from` resolved to the tenant user; `inbound-message.applied.v1` carries message, address and row ids |
| `F072-REQ-012` | FR-F072-12 | api | eleven attachments → ten offered to F017, the eleventh `rejected_count`; an executable `rejected_type`; an oversize part `rejected_size`; a detected part `quarantined`; the row is created either way |
| `F072-REQ-013` | FR-F072-13 | api, frontend | deleted target column → value in the primary column plus a `column_missing` issue and a row; sheet with no writable column → `target_unavailable` |
| `F072-REQ-014` | FR-F072-14 | api, e2e | valid plus-token → comment on its bound row attributed to the recipient; forged `In-Reply-To` without a token → new row; wrong token → `invalid_thread_token` behind the uniform bounce |
| `F072-REQ-015` | FR-F072-15 | api, frontend | log pages and filters by address, sheet, disposition, sender and date; body text, headers and the raw message are absent; foreign-tenant id → 404 |
| `F072-REQ-016` | FR-F072-16 | api, database | raw object written under `inbound-raw/`, unreachable by any route, deleted at `raw_expires_at`; metadata purged at 400 days; legal hold suspends both; sender logged as a domain |
| `F072-REQ-017` | FR-F072-17 | frontend, e2e | settings surface shows address with copy, sender policy, allow-list, mapping editor, limits, rotation and revocation; log shows accepted, rejected and quarantined entries |
| `F072-NFR-001` | NFR-F072-01 | performance | webhook ack p95 < 400 ms excluding the refusal floor; 5 MB message applied within 15 s p95; log and address reads p95 < 500 ms at 100,000 messages; 20 messages per second sustained |
| `F072-NFR-002` | NFR-F072-02 | api | entropy, timing and body uniformity, signature rotation, hashed constant-time tokens, no network fetch, no formula parse, no HTML render, no raw route, cross-tenant negatives, PII redaction |
| `F072-NFR-003` | NFR-F072-03 | accessibility | axe serious and critical = 0 on both routes and the drawer; disposition and authentication carry text; copy announced; drawer traps and restores focus |
| `F072-NFR-004` | NFR-F072-04 | api, performance | ingestion idempotent per `(provider, provider_message_id)`, resumable after restart, dead-lettered after 3 attempts; the four metrics emitted; spans carry tenant, address, message and correlation ids |
| `F072-NFR-005` | NFR-F072-05 | api | RFC 2047 and RFC 2231 headers decoded, declared charset honoured with UTF-8 fallback, invalid bytes replaced, five-deep forward parsed, unparseable tree quarantined |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F072/`.
