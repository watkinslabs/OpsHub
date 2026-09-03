# F046 requirements cases

Feature: Live collaboration. Flag `F046_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F046-REQ-001` | FR-F046-01 | api | editor upgrade → `hello` with `durable_rev`; viewer → `read_only: true`; denied → 4403; foreign → 4404; no session → 4401 |
| `F046-REQ-002` | FR-F046-02 | api | `seq` 1, 2, 4 → third message answered `error invalid`, socket stays open |
| `F046-REQ-003` | FR-F046-03 | api, database | join → lease `expires_at = now + 30 s`, `presence.joined.v1`; no renewal for 31 s → `presence.left.v1` |
| `F046-REQ-004` | FR-F046-04 | api, database | two editors send changes concurrently → revs N+1 and N+2, acks after commit, `document.change-applied.v1` x2 |
| `F046-REQ-005` | FR-F046-05 | api | retransmit same change → same rev, one row; unknown deps → `error conflict` with `missing_deps` |
| `F046-REQ-006` | FR-F046-06 | api | 500 changes → revision posted through F045 with `If-Match`, `snapshot_rev` stamped; new joiner replays only later revs |
| `F046-REQ-007` | FR-F046-07 | api | patch with current version → ack with `row_version`, `sheet.patch-applied.v1`; stale → `conflict` with server value |
| `F046-REQ-008` | FR-F046-08 | frontend, e2e | conflict banner shows both values; `Keep mine` resubmits with server version; banner persists until chosen |
| `F046-REQ-009` | FR-F046-09 | api | `since=12` → revs 13..20 ordered, `limit` 1,000, cursor; `since` before retention → 409 with `snapshot_rev` |
| `F046-REQ-010` | FR-F046-10 | frontend, e2e | offline 2 s → `Reconnecting`; 30 s → `Changes not saved`; reconnect flushes queue in order; unload prompt |
| `F046-REQ-011` | FR-F046-11 | api | 101 messages in 1 s → `rate_limited`; third violation → 4429; 101st document session → 4429 |
| `F046-REQ-012` | FR-F046-12 | api | admin lists tenant sessions; user lists own; DELETE closes 4400; other user's session → 403 |
| `F046-REQ-013` | FR-F046-13 | api, performance | clients on node A and B → presence and change visible on the other within 1 s |
| `F046-REQ-014` | FR-F046-14 | frontend, e2e | avatars, cursors, status badge, conflict banner in editor and grid; viewer has no send controls |
| `F046-NFR-001` | NFR-F046-01 | performance | round trip p95 < 250 ms with 50 editors; 1,000 sessions < 512 MB; replay 1,000 < 500 ms |
| `F046-NFR-002` | NFR-F046-02 | api | revoked editor downgraded within 60 s; cursors not seen on another document; payload absent from logs |
| `F046-NFR-003` | NFR-F046-03 | accessibility | axe serious = 0; join announcements ≤ 1 per 5 s; status text+icon; banner keyboard resolvable |
| `F046-NFR-004` | NFR-F046-04 | api, database | duplicate fan-out message applied once; ack after commit; metrics exported; spans carry session ids |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F046/`.
