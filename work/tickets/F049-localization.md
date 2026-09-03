---
id: F049
type: feature
status: planned
priority: P2
owner: platform
estimate: 5
target_milestone: M2
parent_epic: E003
depends_on: [F005]
blocks: []
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/i18n/**, services/api/src/i18n/**, apps/web/src/features/i18n/**, services/api/migrations/*_i18n_*.sql, testing/features/F049/**]
feature_flag: F049_FEATURE
flag_default: off
branch: f049-localization
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 6
- Capability contract: `docs/capability-contracts.md` row F049

# F049 — Localization

## 1. Identity and dates

- Branch: `f049-localization`
- Capability area: cross-cutting internationalization (spec section 6 Internationalization; 5.1 timezone-aware calendar/timeline rendering; 5.6 chart timezone declaration)
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 6; `docs/capability-contracts.md` row F049
- Module slug: `i18n`

## 2. Requirement specification

### Problem and user outcome

Teams in different countries share one tenant. A date typed in Berlin must not read as a different day in São Paulo, a number exported for Paris must use the comma decimal separator, and a user working in Japanese must see the application chrome in Japanese without the tenant switching everyone else. Today there is no locale or timezone anywhere in the platform, so every feature would invent its own formatting.

As a tenant administrator, I want to set the tenant default locale, timezone, and week start, and as a user, I want to override locale and timezone for myself, so that dates, numbers, currency, and interface text render correctly for each person while stored values stay canonical.

### Functional requirements

- **FR-F049-01:** `GET /api/v1/locales` returns the supported locale list `en-US`, `en-GB`, `de-DE`, `fr-FR`, `es-ES`, `pt-BR`, `ja-JP` plus the pseudo-locale `en-XA` (only when `F049_PSEUDO_LOCALE=true`), each with `tag`, `display_name`, `catalog_version`, `first_day_of_week`, `hour_cycle`, and `decimal_separator`; the list is identical for every tenant.
- **FR-F049-02:** A `tenant-admin` can `PATCH /api/v1/tenants/{id}/locale` with `{ locale, timezone, first_day_of_week?, hour_cycle?, currency? }`; an unsupported `locale` returns `400 invalid` with `field_errors.locale = "unsupported"`, and a `timezone` not in the IANA tz database returns `400 invalid` with `field_errors.timezone = "unknown"`.
- **FR-F049-03:** A user can `PATCH /api/v1/users/{id}/locale` only for their own `id` (`self`) or as `tenant-admin`; the body accepts `{ locale?, timezone?, first_day_of_week?, hour_cycle? }` where `null` clears the override, and a non-admin patching another user receives `403 denied`.
- **FR-F049-04:** Effective settings resolve in the order user override, then tenant default, then platform default `en-US`/`UTC`/`monday`/`h12`; every authenticated response carries the resolved values in `X-OpsHub-Locale` and `X-OpsHub-Timezone` headers and `GET /api/v1/users/{id}` includes `effective_locale`.
- **FR-F049-05:** Server-side formatting for exports, emails, and notifications uses the ICU rules of the effective locale: `1234567.891` renders `1,234,567.891` for `en-US`, `1.234.567,891` for `de-DE`, and `1 234 567,891` for `fr-FR`; currency uses the tenant `currency` code with locale placement (`1.234,57 €` for `de-DE`, `€1,234.57` for `en-US`).
- **FR-F049-06:** `date` cells are stored as calendar dates with no timezone and render unchanged in every timezone; `datetime` cells are stored as UTC instants and render in the viewer's effective timezone with DST applied, so `2026-03-29T00:30:00Z` renders `01:30` in `Europe/London` and `02:30` in `Europe/Berlin`.
- **FR-F049-07:** All text input is normalized to Unicode NFC before validation and storage; length limits count grapheme clusters, so a 200-character name limit accepts 200 emoji or combining-mark sequences; invalid UTF-8 returns `400 invalid` with `field_errors.<name> = "encoding"`.
- **FR-F049-08:** `GET /api/v1/messages/{locale}` returns the ICU MessageFormat catalog `{ locale, version, fallback: "en-US", messages: { key: pattern } }` with a strong `ETag` and `Cache-Control: public, max-age=86400, immutable`; `If-None-Match` matching the current version returns `304`; an unsupported locale returns `404 not_found`.
- **FR-F049-09:** Any catalog key missing in a non-`en-US` locale falls back to the `en-US` pattern and increments the `i18n_missing_key_total{locale,key}` counter once per key per process; the web client applies the same fallback from the bundled `en-US` catalog.
- **FR-F049-10:** Plural and select forms follow ICU rules per locale: `{count, plural, one {# row} other {# rows}}` produces `1 row` and `2 rows` in `en-US`, and the `ja-JP` catalog with only `other` produces `2 行` without a missing-form error.
- **FR-F049-11:** The tenant settings page `/admin/locale` lets a `tenant-admin` pick locale, timezone, week start, hour cycle, and currency with a live preview of a date, datetime, number, and currency; saving requires `If-Match` and shows the conflict banner when the tenant version is stale.
- **FR-F049-12:** The user profile page `/me/locale` lets any user pick their own locale and timezone overrides or `Use tenant default`; saving re-renders the whole app in the new locale without a reload and emits `locale.updated.v1` with `changed_fields`.
- **FR-F049-13:** The pseudo-locale `en-XA` wraps every `en-US` pattern as `[!!! Ẽẽẽ !!!]` with 40% padding so untranslated strings and layout overflow are visible in tests; it is never listed to tenants in production.
- **FR-F049-14:** Cross-tenant `PATCH /api/v1/tenants/{id}/locale` or `PATCH /api/v1/users/{id}/locale` with an `id` from another tenant returns `404 not_found`.

### Non-functional requirements

- **NFR-F049-01 Performance:** resolving effective settings adds under 1 ms per request from an in-process cache keyed by `(tenant_id, user_id, version)`; `GET /api/v1/messages/{locale}` serves a 2,000-key catalog in under 50 ms p95 uncached and under 500 ms p95 for the first client paint in the web app (spec section 6).
- **NFR-F049-02 Security/privacy:** locale and timezone are non-sensitive but tenant-scoped; every query carries a `tenant_id` predicate; catalogs are static content with no tenant data; user overrides are readable only by self and `tenant-admin`.
- **NFR-F049-03 Accessibility:** locale and timezone pickers are native comboboxes with labels, `lang` attribute updates on `<html>` when the locale changes, screen readers announce `Language changed to Deutsch`, and formatted dates carry `<time datetime>` with the ISO value.
- **NFR-F049-04 Reliability/observability:** unknown timezone data at startup fails readiness (`/readyz` reports `tzdata: missing`); `i18n_missing_key_total`, `i18n_catalog_version`, and `i18n_resolve_duration_seconds` are exported; catalog build runs in CI and fails on malformed ICU syntax.

### Scope

Included: supported locale list, tenant and user locale/timezone settings, resolution order, ICU number/currency/date formatting on the server and browser, NFC normalization and grapheme-aware limits, message catalogs with fallback and telemetry, pseudo-locale, settings pages, headers.

Excluded: working calendars and holidays (F011), user-translated column names or cell content, right-to-left layout (no RTL locale in the supported list), machine translation, per-workspace locale, currency exchange rates.

## 3. UX specification

- Entry points: admin navigation `Settings → Locale` at `/admin/locale`; profile menu `Language & time` at `/me/locale`; first-login banner `Your tenant uses Deutsch (Deutschland). Keep or change?` when the browser locale differs from the tenant default.
- Primary flow: administrator opens `/admin/locale`, sees current locale `English (United States)` and timezone `UTC`, picks `Deutsch (Deutschland)` and `Europe/Berlin`, the preview panel updates to `03.09.2026`, `03.09.2026, 14:00`, `1.234.567,89`, `1.234,57 €`; clicks `Save`, toast `Locale saved`, other users see the new format on their next navigation; a user opens `/me/locale`, chooses `Português (Brasil)` and `America/Sao_Paulo`, saves, and the interface text and formats switch immediately.
- Loading: skeleton for the settings form and preview; Empty: not applicable (defaults always exist); Error: inline banner with `correlation_id` and retry; Success: toast; Stale/conflict: banner `Tenant settings changed` with `Reload`; Offline: save disabled with an offline badge; Denied: non-admins opening `/admin/locale` see the denied page with a link to `/me/locale`.
- Timezone picker groups by region, searches by city and by UTC offset, shows the current offset (`Europe/Berlin (UTC+02:00)`), and lists the browser-detected timezone first.
- Responsive: form and preview stack vertically under 768 px; timezone list uses a full-screen sheet on mobile.
- Keyboard: comboboxes support type-ahead, `ArrowUp`/`ArrowDown`, `Enter`, `Escape`; `Save` is reachable by `Tab`; focus returns to the changed control after save; motion respects `prefers-reduced-motion`.
- Font/icon/design tokens: Inter variable with CJK fallback stack `Noto Sans JP`; Lucide icons `Globe`, `Clock`, `Languages`, `Save`; tokens from `apps/web/src/design/tokens.css`.

## 4. Technical specification

### Rust backend

- Domain entities: `LocaleTag(String)` validated against `SUPPORTED_LOCALES`, `TimezoneId(String)` validated by `jiff::tz::TimeZone::get`, `TenantLocale { tenant_id, locale, timezone, first_day_of_week: Weekday, hour_cycle: HourCycle, currency: CurrencyCode, version, audit fields }`, `UserLocale { tenant_id, user_id, locale: Option<LocaleTag>, timezone: Option<TimezoneId>, first_day_of_week: Option<Weekday>, hour_cycle: Option<HourCycle>, version, audit fields }`, `EffectiveLocale { locale, timezone, first_day_of_week, hour_cycle, currency, source: LocaleSource }`, `MessageCatalog { locale, version, messages: BTreeMap<String, String>, etag }`.
- Use cases in `crates/domain/src/i18n/`: `list_locales`, `update_tenant_locale`, `update_user_locale`, `resolve_effective_locale`, `get_catalog`, `format_number`, `format_currency`, `format_date`, `format_datetime`, `normalize_text`, `grapheme_len`, `render_message`.
- Formatting uses the `icu` crate (`icu_decimal`, `icu_datetime`, `icu_plurals`) with compiled data for the eight locales; `jiff` provides the tz database and DST arithmetic; `unicode-normalization` provides NFC; `unicode-segmentation` provides grapheme counts; ICU MessageFormat rendering uses `icu_pattern` plus `icu_plurals` for plural and select arguments.
- API endpoints (`services/api/src/i18n/`): `GET /api/v1/locales`, `PATCH /api/v1/tenants/{id}/locale`, `PATCH /api/v1/users/{id}/locale`, `GET /api/v1/messages/{locale}`. Request bodies `UpdateTenantLocaleRequest`, `UpdateUserLocaleRequest`; responses `LocaleListResponse`, `TenantLocaleResponse`, `UserLocaleResponse { ...overrides, effective: EffectiveLocale }`, `MessageCatalogResponse`.
- Middleware `EffectiveLocaleLayer` in `services/api/src/i18n/middleware.rs` resolves settings from the gateway context and inserts `EffectiveLocale` as a request extension and the two response headers; `services/worker` email and export rendering call `resolve_effective_locale` for the recipient.
- Events: `locale.updated.v1` with `aggregate_id` = tenant id or user id, `changed_fields` listing the changed keys, and `scope: "tenant" | "user"` in the payload.
- Authorization: `tenant-admin` for tenant locale and any user; `self` for own user locale; reads of another user's overrides by a non-admin map to `denied`; foreign tenant IDs map to `not_found`.
- Validation: `locale` in supported list (`en-XA` only when the pseudo flag is on), `timezone` resolvable by `jiff`, `first_day_of_week` in `monday|sunday|saturday`, `hour_cycle` in `h12|h23`, `currency` an ISO 4217 code from the `iso_currency` list. Idempotency and `If-Match` follow the contract conventions.
- Error mapping: `LocaleError::Unsupported → 400 invalid (field_errors.locale)`, `LocaleError::UnknownTimezone → 400 invalid (field_errors.timezone)`, `LocaleError::StaleVersion → 409 conflict`, `LocaleError::CatalogNotFound → 404 not_found`, `TextError::InvalidEncoding → 400 invalid`, `AuthzError::Denied → 403 denied`.

### PostgreSQL/SQLx

- Migration `*_i18n_*.sql` creates `tenant_locales(tenant_id uuid primary key references tenants(id), locale text not null default 'en-US', timezone text not null default 'UTC', first_day_of_week text not null default 'monday', hour_cycle text not null default 'h12', currency char(3) not null default 'USD', version bigint not null default 1, created_by, created_at, updated_by, updated_at)`, `user_locales(tenant_id uuid not null, user_id uuid not null references users(id), locale text null, timezone text null, first_day_of_week text null, hour_cycle text null, version bigint not null default 1, audit fields, primary key (tenant_id, user_id))`, `message_catalogs(locale text not null, version integer not null, messages jsonb not null, etag text not null, built_at timestamptz not null, primary key (locale, version))`.
- Invariants: check constraints `locale in ('en-US','en-GB','de-DE','fr-FR','es-ES','pt-BR','ja-JP','en-XA')` on both settings tables, `hour_cycle in ('h12','h23')`, `first_day_of_week in ('monday','sunday','saturday')`; `message_catalogs.messages` must be a JSON object (check `jsonb_typeof(messages) = 'object'`); one row per tenant in `tenant_locales` created by the tenant creation transaction of F002 through a trigger in this migration.
- Indexes: `user_locales(user_id)`, `message_catalogs(locale, version desc)`; all database text columns use `COLLATE "C"` for identifiers and ICU collation `und-u-ks-level2` for user-visible sort in list queries added by later features.
- Audit events: `tenant-locale.update`, `user-locale.update` with field-level diffs.
- Retention/deletion: settings rows follow the owning tenant/user lifecycle; `message_catalogs` rows are static content refreshed by the catalog build job and never soft-deleted; migration rollback drops the trigger and the three tables.

### React/TypeScript

- Routes: `/admin/locale` (`TenantLocalePage`) and `/me/locale` (`UserLocalePage`) in `apps/web/src/features/i18n/`; components `LocaleSelect`, `TimezoneSelect`, `WeekStartSelect`, `HourCycleToggle`, `CurrencySelect`, `FormatPreview`, `LocaleBanner`; provider `I18nProvider` wrapping the app with `useI18n()` returning `t(key, args)`, `formatDate`, `formatDateTime`, `formatNumber`, `formatCurrency`, `locale`, `timezone`.
- Formatting in the browser uses `Intl.DateTimeFormat`, `Intl.NumberFormat`, and `Intl.PluralRules` with the effective locale and timezone; message rendering uses `@formatjs/intl-messageformat` pinned in `apps/web/package.json`.
- State: TanStack Query keys `['locales']`, `['tenant-locale', tenantId]`, `['user-locale', userId]`, `['messages', locale, version]`; the catalog query uses `staleTime: Infinity` and the `ETag`; a locale change invalidates `['messages']` and sets `document.documentElement.lang`.
- API client: generated `I18nApi` with `listLocales`, `updateTenantLocale`, `updateUserLocale`, `getMessages`.
- Telemetry: `locale_settings_opened`, `tenant_locale_saved`, `user_locale_saved`, `i18n_missing_key` (client) with `locale` and `key`, `locale_banner_dismissed`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F049-01 through FR-F049-14 in `testing/features/F049/requirements/cases.md`
- [ ] Failure/edge-case tests: unsupported locale, unknown timezone, DST transition instants, NFC/NFD equivalence, grapheme-cluster limit, missing catalog key, `304` on matching `ETag`, pseudo-locale hidden in production
- [ ] Permission-negative and tenant-isolation tests: non-admin patches another user → `denied`; foreign tenant ids → `not_found`; viewer cannot read another user's overrides
- [ ] Rust unit tests: `crates/domain/src/i18n/` formatting tables per locale, resolution order, plural rules, normalization
- [ ] API contract/integration tests: every route above with success and each error code, headers present on every authenticated response
- [ ] Database migration/constraint tests: check constraints, tenant trigger, catalog object check, rollback
- [ ] React component tests: `TenantLocalePage`, `UserLocalePage`, `FormatPreview`, `I18nProvider` fallback
- [ ] Browser E2E tests: admin changes tenant locale, user overrides locale, pseudo-locale run, stale conflict
- [ ] Accessibility tests: axe on both pages, `lang` attribute, live-region announcement, keyboard combobox
- [ ] Performance/load tests: resolve cache under 1 ms, catalog fetch under 50 ms p95, first paint under 500 ms

### Fast fanout configuration

- Test harness path: `testing/features/F049/`
- Feature flag: `F049_FEATURE`
- Fixture/seed factory: `testing/fixtures/i18n.rs` builds tenant A (`de-DE`, `Europe/Berlin`), tenant B (`en-US`, `UTC`), an admin, a user with a `pt-BR`/`America/Sao_Paulo` override, a user without override, and a foreign-tenant actor; catalogs for all eight locales with 2,000 keys
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T12:00:00Z`, DST fixtures at `2026-03-29T00:30:00Z` and `2026-10-25T00:30:00Z`
- Mock/stub contracts: outbox publisher recorded in memory; metrics registry captured in-process; browser `Intl` real, with `TZ` pinned per Playwright project
- Parallel isolation: one schema per test worker, tenant ID per test
- Targeted command: `cargo xtask test-feature F049`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F049/`

## 6. Acceptance criteria

```gherkin
Feature: Locale, timezone, and translations

Scenario: Tenant default applies to a user without overrides
  Given tenant "Acme" set to de-DE and Europe/Berlin
  And user "Jonas" has no override
  When Jonas requests his profile
  Then X-OpsHub-Locale is de-DE and X-OpsHub-Timezone is Europe/Berlin
  And the number 1234567.891 renders as "1.234.567,891"

Scenario: User override wins over tenant default
  Given tenant "Acme" set to de-DE
  When user "Ana" sets her locale to pt-BR and timezone to America/Sao_Paulo
  Then locale.updated.v1 is published with scope "user"
  And the datetime 2026-09-03T12:00:00Z renders as "03/09/2026 09:00"

Scenario: Non-admin cannot change another user's locale
  Given user "Ana" is not a tenant-admin
  When Ana patches the locale of user "Jonas"
  Then the response is 403 denied and Jonas's settings are unchanged

Scenario: Catalog fallback and telemetry
  Given the ja-JP catalog lacks key "sheet.restore.confirm"
  When the message is rendered for a ja-JP user
  Then the en-US pattern is returned
  And i18n_missing_key_total{locale="ja-JP",key="sheet.restore.confirm"} is 1
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F005 (workspace shell, admin navigation, profile menu); F002 tenants and users tables for foreign keys; decisions sections 2, 3, 6; contracts row F049
- Blocks: none in the plan; F011 working calendars, F013 calendar rendering, and F024 chart timezone consume `EffectiveLocale` once available
- Conflicts with: none (disjoint owned paths)
- External dependencies: `icu` crate compiled data, `jiff` tz database embedded at build, `@formatjs/intl-messageformat`
- Risks and mitigations: ICU compiled data increases binary size by about 6 MB, so only the eight locales are compiled; browser `Intl` output differs slightly across engines, so E2E asserts on the ISO `datetime` attribute and a normalized text form; tz database drift between server and browser is detected by a startup check comparing `jiff` tzdata version with the CI pinned version.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F005 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F049/`
- [ ] Migration file name and owned paths claimed
- [ ] Catalog source files for the eight locales checked into `apps/web/src/features/i18n/catalogs/` with the CI build step

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F049_FEATURE`, run down migration on an empty tenant; requests fall back to `en-US`/`UTC`
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Administrators can set a tenant locale, timezone, week start, hour cycle, and currency; users can override locale and timezone; dates, numbers, currency, and interface text render per person.
- Migration adds `tenant_locales`, `user_locales`, and `message_catalogs`; rollback drops them. Feature is off by default behind `F049_FEATURE`.
