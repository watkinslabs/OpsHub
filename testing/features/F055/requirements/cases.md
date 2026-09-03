# F055 requirements cases

Feature: Calendar App. Flag `F055_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F055-REQ-001` | FR-F055-01 | api | `calendar-editor` creates a calendar with name, workspace, IANA `default_timezone`, `week_start`; blank name, 121 chars, or `Mars/Olympus` → 400 `invalid` |
| `F055-REQ-002` | FR-F055-02 | api, database | `PUT /sources` replaces 1–20 sources mapping sheet or view, start/end/duration/title/color columns; 21 sources → 400; non-date start column → 400 |
| `F055-REQ-003` | FR-F055-03 | api, performance | `GET /events?from&to&tz` returns typed events for the window; 367-day window → 400 `invalid`; response carries `hidden_sources` and the resolved `tz` |
| `F055-REQ-004` | FR-F055-04 | api | viewer without row access to source 2 sees only source 1 events and `hidden_sources: 1`; view filters from F013 apply per source |
| `F055-REQ-005` | FR-F055-05 | api, e2e | date-only column → all-day event with no offset; datetime crossing the 2026-03-29 Europe/London DST gap and the 2026-11-01 America/New_York overlap resolve to the documented instants |
| `F055-REQ-006` | FR-F055-06 | api, frontend, e2e | drag to a new date calls the F011 reschedule route with `If-Match`; stale version → 409 and the chip returns to its original slot |
| `F055-REQ-007` | FR-F055-07 | api, database | publish creates one active publication with a hashed 32-byte token and `expires_at` ≤ 30 days; `expires_in_days: 31` → 400; revoke sets `revoked_at` |
| `F055-REQ-008` | FR-F055-08 | api, e2e | `GET /public/calendars/{token}.ics` without a session streams RFC 5545 with `X-WR-CALNAME`, one `VTIMEZONE` per zone, and stable `UID`s; unknown, revoked, or expired token → 404 |
| `F055-REQ-009` | FR-F055-09 | api | the feed carries only mapped title and dates — no comments, attachments, or other column values — and never exceeds the publisher's permissions at request time |
| `F055-REQ-010` | FR-F055-10 | api | list pages by cursor and filters by `workspace_id` and name prefix; `PATCH` updates name, timezone, and week start under `expected_version` |
| `F055-REQ-011` | FR-F055-11 | api, database | every mutation requires `Idempotency-Key`, writes `audit_events`, and publishes `calendar.updated.v1` or `calendar.published.v1`; replayed key returns the first result |
| `F055-REQ-012` | FR-F055-12 | api | tenant without an active `calendar-app` entitlement → 403 `denied` on every `/api/v1/calendars*` route with the module field error |
| `F055-REQ-013` | FR-F055-13 | frontend, e2e | month, week, and agenda layouts render with timezone switcher, per-source colour legend with toggles, and the hidden-sources notice; layout and `tz` survive reload through the URL |
| `F055-REQ-014` | FR-F055-14 | api, frontend | read-only viewer sees no source editor, publish, or drag affordance; no access → not-found state; foreign-tenant calendar id → 404 |
| `F055-NFR-001` | NFR-F055-01 | performance | 31-day window over 20 sources totalling 100,000 rows p95 < 500 ms; 5,000-event ICS streams in under 2 s |
| `F055-NFR-002` | NFR-F055-02 | api, database | tokens are 256-bit random, stored as SHA-256, compared in constant time, rate limited to 60/min/token, revocable, and reveal no tenant identity |
| `F055-NFR-003` | NFR-F055-03 | accessibility | axe serious = 0 on all three layouts; roving-tabindex event grid; keyboard reschedule via `Space`, arrows, `Enter`; colour is never the only source signal |
| `F055-NFR-004` | NFR-F055-04 | performance, e2e | spans carry `tenant_id`, `calendar_id`, `source_count`, `hidden_sources`, `correlation_id`; `calendar_events_duration_seconds` and `calendar_ics_requests_total{result}` are emitted |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F055/`.
