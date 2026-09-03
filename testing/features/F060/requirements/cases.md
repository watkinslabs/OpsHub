# F060 requirements cases

Feature: Conditional formatting. Flag `F060_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F060-REQ-001` | FR-F060-01 | api | create rule → UUIDv7 id, fractional position at end of scope, version 1, resolved `materialized`; 101st rule → `invalid` `rule_limit` and nothing written |
| `F060-REQ-002` | FR-F060-02 | api | condition leaf operators validated per F007 column type; formula leaf must parse boolean and stay under 200 AST nodes; 21 leaves or depth 5 → `invalid` with the offending leaf index |
| `F060-REQ-003` | FR-F060-03 | api, frontend | target `row` or `cells` with 1–50 same-sheet columns; deleted or foreign column → `invalid`; cell state overrides row state for the same property |
| `F060-REQ-004` | FR-F060-04 | api, accessibility | format accepts only the seven colour tokens, three text styles, six icons, 12-char badge; fill or text colour with no icon, badge, or style → `needs_non_color_signal` |
| `F060-REQ-005` | FR-F060-05 | api | rule list ordered sheet-scope first then by position, filterable by `view_id` and `enabled`, carrying `materialized`, `version`, and `last_evaluated_at` |
| `F060-REQ-006` | FR-F060-06 | api, frontend | reorder moves a rule inside its own scope, bumps version, publishes `formatting-rule.updated.v1` with `change_kind: reordered`; cross-scope target → `scope_mismatch` |
| `F060-REQ-007` | FR-F060-07 | api | matching rules apply in order, each overriding only its own properties; `stop_if_true` halts the row; disabled rules skipped; `applied_rule_ids` and per-property `winning_rule_id` returned and stable across repeat runs |
| `F060-REQ-008` | FR-F060-08 | api, e2e | sheet-scoped rule applies in every view; view-scoped rule applies only in its view and layers last; foreign `view_id` → `invalid`; deleting the view soft-deletes its rules |
| `F060-REQ-009` | FR-F060-09 | api | `include=formatting` on the F006 rows, F008 changes, and F013 view-rows reads attaches `formatting` with `row`, `cells`, `applied_rule_ids`, `hidden_inputs`, and `degraded` after permission filtering |
| `F060-REQ-010` | FR-F060-10 | api, database | formula-backed rules and rules on sheets over 20,000 rows are `materialized`; the worker upserts `formatting_states` from the seven listed events with `source_change_version` |
| `F060-REQ-011` | FR-F060-11 | api, performance | materialized state used only when `source_change_version` is current, otherwise inline evaluation plus repair; inline and materialized states identical over 5,000 rows |
| `F060-REQ-012` | FR-F060-12 | api, frontend | `POST /formatting/evaluate` returns up to 200 resolved rows without persisting, accepts a draft rule for preview, and with `explain: true` returns `matched`, `leaf_results`, and `skipped_reason` per rule |
| `F060-REQ-013` | FR-F060-13 | api | unreadable column leaf unmatched and listed in `hidden_inputs`; formula error cell matches only `is_error`; 150 ms budget exceeded → page `degraded` while the evaluate route returns `unavailable` |
| `F060-REQ-014` | FR-F060-14 | api | `PATCH` needs `If-Match` and publishes `formatting-rule.updated.v1` with `change_kind`; `DELETE` soft-deletes and publishes `formatting-rule.deleted.v1`; viewer → 403; foreign tenant → 404; audit row per mutation |
| `F060-REQ-015` | FR-F060-15 | frontend, e2e | panel lists rules in order with keyboard reorder, editor with builder and 10-row preview, legend, `Why is this row highlighted?` popover, and the signal mode switch mirrored in `signals` |
| `F060-NFR-001` | NFR-F060-01 | performance | compile 100 rules < 5 ms; 100 rules over 500 rows < 25 ms p95; view row page p95 < 550 ms; 100,000-row materialization < 90 s; no paint frame over 16 ms |
| `F060-NFR-002` | NFR-F060-02 | api | formatting computed after permission filtering and never reveals a value; formula leaves pure with a 200 ms budget; rule bodies audited, cell values never logged; cross-tenant ids → 404 |
| `F060-NFR-003` | NFR-F060-03 | accessibility | colour-only formats rejected; token pairs ≥ 4.5:1 text on fill and ≥ 3:1 icons; `aria-describedby` names applied rules; `Icon only` mode drops fills; reduced motion removes the flash; axe serious = 0 |
| `F060-NFR-004` | NFR-F060-04 | api, performance | materialization idempotent per `(rule_id, row_id, source_change_version)` and resumable; the four formatting metrics exported; spans carry `rules_version` and `correlation_id` |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F060/`.
