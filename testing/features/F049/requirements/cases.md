# F049 requirements cases

Feature: Localization. Flag `F049_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F049-REQ-001` | FR-F049-01 | api | any user lists locales → eight entries with `tag`, `display_name`, `catalog_version`, `first_day_of_week`, `hour_cycle`, `decimal_separator`; `en-XA` only with the pseudo flag |
| `F049-REQ-002` | FR-F049-02 | api | admin patches tenant locale with `xx-YY` → 400 `field_errors.locale`; with `Mars/Olympus` → 400 `field_errors.timezone`; valid → 200 |
| `F049-REQ-003` | FR-F049-03 | api | self patch → 200; `null` clears override; other user by non-admin → 403 `denied` |
| `F049-REQ-004` | FR-F049-04 | api | user with override, user without, tenant default → headers follow user > tenant > `en-US`/`UTC` |
| `F049-REQ-005` | FR-F049-05 | api | `1234567.891` and `1234.567 EUR` → `en-US`, `de-DE`, `fr-FR` strings match ICU tables |
| `F049-REQ-006` | FR-F049-06 | api, frontend | `date` unchanged across timezones; `2026-03-29T00:30:00Z` → `01:30` London, `02:30` Berlin |
| `F049-REQ-007` | FR-F049-07 | api | NFD input stored as NFC; 200 emoji accepted at 200-cluster limit; invalid UTF-8 → 400 `encoding` |
| `F049-REQ-008` | FR-F049-08 | api | catalog → `ETag`, `Cache-Control` immutable; matching `If-None-Match` → 304; `xx-YY` → 404 |
| `F049-REQ-009` | FR-F049-09 | api, frontend | `ja-JP` missing key → `en-US` pattern; counter incremented once per key |
| `F049-REQ-010` | FR-F049-10 | api, frontend | plural `one`/`other` in `en-US`; `ja-JP` `other` only renders without error |
| `F049-REQ-011` | FR-F049-11 | frontend, e2e | admin page preview updates live; save with stale `If-Match` → conflict banner |
| `F049-REQ-012` | FR-F049-12 | frontend, e2e | user saves `pt-BR` → app re-renders without reload, `locale.updated.v1` published |
| `F049-REQ-013` | FR-F049-13 | e2e | pseudo run → every visible string wrapped; `en-XA` absent from tenant list in production |
| `F049-REQ-014` | FR-F049-14 | api | foreign tenant id on either patch route → 404 `not_found` |
| `F049-NFR-001` | NFR-F049-01 | performance | resolver p95 < 1 ms warm; 2,000-key catalog p95 < 50 ms; first paint < 500 ms |
| `F049-NFR-002` | NFR-F049-02 | api | tenant predicate on every query; non-admin cannot read another user's override |
| `F049-NFR-003` | NFR-F049-03 | accessibility | axe serious = 0; `<html lang>` updates; change announced; combobox keyboard operable |
| `F049-NFR-004` | NFR-F049-04 | api, database | missing tzdata fails `/readyz`; metrics exported; malformed catalog fails startup |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F049/`.
