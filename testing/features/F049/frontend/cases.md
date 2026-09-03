# F049 frontend cases

File: `testing/features/F049/frontend/{I18nProvider.test.tsx,TenantLocalePage.test.tsx,UserLocalePage.test.tsx,FormatPreview.test.tsx}`. Vitest with MSW. Flag `F049_FEATURE`.

- `provider_loads_catalog_and_renders_message` — FR-F049-08: `de-DE` catalog fetched with key `['messages','de-DE',3]`; `t('sheet.new')` renders `Neues Blatt`.
- `provider_falls_back_per_key` — FR-F049-09: missing `ja-JP` key renders the bundled `en-US` pattern and emits `i18n_missing_key` once.
- `provider_plural_and_select` — FR-F049-10: `t('rows.count', { count: 1 })` → `1 row`; `count: 2` → `2 rows`; `ja-JP` → `2 行`.
- `provider_formats_datetime_in_effective_timezone` — FR-F049-06: `2026-09-03T12:00:00Z` → `03/09/2026 09:00` for `pt-BR`/`America/Sao_Paulo`; `<time datetime>` carries the ISO instant.
- `tenant_page_preview_updates_live` — FR-F049-11: choosing `de-DE` updates preview to `03.09.2026`, `1.234.567,89`, `1.234,57 €` before save.
- `tenant_page_shows_conflict_banner_on_409` — FR-F049-11: save with stale version → banner `Tenant settings changed` with reload.
- `tenant_page_denied_for_non_admin` — FR-F049-11: editor role renders the denied page with a link to `/me/locale`.
- `user_page_switches_locale_without_reload` — FR-F049-12: saving `pt-BR` re-renders header text and sets `document.documentElement.lang = 'pt-BR'`.
- `user_page_use_tenant_default_clears_override` — FR-F049-03: selecting `Use tenant default` sends `{ locale: null, timezone: null }`.
- `timezone_select_groups_and_searches_by_offset` — FR-F049-11: typing `+02:00` lists `Europe/Berlin (UTC+02:00)`; browser timezone appears first.
- `shows_error_banner_with_correlation_id` — NFR-F049-04: 500 on save shows banner containing `correlation_id` and retry.
- `offline_disables_save` — FR-F049-11: `navigator.onLine=false` shows offline badge and disables `Save`.

Evidence: Vitest JUnit under `testing/evidence/F049/frontend/`.
