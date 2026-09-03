# F016 requirements cases

Feature: Comments and activity. Flag `F016_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F016-REQ-001` | FR-F016-01 | api | commenter posts on row → 201, `thread_id`, version 1 |
| `F016-REQ-002` | FR-F016-02 | api | `thread_id` bound to another row → 400 `field_errors.thread_id = target_mismatch` |
| `F016-REQ-003` | FR-F016-03 | api | 10,001-char body → 400 `field_errors.body = too_long`; 51 tokens → `too_many_mentions` |
| `F016-REQ-004` | FR-F016-04 | api | mention of `dana` → `mentions` row and `mention.created.v1`; mention of no-access user → `unresolved_mentions` |
| `F016-REQ-005` | FR-F016-05 | api | 120 threads → cursor pages of 100, `resolved=false` filter, nested comments in order |
| `F016-REQ-006` | FR-F016-06 | api | author edits inside 24 h → `edited_at`; after 24 h → 403; admin edits → 200; only new mention published |
| `F016-REQ-007` | FR-F016-07 | api | delete with replies → placeholder; without → hidden; `comment.deleted.v1` |
| `F016-REQ-008` | FR-F016-08 | api | resolve → `resolved_at`; resolve again → 409 `conflict` |
| `F016-REQ-009` | FR-F016-09 | api | activity newest first, `actor_kind=automation`, `since`/`until`, limit 200 |
| `F016-REQ-010` | FR-F016-10 | api, database | replayed `source_event_id` → one entry |
| `F016-REQ-011` | FR-F016-11 | api, database | each mutation → one audit row and one outbox row in the same transaction |
| `F016-REQ-012` | FR-F016-12 | api | viewer POST → 403; tenant B → 404 on all six routes |
| `F016-REQ-013` | FR-F016-13 | frontend, e2e | panel, combobox, resolve, activity tab render and act |
| `F016-REQ-014` | FR-F016-14 | api, frontend | row delete hides threads; restore shows them plus two entries |
| `F016-NFR-001` | NFR-F016-01 | performance | 1,000-comment list p95 < 500 ms; create p95 < 800 ms; lag p95 < 2 s |
| `F016-NFR-002` | NFR-F016-02 | api, frontend | suggestions exclude foreign/inactive; sanitizer strips XSS corpus |
| `F016-NFR-003` | NFR-F016-03 | accessibility | axe serious = 0; combobox keyboard; live region |
| `F016-NFR-004` | NFR-F016-04 | api | 5 failed projections → dead letter; metrics and spans present |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F016/`.
