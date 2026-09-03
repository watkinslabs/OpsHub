# F045 requirements cases

Feature: Documents/folders. Flag `F045_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F045-REQ-001` | FR-F045-01 | api | editor creates folder and doc → 201, version 1, `path` holds ancestors, doc has `current_revision` 1 |
| `F045-REQ-002` | FR-F045-02 | api, database | second "Runbooks" under same parent, different case → 409 `conflict`, `field_errors.title` |
| `F045-REQ-003` | FR-F045-03 | api, database | move folder under its own child → 400 `parent_id=cycle`; move to depth 33 → `too_deep` |
| `F045-REQ-004` | FR-F045-04 | api | PATCH title with stale `If-Match` → 409 with `current_version` |
| `F045-REQ-005` | FR-F045-05 | api, database | delete folder with 3 docs, restore → same ids; restore child under deleted parent → root, `restored_to_root` |
| `F045-REQ-006` | FR-F045-06 | api | 10,000 children → cursor pages of 100; `q=deploy` returns snippets, sorted by rank |
| `F045-REQ-007` | FR-F045-07 | api, database | POST revision with current `If-Match` → revision +1, checksum stored, event published; stale → 409 |
| `F045-REQ-008` | FR-F045-08 | api | GET revision → presigned URL expiring in 15 min; tampered object → 503 `unavailable` |
| `F045-REQ-009` | FR-F045-09 | api | 250 revisions → pages of 100 newest first with label and checksum |
| `F045-REQ-010` | FR-F045-10 | api | grant on workspace, deny on "Finance" → Finance subtree 404; `effective_role` on reads |
| `F045-REQ-011` | FR-F045-11 | api, e2e | link principal: root list 403, granted folder 200, mutations 403, 61st call 429 |
| `F045-REQ-012` | FR-F045-12 | api | hidden node and link-only node absent from `q`; present when `link_search_discoverable` |
| `F045-REQ-013` | FR-F045-13 | api, database | each mutation → one audit event, one outbox event; tenant B by id → 404 |
| `F045-REQ-014` | FR-F045-14 | frontend, e2e | tree, list, editor, history, move, trash render; viewer read-only; non-member not-found |
| `F045-NFR-001` | NFR-F045-01 | performance | 10k-child list p95 < 500 ms; 1 MB revision save p95 < 800 ms; 100k search p95 < 500 ms |
| `F045-NFR-002` | NFR-F045-02 | api | tenant predicate, guest/link negatives, 30-day link expiry suite green |
| `F045-NFR-003` | NFR-F045-03 | accessibility | axe serious = 0; tree follows ARIA pattern; restore announced |
| `F045-NFR-004` | NFR-F045-04 | api, database | spans carry tenant, document, revision, correlation; failed put rolls back; checksum metric emitted |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F045/`.
