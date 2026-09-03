# F049 api cases

File: `testing/features/F049/api/{locale_tests.rs,messages_tests.rs,settings_tests.rs}`. Flag `F049_FEATURE`.

- `locales_list_returns_supported_set` — FR-F049-01: GET `/api/v1/locales` → 200 with `en-US`, `en-GB`, `de-DE`, `fr-FR`, `es-ES`, `pt-BR`, `ja-JP` and per-entry metadata; identical for tenants A and B.
- `pseudo_locale_hidden_without_flag` — FR-F049-13: `en-XA` absent unless `F049_PSEUDO_LOCALE=true`; catalog route returns 404 for it when off.
- `effective_locale_headers_follow_resolution_order` — FR-F049-04: user with `pt-BR` override → `X-OpsHub-Locale: pt-BR`; user without → tenant `de-DE`; tenant without row → `en-US`/`UTC`.
- `number_and_currency_format_per_locale` — FR-F049-05: `1234567.891` → `1,234,567.891` / `1.234.567,891` / `1 234 567,891`; `1234.567 EUR` → `€1,234.57` / `1.234,57 €`.
- `datetime_applies_dst_for_viewer_timezone` — FR-F049-06: `2026-03-29T00:30:00Z` → `01:30` in `Europe/London`, `02:30` in `Europe/Berlin`; `2026-10-25T00:30:00Z` → `01:30` in both.
- `date_cell_unchanged_across_timezones` — FR-F049-06: `2026-09-03` renders `03.09.2026` for Berlin and `03/09/2026` for São Paulo with the same calendar day.
- `text_nfc_and_grapheme_limit` — FR-F049-07: NFD `é` stored as NFC; 200 emoji accepted, 201 rejected; `0xFF` byte → 400 `field_errors.name = "encoding"`.
- `messages_returns_catalog_with_etag` — FR-F049-08: GET `/api/v1/messages/de-DE` → 200, `ETag`, `Cache-Control: public, max-age=86400, immutable`, `fallback: "en-US"`.
- `messages_etag_returns_304` — FR-F049-08: `If-None-Match` with current `ETag` → 304 and empty body.
- `messages_unsupported_locale_not_found` — FR-F049-08: GET `/api/v1/messages/xx-YY` → 404 `not_found`.
- `missing_key_falls_back_and_counts` — FR-F049-09: `ja-JP` render of `sheet.restore.confirm` → `en-US` text; `i18n_missing_key_total` = 1 after two renders.
- `plural_rules_per_locale` — FR-F049-10: `en-US` count 1/2 → `1 row`/`2 rows`; `ja-JP` `other`-only pattern → `2 行`.
- `tenant_locale_patch_updates_and_emits_event` — FR-F049-02: admin PATCH `de-DE`/`Europe/Berlin` → 200 version 2, audit row, `locale.updated.v1` with `scope: "tenant"`.
- `tenant_locale_patch_rejects_unknown_timezone` — FR-F049-02: `Mars/Olympus` → 400 `field_errors.timezone = "unknown"`; `xx-YY` → `field_errors.locale = "unsupported"`.
- `tenant_locale_patch_stale_version_conflicts` — FR-F049-11: `If-Match: 1` against version 2 → 409 with `current_version: 2`.
- `tenant_locale_patch_non_admin_denied` — FR-F049-02, NFR-F049-02: editor PATCH tenant locale → 403 `denied`.
- `user_locale_patch_self_succeeds` — FR-F049-03: self PATCH `pt-BR` → 200 with `effective.locale = pt-BR`, event `scope: "user"`.
- `user_locale_patch_null_clears_override` — FR-F049-03: `{ locale: null }` → effective falls back to tenant default.
- `user_locale_patch_other_user_denied` — FR-F049-03: non-admin PATCH another user → 403 `denied`; admin → 200.
- `user_locale_patch_foreign_tenant_not_found` — FR-F049-14: tenant B actor with tenant A user or tenant id → 404 on both routes.
- `idempotent_replay_returns_original` — FR-F049-02: same `Idempotency-Key` twice → one write; different body → 409.
- `readiness_fails_without_tzdata` — NFR-F049-04: `jiff` tz database unavailable → `/readyz` 503 with `tzdata: missing`.
- `malformed_catalog_fails_readiness` — NFR-F049-04: catalog with unbalanced `{` → startup sync error naming locale and key.

Evidence: JUnit output and request logs under `testing/evidence/F049/api/`.
