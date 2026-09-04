---
id: T195
type: task
status: planned
parent_epic: E003
parent_feature: F049
parent_story: S098
depends_on: [T194]
owned_paths: [crates/domain/src/i18n/**, crates/persistence/src/i18n/**, services/api/src/i18n/**, apps/web/src/features/i18n/**, testing/features/F049/api/**, testing/features/F049/frontend/**]
feature_flag: F049_FEATURE
branch: t195-tenant-locale-settings
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 6
- Capability contract: `docs/capability-contracts.md` row F049

# T195 — Tenant locale settings

## Identity

- Parent story: `S098` Translations
- Owner: platform
- Branch: `t195-tenant-locale-settings`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 6; `docs/capability-contracts.md` row F049

## Objective

Implement the tenant and user locale mutation routes with authorization, idempotency, optimistic concurrency, audit, and outbox publication, and build the `I18nProvider`, tenant settings page, and user profile page that consume them.

## Specification

- Owned paths: `crates/domain/src/i18n/{settings.rs, service.rs}`, `crates/persistence/src/i18n/{tenant_locale_repository.rs, user_locale_repository.rs}`, `services/api/src/i18n/{handlers_tenant.rs, handlers_user.rs}`, `apps/web/src/features/i18n/{I18nProvider.tsx, useI18n.ts, TenantLocalePage.tsx, UserLocalePage.tsx, LocaleSelect.tsx, TimezoneSelect.tsx, WeekStartSelect.tsx, HourCycleToggle.tsx, CurrencySelect.tsx, FormatPreview.tsx, LocaleBanner.tsx, api.ts, hooks.ts, routes.ts}`
- Contract/input: `UpdateTenantLocaleRequest { locale, timezone, first_day_of_week?, hour_cycle?, currency? }`, `UpdateUserLocaleRequest { locale?: string | null, timezone?: string | null, first_day_of_week?: string | null, hour_cycle?: string | null }`; headers `Idempotency-Key`, `If-Match`; generated `I18nApi` client; route params `tenantId`, `userId` from the session context.
- Output/behavior: `PATCH /api/v1/tenants/{id}/locale` (`tenant-admin`) and `PATCH /api/v1/users/{id}/locale` (`self` or `tenant-admin`) return `TenantLocaleResponse` / `UserLocaleResponse { overrides, effective, version }`; validation errors map to `400 invalid` with `field_errors.locale = "unsupported"` or `field_errors.timezone = "unknown"`; another user's id maps to `403 denied`; a foreign tenant id maps to `404 not_found`; stale `If-Match` maps to `409 conflict`; the tenant write runs through `TenantLocaleRepository::upsert_tenant_locale` and the user write through `UserLocaleRepository::upsert_user_override`, with a `null` member calling `clear_user_override`, so `settings.rs`, `service.rs`, and both handlers contain no SQL; each success writes an audit row and `locale.updated.v1` with `scope` and `changed_fields` in the same `UnitOfWork` transaction as the row update and invalidates the resolver cache. `I18nProvider` fetches `['messages', locale, version]` with the `ETag`, renders `t(key, args)` through `@formatjs/intl-messageformat`, falls back per key to the bundled `en-US` catalog with `i18n_missing_key` telemetry, and sets `document.documentElement.lang`. `TenantLocalePage` at `/admin/locale` renders pickers with a live `FormatPreview` (date, datetime, number, currency), saves with `If-Match`, shows the conflict banner on `409`, and the denied page for non-admins. `UserLocalePage` at `/me/locale` offers overrides or `Use tenant default` and re-renders the app on save without reload. States: loading skeleton, error banner with `correlation_id`, offline badge, success toast. Telemetry `locale_settings_opened`, `tenant_locale_saved`, `user_locale_saved`, `locale_banner_dismissed`.
- Dependencies: T194 catalog route; F003 `authz::require(actor, Permission::TenantAdmin, tenant)` and `Permission::SelfProfile`; F004 outbox writer; F005 admin navigation and profile menu entry points.
- Feature flag: `F049_FEATURE` gates the routes and hides the navigation entries; the provider falls back to `en-US`/`UTC` when off.

## TDD

- Failing test first: `testing/features/F049/api/settings_tests.rs::tenant_locale_patch_updates_and_emits_event`, `::tenant_locale_patch_rejects_unknown_timezone`, `::tenant_locale_patch_stale_version_conflicts`, `::user_locale_patch_self_succeeds`, `::user_locale_patch_null_clears_override`, `::user_locale_patch_other_user_denied`, `::user_locale_patch_foreign_tenant_not_found`; `testing/features/F049/frontend/I18nProvider.test.tsx::provider_falls_back_per_key`, `TenantLocalePage.test.tsx::tenant_page_preview_updates_live`, `UserLocalePage.test.tsx::user_page_switches_locale_without_reload`
- Targeted command: `cargo xtask test-feature F049`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/i18n.rs` admin, self user, other user, foreign-tenant actor; MSW handlers for the four routes and seeded catalogs

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Routes mounted in `services/api/src/router.rs`; provider mounted in `apps/web/src/app/App.tsx`; pages registered in the router
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S098
- [ ] `finished_at` recorded
