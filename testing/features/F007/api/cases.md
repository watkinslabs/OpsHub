# F007 api cases

File: `testing/features/F007/api/{column_tests.rs,validation_tests.rs,contract_tests.rs,event_tests.rs}`. Flag `F007_FEATURE`.

- `column_create_returns_version_one` — FR-F007-01: POST `/api/v1/sheets/{sheet_id}/columns` type `select` with three options → 201, `version: 1`, options ordered.
- `column_create_rejects_unknown_type_and_bad_width` — FR-F007-01: type `money` or width 20 → 400 `invalid` with `field_errors.type` / `field_errors.width`.
- `column_limit_501_rejected` — FR-F007-02: 500 seeded columns, 501st POST → 400 `column_limit`; two concurrent creates at 499 yield exactly one success.
- `column_duplicate_label_conflicts` — FR-F007-03: `status` then `Status` in the same sheet → 409 `conflict`, `field_errors.label = taken`.
- `column_rename_keeps_id_and_cells` — FR-F007-04: PATCH label → same `id`, row read returns cells under the same key.
- `column_type_change_previews_invalid` — FR-F007-05, FR-F007-06: `text` → `number` on `5`, `12`, `n/a` → `preview.invalid_count: 1`; `file` → `number` → 400 `unsupported_conversion`.
- `column_type_change_large_sheet_is_async` — FR-F007-06: 20,000-row sheet → `preview.mode: async`, cells `pending` until job completes.
- `select_archived_option_rejects_new_write` — FR-F007-07: archive `Done` → existing cell `valid`; write `Done` → `invalid` code `allowed_options`.
- `number_normalizes_with_precision` — FR-F007-08: precision 2 USD `1,234.5` → normalized `1234.50`, display `$1,234.50`; `abc` → `type_mismatch`.
- `duration_and_date_normalize_iso` — FR-F007-08, FR-F007-09: `2h 30m` → `PT2H30M`; `03/09/2026` with format `DD/MM/YYYY` → `2026-09-03`.
- `person_outside_tenant_invalid` — FR-F007-09, NFR-F007-02: user id from tenant B in `person` cell → `invalid` code `unknown_person`.
- `regex_rule_records_code_and_message` — FR-F007-10: rule `^[A-Z]{3}-\d+$` on `abc` → state `invalid`, `code: regex`, message present; 513-char pattern → 400.
- `unique_rule_flags_duplicates` — FR-F007-10: two rows with `INV-1` → both `invalid` code `unique`.
- `validate_job_acknowledges_under_two_seconds` — FR-F007-11: POST validate → `queued` in < 2 s; after job, `last_validation.invalid_count` matches fixture.
- `column_reorder_keeps_primary_first` — FR-F007-12, FR-F007-13: reorder before primary → primary still first; `column.reordered.v1` emitted.
- `primary_column_immutable` — FR-F007-13: DELETE, `hidden: true`, and type `number` on primary → 400 `field_errors.is_primary`.
- `column_delete_marks_dependents_missing` — FR-F007-14: delete referenced column → dependent formula cell state `missing reference`.
- `formula_shell_cells_read_only` — FR-F007-15: cell write to `formula` column → 400 `field_errors.cells`.
- `column_idempotent_replay_returns_original` — FR-F007-16: same key twice → one column, same body; different body → 409.
- `column_cross_tenant_not_found` — FR-F007-16: tenant B on all six routes → 404.
- `column_viewer_mutation_denied` — NFR-F007-02: viewer POST/PATCH/DELETE/reorder/validate → 403 `denied`.
- `column_stale_version_conflicts` — FR-F007-16: `If-Match: 1` against version 2 → 409 with `current_version: 2`.
- `every_column_route_matches_openapi` — FR-F007-16: each route response validates against `openapi/v1.json`.
- `each_mutation_emits_one_named_event` — FR-F007-16, NFR-F007-04: create/update/delete/reorder → exactly one `column.*.v1` outbox row with `changed_fields`.
- `request_span_carries_column_ids` — NFR-F007-04: span has `tenant_id`, `sheet_id`, `column_id`, `correlation_id`; validate job writes `job_runs`.

Evidence: JUnit output and request logs under `testing/evidence/F007/api/`.
