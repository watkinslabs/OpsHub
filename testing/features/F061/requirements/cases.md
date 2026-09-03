# F061 requirements cases

Feature: Update requests. Flag `F061_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F061-REQ-001` | FR-F061-01 | api | create with 12 rows × 3 columns → 201, `status: open`, one `recipient_id` per recipient; formula or unwritable column → 400 with `field_errors.column_ids` |
| `F061-REQ-002` | FR-F061-02 | api, database | one 32-byte token per recipient, stored only as SHA-256 `token_hash`; `expires_at` defaults to `due_at + 7 days`; beyond 90 days → 400 |
| `F061-REQ-003` | FR-F061-03 | api | `scope_keys` maps `row_key`/`field_key` to row and column ids; a row deleted after send drops out and raises `removed_count` |
| `F061-REQ-004` | FR-F061-04 | api, e2e | public scope read with no session returns labels, types, current values, `row_version`; no internal ids; `no-referrer`, `noindex`, `no-store` headers |
| `F061-REQ-005` | FR-F061-05 | api | submission validates through the F007 validators, returns `field_errors.<row_key>.<field_key>`; 31st submission in an hour → 429 with `Retry-After` |
| `F061-REQ-006` | FR-F061-06 | api, database | response row written before cell apply; cells applied through the F008 path; `cell.updated.v1` and `update-request.responded.v1` published |
| `F061-REQ-007` | FR-F061-07 | api, frontend | `submit: false` writes no cells and resumes for 7 days; partial submit marks the recipient `partial`; gap with `allow_partial: false` → 400 `incomplete` |
| `F061-REQ-008` | FR-F061-08 | api, frontend | stale `row_versions` → 409 with current values, response `rejected` with reason `stale_row`, no cell written |
| `F061-REQ-009` | FR-F061-09 | api | full scope filled → recipient and request `completed`; `expires_at` passed → `expired`; later submission → 409 `closed` |
| `F061-REQ-010` | FR-F061-10 | api, performance | reminder job claims with `for update skip locked`, dedupes per `(recipient_id, sequence)`, advances the cadence, stops at max, expiry, or first response |
| `F061-REQ-011` | FR-F061-11 | api | manual remind returns `sent` and `skipped` with reasons, reuses the token; 4th within 24 h per recipient → 429 |
| `F061-REQ-012` | FR-F061-12 | api, e2e | cancel nulls every `token_hash`, cancels pending schedules, publishes `update-request.cancelled.v1`; public routes then → 404; repeat cancel → 200 |
| `F061-REQ-013` | FR-F061-13 | api | list pages and filters by `status`, `sheet_id`, `requested_by`, `due_before`; detail returns recipient states and per-cell changes; non-owner → 403 |
| `F061-REQ-014` | FR-F061-14 | api, database | four audit actions written in-transaction; recipient response records `actor_kind: 'system'` with `after.recipient`; `correlation_id` shared with `cell_history` |
| `F061-REQ-015` | FR-F061-15 | frontend, e2e | grid action opens the dialog, list and detail show status and changes, public form renders per-row cards with terminal screens |
| `F061-NFR-001` | NFR-F061-01 | performance | scope read 200×20 p95 < 300 ms; 50-cell submit p95 < 900 ms; list p95 < 500 ms; 100,000-row reminder claim < 2 s |
| `F061-NFR-002` | NFR-F061-02 | api | token hashed and constant-time compared, absent from logs and responses; out-of-scope key → 404; requester permission revoked → apply rejected; cross-tenant → 404 |
| `F061-NFR-003` | NFR-F061-03 | accessibility | axe serious/critical = 0 on dialog, list, drawer, and public form; keyboard-only completion; live-region announcements; 320 px layout |
| `F061-NFR-004` | NFR-F061-04 | api | reminder job idempotent per sequence and resumable; failed apply retried under the same key without a second notification; five metrics exported |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F061/`.
