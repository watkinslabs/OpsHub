# F030 requirements cases

Feature: Jira/Salesforce/files. Flag `F030_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F030-REQ-001` | FR-F030-01 | api | registry adds six connectors to the F029 provider list with sync kinds, directions, cursor kinds, and pinned API versions; F030 never reads `oauth_tokens` |
| `F030-REQ-002` | FR-F030-02 | api | create sync → 201 `paused` version 1; unsupported direction → 400; `needs_reauth` connection → 409 |
| `F030-REQ-003` | FR-F030-03 | api | list pages by cursor and filters `connection_id`, `connector`, `kind`, `state`; detail returns mappings, cursor, last five runs |
| `F030-REQ-004` | FR-F030-04 | api | patch with `expected_version` → new version and `sync.updated.v1`; stale version → 409; activate with no mappings → 400 |
| `F030-REQ-005` | FR-F030-05 | api, database | mapping replacement is atomic; duplicate `external_field` or `column_id`, 301st mapping, and required-without-default rejected with `field_errors` |
| `F030-REQ-006` | FR-F030-06 | api | twelve transforms evaluate purely under 5 ms; unknown name → 400; transform failure marks one record `mapping_failed` |
| `F030-REQ-007` | FR-F030-07 | api | run trigger → 202 `queued` under 2 s and `sync-run.started.v1`; second trigger while running → 409; pause cancels the queued run |
| `F030-REQ-008` | FR-F030-08 | api | scheduler enqueues each cadence, skips non-active connections, and a verified Jira webhook enqueues within 30 s |
| `F030-REQ-009` | FR-F030-09 | api, database | cursor checkpoints every 500 records in the applying transaction; restart resumes from `checkpoint_record_id`; `reset_cursor_to` audited |
| `F030-REQ-010` | FR-F030-10 | api | 429/5xx retried five times with backoff and `Retry-After`; 4xx not retried; `partial` under 10% failures, `failed` at 10% pauses the sync |
| `F030-REQ-011` | FR-F030-11 | api | run history returns state, trigger, six counters, durations, cursor before/after, and 50 failed-record samples |
| `F030-REQ-012` | FR-F030-12 | api, e2e | replay from `cursor_before`; `only_failed` touches only failed records; `dry_run` writes nothing; applied records count `skipped` |
| `F030-REQ-013` | FR-F030-13 | api | both sides changed → `sync_conflicts` row with per-field values and `sync-conflict.detected.v1`; `manual` writes neither side |
| `F030-REQ-014` | FR-F030-14 | api, frontend | resolve `keep_opshub`, `keep_external`, `merge` writes both sides and publishes `sync-conflict.resolved.v1`; settled conflict → 409 |
| `F030-REQ-015` | FR-F030-15 | api | `ignore`, `mark_deleted`, `soft_delete` behave as specified; no hard delete on either side; `mark_deleted` needs a column |
| `F030-REQ-016` | FR-F030-16 | api, e2e | Jira issues sync with JQL filter, discovered custom fields, 2-minute overlap window, and transition-graph status writes |
| `F030-REQ-017` | FR-F030-17 | api | Salesforce reads by `SystemModstamp`, deletes via `getDeleted`, writes in composite batches of 200; DML keyword in SOQL rejected |
| `F030-REQ-018` | FR-F030-18 | api | Box and Dropbox folder binding downloads through the file service with scan, MIME, 100 MB and 2 GB caps; scan failure never attaches |
| `F030-REQ-019` | FR-F030-19 | api | Tableau publish replaces the datasource and stores the LUID; database connector is read-only, allowlisted, timeout-bounded, row-capped |
| `F030-REQ-020` | FR-F030-20 | api | member → 403; admin without sheet edit → 403; foreign-tenant sync, run, and conflict ids → 404; missing idempotency key → 400 |
| `F030-REQ-021` | FR-F030-21 | frontend, e2e | sync list, three-step wizard with preview, run history with failed records, replay dialogs, and conflict queue with merge chooser |
| `F030-NFR-001` | NFR-F030-01 | performance | list and conflict reads p95 < 500 ms; enqueue < 2 s; 10,000-record run < 10 min; preview < 1 s; transform < 5 ms |
| `F030-NFR-002` | NFR-F030-02 | api | no credentials in F030 tables; read-only database pool; sandboxed transforms; digest-only run logs unless `debug_payloads`; webhook signatures verified |
| `F030-NFR-003` | NFR-F030-03 | accessibility | axe serious and critical = 0 on list, wizard, mapping editor, conflict queue; keyboard mapping reorder; sequential conflict diff |
| `F030-NFR-004` | NFR-F030-04 | api, performance | runs idempotent per `(sync_id, external_id, external_version)`, resume after restart, dead-letter after 5; four metrics and run spans emitted |
| `F030-NFR-005` | NFR-F030-05 | api, database | 200 syncs per tenant, 300 mappings per sync, 5 concurrent runs per tenant, one active sync tuple; pinned API versions recorded per run |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F030/`.
