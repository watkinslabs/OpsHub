---
id: S098
type: story
status: planned
parent_epic: E003
parent_feature: F049
depends_on: [S097]
owned_paths: [crates/domain/src/i18n/**, services/api/src/i18n/**, apps/web/src/features/i18n/**, testing/features/F049/**]
feature_flag: F049_FEATURE
branch: s098-translations
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 6
- Capability contract: `docs/capability-contracts.md` row F049

# S098 — Translations

## Identity

- Parent feature: `F049` Localization
- Owner: platform
- Branch: `s098-translations`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 6; `docs/capability-contracts.md` row F049

## Vertical slice

As a tenant administrator, I want to set the tenant locale, timezone, week start, hour cycle, and currency, and as a user, I want to override my own locale and timezone and see the whole interface switch language and formats immediately, so that every person works in their own language over the same shared data.

## Requirements

- **SR-S098-01:** `PATCH /api/v1/tenants/{id}/locale` accepts `{ locale, timezone, first_day_of_week?, hour_cycle?, currency? }` as `tenant-admin`, rejects unsupported locales and unknown timezones with `400 invalid` field errors, requires `If-Match`, and emits `locale.updated.v1` with `scope: "tenant"` (covers FR-F049-02).
- **SR-S098-02:** `PATCH /api/v1/users/{id}/locale` succeeds for `self` or `tenant-admin`, treats `null` as clearing an override, returns `403 denied` for another user's id, and `404 not_found` for a foreign-tenant id (FR-F049-03, FR-F049-14).
- **SR-S098-03:** `I18nProvider` loads the catalog for the effective locale with `ETag` caching, exposes `t`, `formatDate`, `formatDateTime`, `formatNumber`, `formatCurrency`, falls back to the bundled `en-US` catalog per key, and emits `i18n_missing_key` telemetry (FR-F049-09, FR-F049-10).
- **SR-S098-04:** `TenantLocalePage` at `/admin/locale` renders pickers and a live `FormatPreview`, saves with `If-Match`, shows the conflict banner on `409`, and shows the denied page for non-admins (FR-F049-11).
- **SR-S098-05:** `UserLocalePage` at `/me/locale` lets a user pick overrides or `Use tenant default`; saving re-renders the app in the new locale without reload and updates `<html lang>` (FR-F049-12, NFR-F049-03).
- **SR-S098-06:** With `F049_PSEUDO_LOCALE=true` the `en-XA` catalog wraps every pattern and the E2E run flags any visible string not wrapped (FR-F049-13).
- **SR-S098-07:** Both pages pass axe with zero serious violations, comboboxes are keyboard operable, and the locale change is announced by a live region (NFR-F049-03).

## Surfaces

- Infrastructure/container: none
- Rust service/API: `crates/domain/src/i18n/{settings.rs, service.rs}`; `services/api/src/i18n/{handlers_tenant.rs, handlers_user.rs}`
- Data/migration: none new; uses tables from S097
- React/UI: `apps/web/src/features/i18n/{I18nProvider.tsx, useI18n.ts, TenantLocalePage.tsx, UserLocalePage.tsx, LocaleSelect.tsx, TimezoneSelect.tsx, WeekStartSelect.tsx, HourCycleToggle.tsx, CurrencySelect.tsx, FormatPreview.tsx, LocaleBanner.tsx, api.ts, hooks.ts, routes.ts, catalogs/*.json}`
- Mocks/fixtures: MSW handlers for the four routes; seeded catalogs; Playwright projects pinned to `TZ=Europe/Berlin` and `TZ=America/Sao_Paulo`

## TDD harness

- Test path: `testing/features/F049/{api,frontend,e2e,accessibility}/`
- Feature flag: `F049_FEATURE`
- Targeted command: `cargo xtask test-feature F049`
- Full command: `cargo xtask test-all`
- First failing tests: `tenant_locale_patch_rejects_unknown_timezone`, `user_locale_patch_other_user_denied`, `user_locale_patch_foreign_tenant_not_found`, `provider_falls_back_per_key`, `tenant_page_preview_updates_live`, `user_page_switches_locale_without_reload`, `locale_pages_have_no_serious_axe_violations`

## Exit criteria

- [ ] Requirement tests SR-S098-01 through SR-S098-07 written first and failing
- [ ] Tasks T195 and T196 complete; UI wired to the real API through the generated client
- [ ] Unit, API, React, E2E, accessibility, and permission tests pass in targeted and full modes
- [ ] Production call path named: `apps/web/src/features/i18n/I18nProvider.tsx` mounted in `apps/web/src/app/App.tsx`, pages registered at `/admin/locale` and `/me/locale` in `apps/web/src/features/i18n/routes.ts`
- [ ] Handoff evidence recorded in the F049 ticket
