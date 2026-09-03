# F035 requirements cases

Feature: Formula engine. Flag `F035_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F035-REQ-001` | FR-F035-01 | api | parse `=SUM([Estimate])*2` → AST, node_count, references with column_id; `=SUM(` → errors[0].code invalid, position 6 |
| `F035-REQ-002` | FR-F035-02 | api | labels, `@row`, `{col:}`, `{sheet:}!{col:}`, 64 arguments accepted; canonical form uses stable IDs |
| `F035-REQ-003` | FR-F035-03 | api | 10,001-node expression → 400 `too_large`; `=FOO(1)` → 400 `unsupported_function:FOO` |
| `F035-REQ-004` | FR-F035-04 | api | functions catalog lists eight groups with signature, return type, example; equals registry |
| `F035-REQ-005` | FR-F035-05 | api | each listed function evaluates fixture expectations; wrong argument type → `type_mismatch` |
| `F035-REQ-006` | FR-F035-06 | api, database | PUT formula → definition row, edges, `formula.updated.v1`; `expression: null` clears results |
| `F035-REQ-007` | FR-F035-07 | api | evaluate on one row → value/display/status without persisting; budget applied |
| `F035-REQ-008` | FR-F035-08 | api, database | results carry status and one of the five error codes; cell read returns them in `validation` |
| `F035-REQ-009` | FR-F035-09 | api | edit one child Estimate → only dependent cells recomputed in topological order; one event per column |
| `F035-REQ-010` | FR-F035-10 | api | closing cycle at PUT → 400 `cycle:<ids>`; cycle via linked sheet at recalc → cells `cycle`, `formula.failed.v1` |
| `F035-REQ-011` | FR-F035-11 | api, performance | pathological batch over 2,000 ms → remaining cells `timeout`, `formula.failed.v1` reason timeout |
| `F035-REQ-012` | FR-F035-12 | api | cross-sheet target deleted or unreadable → `missing_reference` per cell; foreign tenant at definition → 404 |
| `F035-REQ-013` | FR-F035-13 | api, frontend | formula graph returns nodes, edges, depth, has_cycle, last status |
| `F035-REQ-014` | FR-F035-14 | api | recalculate → 202 job under 2 s; second request while active → 429 `rate_limited` |
| `F035-REQ-015` | FR-F035-15 | frontend, e2e | editor shows parse error at caret, autocomplete, chips, preview, cell badges with tooltip |
| `F035-REQ-016` | FR-F035-16 | api, frontend | viewer PUT/recalculate → 403 `denied`; read-only editor; cross-tenant ids → 404 |
| `F035-NFR-001` | NFR-F035-01 | performance | parse 1,000 nodes < 20 ms; incremental recalc < 2 s on 100k rows; full recalc < 60 s |
| `F035-NFR-002` | NFR-F035-02 | api | evaluator has no I/O; fixed clock; unreadable sheet never yields a value; results absent from logs |
| `F035-NFR-003` | NFR-F035-03 | accessibility | axe serious = 0 on editor and badges; combobox keyboard flow; error announced |
| `F035-NFR-004` | NFR-F035-04 | api, performance | replayed event no-op; metrics `formula_recalc_duration_ms`, `formula_timeouts_total` present; spans carry ids |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F035/`.
