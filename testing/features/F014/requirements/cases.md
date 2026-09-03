# F014 requirements cases

Feature: Forms. Flag `F014_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F014-REQ-001` | FR-F014-01 | api | form admin creates form on sheet → 201, `status: draft`, version 1, no fields |
| `F014-REQ-002` | FR-F014-02 | api, database | field with foreign `column_id` → 400 `field_errors.fields[n].column_id`; duplicate key rejected |
| `F014-REQ-003` | FR-F014-03 | api, frontend | `show_if` false → field not required, value dropped; both evaluators agree on 64 fixtures |
| `F014-REQ-004` | FR-F014-04 | api, database | publish → version frozen, token issued, `form.published.v1`; PATCH → draft 2 |
| `F014-REQ-005` | FR-F014-05 | api | rotate → old token 404; revoke → both public routes 404 |
| `F014-REQ-006` | FR-F014-06 | api | public schema body has no `sheet_id`, `column_id`, `tenant_id`, user IDs |
| `F014-REQ-007` | FR-F014-07 | api, performance | 61st submission per IP in an hour → 429 with `Retry-After`; 1,001st per token per day → 429 |
| `F014-REQ-008` | FR-F014-08 | api | bad CAPTCHA token or filled honeypot → 400 `invalid`, same body, reason recorded only in event |
| `F014-REQ-009` | FR-F014-09 | api | `email` mode without valid address → 400; `authenticated` mode without session → 403 |
| `F014-REQ-010` | FR-F014-10 | api, database | accepted submission → intake event id lower than row id, `status: accepted`, `form.submitted.v1` |
| `F014-REQ-011` | FR-F014-11 | api | replay same key → same `submission_id` and `row_id`, one row; different body → 409 |
| `F014-REQ-012` | FR-F014-12 | api, frontend | regex failure → 400 `field_errors.<key>` with configured message, rejected event |
| `F014-REQ-013` | FR-F014-13 | api | 11 files, 26 MB file, or `.exe` MIME → reason `upload_rejected`; flag off → pending attachments |
| `F014-REQ-014` | FR-F014-14 | api, frontend | `draft: true` → no row, `expires_at` +7 days; local draft restored on reload |
| `F014-REQ-015` | FR-F014-15 | api, e2e | submit after `closes_at` → reason `form_closed`; confirmation renders `{{field.title}}` |
| `F014-REQ-016` | FR-F014-16 | api, e2e | `/public/forms` response has `frame-ancestors` and no `X-Frame-Options`; iframe submit works |
| `F014-REQ-017` | FR-F014-17 | api, frontend | submissions list pages by cursor, filters by status and date, links `row_id` |
| `F014-REQ-018` | FR-F014-18 | api | tenant B reads form and submission → 404; submitter on admin routes → 403 |
| `F014-NFR-001` | NFR-F014-01 | performance | public schema p95 < 300 ms; 40-field submission p95 < 800 ms |
| `F014-NFR-002` | NFR-F014-02 | api | no session on public routes; `ip_hash` salted; payload absent from logs; negatives green |
| `F014-NFR-003` | NFR-F014-03 | accessibility | axe serious = 0 on builder and public form; errors and show/hide announced; 320 px |
| `F014-NFR-004` | NFR-F014-04 | api | spans carry form, version, submission, correlation; row failure keeps `received` with `error_code` |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F014/`.
