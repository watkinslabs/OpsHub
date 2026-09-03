---
id: T193
type: task
status: planned
parent_epic: E003
parent_feature: F049
parent_story: S097
depends_on: [S097]
owned_paths: [crates/domain/src/i18n/**, services/api/src/i18n/**, services/api/migrations/*_i18n_*.sql, testing/features/F049/api/**, testing/features/F049/database/**]
feature_flag: F049_FEATURE
branch: t193-locale-timezone-formatting
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 6
- Capability contract: `docs/capability-contracts.md` row F049

# T193 — Locale/timezone formatting

## Identity

- Parent story: `S097` Locale formatting
- Owner: platform
- Branch: `t193-locale-timezone-formatting`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 6; `docs/capability-contracts.md` row F049

## Objective

Create the i18n schema, the locale and timezone value types, the effective-locale resolver and middleware, the ICU formatting functions, and the text normalization helpers, exposed through `GET /api/v1/locales`.

## Specification

- Owned paths: `services/api/migrations/<ts>_i18n_create_tables.sql`, `services/api/migrations/<ts>_i18n_create_tables.down.sql`, `crates/domain/src/i18n/{mod.rs, locale.rs, timezone.rs, resolve.rs, format.rs, text.rs, errors.rs, schema.rs}`, `services/api/src/i18n/{mod.rs, routes.rs, middleware.rs, handlers_locales.rs, dto.rs}`
- Contract/input: DDL per F049 ticket section 4 (`tenant_locales`, `user_locales`, `message_catalogs`, check constraints, tenant-creation trigger, indexes); `LocaleTag::parse` against the supported list; `TimezoneId::parse` through `jiff::tz::TimeZone::get`; `resolve_effective_locale(tenant_id, user_id) -> EffectiveLocale` with the order user, tenant, platform default `en-US`/`UTC`/`monday`/`h12`; `format_number(f64, &EffectiveLocale)`, `format_currency(Decimal, CurrencyCode, &EffectiveLocale)`, `format_date(NaiveDate, &EffectiveLocale)`, `format_datetime(Timestamp, &EffectiveLocale)`; `normalize_text(&str) -> Result<String, TextError>` (NFC, invalid UTF-8 rejected) and `grapheme_len(&str) -> usize`.
- Output/behavior: `GET /api/v1/locales` returns `LocaleListResponse` with the eight entries and hides `en-XA` unless `F049_PSEUDO_LOCALE=true`; `EffectiveLocaleLayer` inserts `EffectiveLocale` into request extensions and stamps `X-OpsHub-Locale` and `X-OpsHub-Timezone` on every authenticated response, cached by `(tenant_id, user_id, version)` in a `moka` cache with 10-minute TTL invalidated on `locale.updated.v1`; `sqlx migrate run` and `revert` apply cleanly; `/readyz` reports `tzdata: missing` when `jiff` has no tz database.
- Dependencies: F002 `tenants` and `users` tables for foreign keys and the trigger; F004 readiness probe registry; `icu`, `jiff`, `unicode-normalization`, `unicode-segmentation` crates added to `crates/domain/Cargo.toml`.
- Feature flag: `F049_FEATURE` gates route mounting and the middleware; migration runs regardless.
- Large-table note: `tenant_locales` is one row per tenant; `user_locales` is at most one row per user; no backfill needed because the trigger seeds new tenants and the resolver treats a missing row as the platform default.

## TDD

- Failing test first: `testing/features/F049/database/migration_tests.rs::i18n_tables_exist_with_checks`, `::tenant_creation_seeds_locale_row`, `::unsupported_locale_rejected_by_check`, `::rollback_drops_tables`; `testing/features/F049/api/locale_tests.rs::locales_list_returns_supported_set`, `::pseudo_locale_hidden_without_flag`, `::effective_locale_headers_follow_resolution_order`, `::number_and_currency_format_per_locale`, `::datetime_applies_dst_for_viewer_timezone`, `::date_cell_unchanged_across_timezones`, `::text_nfc_and_grapheme_limit`
- Targeted command: `cargo xtask test-feature F049`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: schema-per-worker database from `testing/harness/db.rs`; `testing/fixtures/i18n.rs` tenants A and B, user with override; DST instants `2026-03-29T00:30:00Z` and `2026-10-25T00:30:00Z`

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; `cargo xtask check-migrations` passes
- [ ] Router and middleware mounted in `services/api/src/router.rs` behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S097
- [ ] `finished_at` recorded
