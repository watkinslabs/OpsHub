# F050 requirements cases

Feature: Dynamic View. Flag `F050_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F050-REQ-001` | FR-F050-01 | api | owner creates view → 201, version 1, policy `edit_mode: none`, no visible fields |
| `F050-REQ-002` | FR-F050-02 | api, database | policy with editable field not in visible → 400 `field_errors.editable_fields`; depth 5 → 400 |
| `F050-REQ-003` | FR-F050-03 | api, database | `allow_new_rows` with `edit_mode: none` → 400; `assigned_rows` without assignment column → 400 |
| `F050-REQ-004` | FR-F050-04 | api | vendor requests `fields=Task,Budget` → Budget absent; `filter` on Budget ignored; 500-row pages |
| `F050-REQ-005` | FR-F050-05 | api | token with 31-day expiry → 400; public response has no tenant/workspace/sheet ids |
| `F050-REQ-006` | FR-F050-06 | api | patch non-editable column → 403 `not_editable`; editable column applied via F008 with `on_behalf_of` |
| `F050-REQ-007` | FR-F050-07 | api, database | accepted edit → one `dynamic_view_edits` row and cell history entry with view origin |
| `F050-REQ-008` | FR-F050-08 | api | token edit without `Idempotency-Key` → 400; 61st edit in a minute → 429; revoked → 403 |
| `F050-REQ-009` | FR-F050-09 | api | delete view → token and shares inert; applied edits remain in the sheet |
| `F050-REQ-010` | FR-F050-10 | api, database | each mutation → one audit row and one `dynamic-view.updated.v1` or `row-edited.v1` outbox row |
| `F050-REQ-011` | FR-F050-11 | api | non-entitled tenant → 403 `field_errors.module`; fourth view with `max_views 3` → 409 `field_errors.limit` |
| `F050-REQ-012` | FR-F050-12 | api | tenant B and unshared sheet viewer → 404 on every route |
| `F050-REQ-013` | FR-F050-13 | frontend, e2e | vendor grid shows 3 columns, locked cells, edits; dead token shows inactive page |
| `F050-REQ-014` | FR-F050-14 | frontend, e2e | owner builds policy, previews as vendor 1, copies link, revokes it |
| `F050-NFR-001` | NFR-F050-01 | performance | 100k rows filtered p95 < 500 ms; edit p95 < 800 ms; token resolve < 20 ms |
| `F050-NFR-002` | NFR-F050-02 | api | hidden values absent from bodies, events, audit, logs; token stored as SHA-256 |
| `F050-NFR-003` | NFR-F050-03 | accessibility | axe serious = 0; editable/read-only cells announced; keyboard reachable |
| `F050-NFR-004` | NFR-F050-04 | api, database | span carries view and hashed token prefix; failed cell apply rolls back the edit row |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F050/`.
