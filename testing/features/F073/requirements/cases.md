# F073 requirements cases

Feature: Announcements and in-app help. Flag `F073_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F073-REQ-001` | FR-F073-01 | api | list returns published, unexpired, undismissed items newest first; `include_dismissed=true` adds history; cursor pages at 20 and caps at 50 |
| `F073-REQ-002` | FR-F073-02 | api | `platform-operator` publishes platform scope → 201 with `audience_size` and `content_hash`; a session holding `tenant-admin` → 403 denied |
| `F073-REQ-003` | FR-F073-03 | api | `tenant-admin` publishes tenant scope with the tenant taken from the session; a `tenant` target naming another tenant → 403 with `field_errors.targets`; audit row carries the target tuples |
| `F073-REQ-004` | FR-F073-04 | api, e2e | targets are OR within a kind and AND across kinds; `plan: enterprise` plus `role: tenant-admin` excludes an enterprise member; empty target set reaches everyone; `entitlement` matches `active` and `trial` only |
| `F073-REQ-005` | FR-F073-05 | api | publish sets `published_at`, snapshots `audience_size`, emits `announcement.published.v1`; adding users afterwards leaves `audience_size` unchanged |
| `F073-REQ-006` | FR-F073-06 | api, e2e | dismiss writes one row and returns 204; a repeat is 204 and writes nothing; the event carries no user identifier; no route or sweep removes the row |
| `F073-REQ-007` | FR-F073-07 | api | editorial edit within the 5% token threshold succeeds; a severity, target or article-slug change → 409 conflict; a superseding publish marks the original `superseded` and its dismissals stand |
| `F073-REQ-008` | FR-F073-08 | api, frontend | `info` and `change` never set `interrupting`; `action_required` without a `learn_more_article_slug` is rejected by the check constraint |
| `F073-REQ-009` | FR-F073-09 | api, e2e | one interruption per 24 h and three per 7 d; over budget the item returns `interrupting: false`; `Later` closes without dismissing; the modal is suppressed while an editor is open |
| `F073-REQ-010` | FR-F073-10 | api, frontend | help index returns the caller's locale; `context` filters to the mapped articles in `position` order; an unmapped context returns the full index with `matched: false` |
| `F073-REQ-011` | FR-F073-11 | api | article read returns the highest version; a missing translation falls back to `default_locale` with `translation_fallback: true`; content arrives only through the signed bundle import |
| `F073-REQ-012` | FR-F073-12 | api, frontend | a withdrawn slug returns 404 and the drawer renders the contextual index; a matching `If-None-Match` returns 304 |
| `F073-REQ-013` | FR-F073-13 | api, frontend | the injection corpus renders as text with no HTML, image, iframe, style or script node; a non-`https:` anchor renders as plain text |
| `F073-REQ-014` | FR-F073-14 | api, frontend | only dismissal and interruption rows exist per user; no open, dwell or click row is written; both surfaces contact no origin other than the API |
| `F073-REQ-015` | FR-F073-15 | api | tenant B admin gets 404 on tenant A's announcement; a member gets 403 on publish; a mutation without `Idempotency-Key` is rejected; `PATCH` requires `If-Match` |
| `F073-NFR-001` | NFR-F073-01 | performance | list p95 < 150 ms with 200 in scope; article p95 < 80 ms warm; 50,000-user audience resolved in < 3 s |
| `F073-NFR-002` | NFR-F073-02 | api | renderer fuzzed against the injection corpus with zero escapes; platform scope refused to every tenant role; the two per-user tables appear in the subject-access export |
| `F073-NFR-003` | NFR-F073-03 | accessibility | axe serious and critical = 0 on panel, modal and drawer; focus returns to the trigger; severity carries text plus a labelled icon; modal escapable under reduced motion |
| `F073-NFR-004` | NFR-F073-04 | api, performance | bundle import idempotent per `bundle_id` and resumable; the four metrics emit; every span carries tenant, actor and correlation ids |
| `F073-NFR-005` | NFR-F073-05 | database | a default-locale translation is required for every announcement and article version; `content_hash` is stable across row order; an unverified bundle writes nothing |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F073/`.
