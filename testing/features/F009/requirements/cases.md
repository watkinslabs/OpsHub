# F009 requirements cases

Feature: Hierarchy and links. Flag `F009_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F009-REQ-001` | FR-F009-01 | api | indent "Design" after "Phase 1" → parent set, depth 1, path rewritten, `row.reparented.v1` |
| `F009-REQ-002` | FR-F009-02 | api | outdent child → placed after parent at parent depth; outdent root → 400 `already_root` |
| `F009-REQ-003` | FR-F009-03 | api | indent first row → `no_previous_sibling`; depth 21 → `depth_exceeded`; under own descendant → `cycle` |
| `F009-REQ-004` | FR-F009-04 | api | `GET /children` direct by child_position; `depth=all` in path order with `has_children`; deleted rows excluded |
| `F009-REQ-005` | FR-F009-05 | api, database | delete parent → descendants deleted; restore parent → restored; restore child alone → 409 |
| `F009-REQ-006` | FR-F009-06 | api | PUT rollup sum on Cost → rule stored; avg on select → 400; `function: null` clears |
| `F009-REQ-007` | FR-F009-07 | api | edit child Cost → only ancestors recomputed, `rollup.recomputed.v1` with cell_count |
| `F009-REQ-008` | FR-F009-08 | api, frontend | pending during compute; direct edit of parent → 400 `rolled_up`; childless parent blank |
| `F009-REQ-009` | FR-F009-09 | api | link Vendor cell to "Acme" → cell display "Acme", `link.created.v1` |
| `F009-REQ-010` | FR-F009-10 | api | list links as viewer without Vendors access → `target_redacted: true`, no values |
| `F009-REQ-011` | FR-F009-11 | api | PATCH target row → rechecked, `link.updated.v1`; DELETE → display cleared, `link.deleted.v1` |
| `F009-REQ-012` | FR-F009-12 | api, e2e | delete "Acme" → link broken, cell invalid `broken_link`; restore → active |
| `F009-REQ-013` | FR-F009-13 | api | pull copies target edit; push writes target; push without target edit → 403 |
| `F009-REQ-014` | FR-F009-14 | api | tenant B target → 404; viewer indent/link/rollup → 403 |
| `F009-REQ-015` | FR-F009-15 | frontend, e2e | treegrid renders guides, chips, broken badge, picker, rule editor with all states |
| `F009-REQ-016` | FR-F009-16 | api, database | each mutation → one audit event and one outbox event in the same transaction |
| `F009-NFR-001` | NFR-F009-01 | performance | 10k-descendant list p95 < 500 ms; indent p95 < 800 ms; 5k-row roll-up < 5 s |
| `F009-NFR-002` | NFR-F009-02 | api | tenant predicate on every query; redacted targets never leak via list, cell, or event |
| `F009-NFR-003` | NFR-F009-03 | accessibility | axe serious = 0; aria-level announced; broken link announced |
| `F009-NFR-004` | NFR-F009-04 | api | consumer replay is a no-op; metrics and spans carry row_id and link_id |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F009/`.
