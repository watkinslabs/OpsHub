# F005 requirements cases

Feature: Workspace navigation. Flag `F005_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F005-REQ-001` | FR-F005-01 | api | user creates workspace "Ops" → 201, version 1, creator listed as `owner` |
| `F005-REQ-002` | FR-F005-02 | api, database | second "ops" in tenant → 409 `conflict`, `field_errors.name = "taken"` |
| `F005-REQ-003` | FR-F005-03 | api | 150 workspaces, actor member of 40 → only 40 returned, cursor pages of 100, prefix and sort honoured |
| `F005-REQ-004` | FR-F005-04 | api | PATCH with stale `If-Match` → 409 with `current_version`, no write |
| `F005-REQ-005` | FR-F005-05 | api, database | delete then restore → same workspace and folder IDs; restore after retention → 404 |
| `F005-REQ-006` | FR-F005-06 | api | PUT members with no owner → 400 `owner_required`; duplicate subject → 400 `duplicate_subject` |
| `F005-REQ-007` | FR-F005-07 | api | 12-folder tree → nested nodes by position, `ETag` equals `tree_version` |
| `F005-REQ-008` | FR-F005-08 | api, database | folder at depth 11 → 400 `max_depth`; sibling name clash → 409 |
| `F005-REQ-009` | FR-F005-09 | api, database | move "Projects" under "Projects/Q4" → 400 `cycle`; valid move rewrites descendant paths, `folder.moved.v1` |
| `F005-REQ-010` | FR-F005-10 | api, database | delete folder with 3 descendants → all four carry `deleted_at`, tree omits them |
| `F005-REQ-011` | FR-F005-11 | api | editor with folder deny → tree omits that subtree; owner sees it |
| `F005-REQ-012` | FR-F005-12 | api | replay same key → identical response, one row; different body → 409 |
| `F005-REQ-013` | FR-F005-13 | api, database | each mutation → one audit event and one outbox event in the same transaction |
| `F005-REQ-014` | FR-F005-14 | api | tenant B and non-member read workspace, tree, folder → 404 |
| `F005-REQ-015` | FR-F005-15 | frontend, e2e | list, shell, tree, and dialogs render; viewer sees read-only tree |
| `F005-NFR-001` | NFR-F005-01 | performance | 2,000-folder tree p95 < 500 ms; folder move p95 < 800 ms |
| `F005-NFR-002` | NFR-F005-02 | api | role matrix, folder deny, cross-tenant, and guest negatives green |
| `F005-NFR-003` | NFR-F005-03 | accessibility | axe serious = 0; `role="tree"` semantics; keyboard move announced |
| `F005-NFR-004` | NFR-F005-04 | api, database | spans carry tenant, workspace, correlation; failed outbox insert rolls back |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F005/`.
