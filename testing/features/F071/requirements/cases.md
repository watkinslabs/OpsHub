# F071 requirements cases

Feature: Migration import. Flag `F071_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F071-REQ-001` | FR-F071-01 | api | create → `202 { id, status: analyzing }` under 2 s; destination folder still holds no sheet |
| `F071-REQ-002` | FR-F071-02 | api | `.xlsx` for excel and google-sheets, `.zip` for smartsheet and airtable; mismatch → `field_errors.file_id = "unsupported_source"`; `.xlsm` accepted, macro project never executed, `macro_dropped` written |
| `F071-REQ-003` | FR-F071-03 | api, database | 51 tabs → `tab_limit`; over-expanding zip → `expansion_limit`; 120,000-row tab truncated with blocking `row_cap_exceeded`; 401st column `excluded`; fourth concurrent migration → `429` with `Retry-After` |
| `F071-REQ-004` | FR-F071-04 | api | one `migration_sheets` row per tab with deduplicated `proposed_name`, `row_count`, `header_row_number`; headerless tab → generated names and `no_header_row` |
| `F071-REQ-005` | FR-F071-05 | api, database | one `migration_column_maps` row per source column with a type from the twelve, `confidence`, `state`, staged settings; sampler capped at 2,000 cells |
| `F071-REQ-006` | FR-F071-06 | api | 0.95/0.80 thresholds, precedence order, `text` fallback with 5 failing samples, empty column at confidence 0, `formula` never inferred from values |
| `F071-REQ-007` | FR-F071-07 | api | select cardinality rule, person email resolution at 0.90 with `unresolved_person`, single ISO 4217 code, duration formats, date order with `ambiguous_date_order` |
| `F071-REQ-008` | FR-F071-08 | api, frontend | `GET /{id}` returns sheets, column maps, 5 sample values, 20 sample rows per tab, issues, `committed_sheet_count: 0`; list pages and filters |
| `F071-REQ-009` | FR-F071-09 | api, frontend | overrides re-validated against the column contract; ambiguous without override → `field_errors.column_overrides`; second commit → `409 conflict` |
| `F071-REQ-010` | FR-F071-10 | api, e2e | `202 committing`, `migration.started.v1`, per-tab structure in one transaction, 1,000-row chunks with the stable idempotency key |
| `F071-REQ-011` | FR-F071-11 | api, e2e | resume from `cursor_row_number` with no duplicates; terminally failed tab soft-deleted; `DELETE` removes every sheet the migration created |
| `F071-REQ-012` | FR-F071-12 | api | AutoFilter → grid view filter; 6 sorts → 5 plus `view_sorts_truncated`; pivot and Smartsheet card views → `unsupported_view_kind`; Airtable CSV → column and row order with `unsupported_view_export` |
| `F071-REQ-013` | FR-F071-13 | api, e2e | resolvable cross-tab reference → `link` column and one link per row after commit; range, cross-workbook, and indirect references → text plus issue |
| `F071-REQ-014` | FR-F071-14 | api | outline levels → indent to depth 20 with `hierarchy_depth_exceeded` beyond; supported function set translated, anything else written as its value with an issue |
| `F071-REQ-015` | FR-F071-15 | api, frontend | every issue kind writes `kind`, `severity`, tab, source reference, and message; 30 MB attachment skipped with `attachment_over_size_cap`; Airtable attachment URL kept in a `link` column |
| `F071-REQ-016` | FR-F071-16 | frontend, e2e | review table, issues panel, gated `Create everything`, progress panel, completion link; viewer and commenter denied on every route |
| `F071-NFR-001` | NFR-F071-01 | performance | 20-tab analysis < 90 s; preview p95 < 800 ms at 50 tabs; 100k-row commit < 15 min; both mutations acknowledged < 2 s; parser peak memory < 512 MB |
| `F071-NFR-002` | NFR-F071-02 | api, database | `tenant_id` predicate on every query; zip path escape rejected; no socket to an external product; source deleted on `DELETE` and 7 days after terminal; foreign-tenant ids → `not_found` |
| `F071-NFR-003` | NFR-F071-03 | accessibility | axe serious and critical = 0 in both themes; labelled type selects; confidence as text plus icon; grouped issue headings; polite progress announcements; keyboard override, waive, and commit |
| `F071-NFR-004` | NFR-F071-04 | api, performance | jobs idempotent per tab and chunk; three retries then dead letter in `job_runs`; the four metrics emitted; spans carry `migration_id` and `sheet_map_id` |
| `F071-NFR-005` | NFR-F071-05 | api | two analyses of the same file produce byte-identical sheet, column map, and issue content in the same order |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F071/`.
