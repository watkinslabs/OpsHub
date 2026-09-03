# F008 requirements cases

Feature: Grid editing. Flag `F008_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F008-REQ-001` | FR-F008-01 | api | patch 3 cells (valid, invalid, stale version) → 200 with applied/invalid/conflict per cell and summary |
| `F008-REQ-002` | FR-F008-02 | api, database | applied cell → row version +1, one `cell_history` row, one audit row, one `cell.updated.v1` |
| `F008-REQ-003` | FR-F008-03 | api | bulk cells 4,999 → applied in one transaction; 5,001 → 400 `field_errors.selection` |
| `F008-REQ-004` | FR-F008-04 | api | bulk rows 1,000 → per-row versions and one `rows.bulk-updated.v1` |
| `F008-REQ-005` | FR-F008-05 | api, database | 51 patches → 50 batches remain, oldest trimmed |
| `F008-REQ-006` | FR-F008-06 | api, e2e | undo after another user's change → 409 listing cell; clean undo → cells restored, `edit.undone.v1` |
| `F008-REQ-007` | FR-F008-07 | api | undo, new edit, redo → 409 `empty_stack`; undo, redo → cells re-applied |
| `F008-REQ-008` | FR-F008-08 | api | changes since version N → ordered entries, `next_since`, `layout` |
| `F008-REQ-009` | FR-F008-09 | api, frontend | history for a cell edited 5 times → 5 entries newest first with cursor |
| `F008-REQ-010` | FR-F008-10 | api, e2e | layout with hidden primary → 400; valid layout → stored for actor only |
| `F008-REQ-011` | FR-F008-11 | frontend, e2e | paste 3×40 TSV → 120 cells in 1 request; invalid cells badged, rest applied |
| `F008-REQ-012` | FR-F008-12 | api, frontend | fill from 2026-01-01 down 5 → consecutive dates; text repeats |
| `F008-REQ-013` | FR-F008-13 | frontend, performance | 100,000×500 sheet → ≤ 60 rows and ≤ 40 columns in DOM; Shift/Ctrl selection |
| `F008-REQ-014` | FR-F008-14 | frontend, e2e | resize, reorder, hide, freeze → persisted within 1 s and restored on reload |
| `F008-REQ-015` | FR-F008-15 | api, frontend | viewer/commenter mutate → 403; foreign tenant → 404; read-only cells |
| `F008-REQ-016` | FR-F008-16 | api | replay same key → stored response, no second write; different body → 409 |
| `F008-NFR-001` | NFR-F008-01 | performance | cell write p95 < 800 ms; 5,000-cell bulk < 5 s; feed < 500 ms; scroll frames ≤ 32 ms |
| `F008-NFR-002` | NFR-F008-02 | api | 1,000 concurrent editors no lost updates; role and tenant negatives green |
| `F008-NFR-003` | NFR-F008-03 | accessibility | axe serious = 0; grid roles; keyboard-only edit; live region for undo |
| `F008-NFR-004` | NFR-F008-04 | api | spans carry tenant, sheet, batch, cell count, correlation; conflict metrics emitted |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F008/`.
