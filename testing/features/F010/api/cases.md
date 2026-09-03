# F010 api cases

File: `testing/features/F010/api/{search_tests.rs,import_tests.rs,export_tests.rs}`. Flag `F010_FEATURE`.

- `search_returns_ranked_hits_with_snippets` — FR-F010-01: `q=kickoff` over seeded `Plan` → hits ordered by `ts_rank_cd`, snippet contains `<mark>kickoff</mark>`, `next_cursor` present at `limit=10`.
- `search_empty_query_invalid` — FR-F010-01: `q=` → 400 `invalid` with `field_errors.q`; `limit=101` → 400 `field_errors.limit`.
- `search_omits_unreadable_sheet_rows` — FR-F010-02: viewer of `Plan` searches "kickoff" → `Payroll` row absent even though its `acl_snapshot` is stale.
- `search_cross_tenant_returns_empty` — FR-F010-02: tenant B actor with tenant A `sheet_id` filter → 200 with zero hits, never 403.
- `search_kind_filter_groups_results` — FR-F010-01: `kind=comment` returns only comment documents with author metadata.
- `indexer_upserts_and_ignores_stale_version` — FR-F010-03: `row.updated.v1` version 5 then version 4 → document stays at 5; one `search.indexed.v1` emitted.
- `indexer_removes_soft_deleted_source` — FR-F010-03: `row.deleted.v1` removes the document; `row.restored.v1` re-creates it.
- `indexer_never_reads_file_bodies` — FR-F010-04: `file.uploaded.v1` indexes filename, MIME, size; object storage stub records zero reads.
- `import_create_rejects_oversize_file` — FR-F010-05: 51 MB `file_id` → 400 `field_errors.file_id = "too_large"`; `broken.xlsx` → `"unparseable"`.
- `import_preview_detects_types_and_duplicates` — FR-F010-06: `plan.csv` → 50 sample rows, `Estimate: number`, `Due: date`, `Status: select`, 12 duplicate matches on `Task ID`, status `previewed`.
- `import_dry_run_writes_no_rows` — FR-F010-07: `dry_run: true` → report `valid 980, invalid 20`, `import_rows` populated, `rows` count unchanged, status `dry_run`.
- `import_commit_writes_chunks_with_idempotency_keys` — FR-F010-08: 5,000 rows → five bulk calls keyed `<id>:0`…`<id>:4`, cursor advances, `import.started.v1` then `import.completed.v1`.
- `import_resumes_after_worker_kill_without_duplicates` — FR-F010-09: kill after chunk 2, restart → resumes at chunk 3; exactly 5,000 new rows; `target_row_id` unique.
- `import_update_strategy_patches_matched_rows` — FR-F010-10: `update` with key `Task ID` → matched rows patched with `If-Match`; a row changed mid-import appears in `report.conflicts`.
- `import_skip_strategy_marks_rows_skipped` — FR-F010-10: `skip` → matched `import_rows.status = skipped`, existing cells untouched; `skip` without `key_column_id` → 400.
- `import_cancel_stops_after_current_chunk` — FR-F010-11: cancel during chunk 2 → status `cancelled`, `processed_rows = 2000`, `import.failed.v1 reason=cancelled`; cancel again → 409.
- `import_dead_letters_after_three_failures` — FR-F010-12, NFR-F010-04: bulk service fails three times → status `failed`, dead-letter row, `import.failed.v1 reason=dead_letter`.
- `import_viewer_denied` — FR-F010-16, NFR-F010-02: viewer POST `/imports` → 403 `denied`, no job row.
- `import_cross_tenant_not_found` — NFR-F010-02: tenant B GET/preview/commit/cancel on tenant A job → 404.
- `export_queues_and_completes` — FR-F010-13: POST `/exports` → 202 in < 2 s; worker sets `storage_key`, `checksum`, `row_count`; `export.completed.v1`.
- `export_excludes_denied_columns` — FR-F010-14: exporter denied `Salary` → CSV, XLSX, and PDF contain no `Salary` header; unreadable rows absent.
- `export_download_requires_requester_or_admin` — FR-F010-15: requester → 302; tenant-admin → 302; other editor → 403; each success writes `export.download` audit.
- `export_download_conflict_while_running` — FR-F010-15: download on `queued` → 409 `conflict`.
- `export_expired_not_found` — FR-F010-15: clock advanced 8 days → 404 `not_found`; object removed by sweep.
- `request_span_carries_job_ids` — NFR-F010-04: spans on import and export handlers carry `tenant_id`, `job_id`, `sheet_id`, `correlation_id`.

Evidence: JUnit output and request logs under `testing/evidence/F010/api/`.
