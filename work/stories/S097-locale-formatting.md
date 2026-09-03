---
id: S097
type: story
status: planned
parent_epic: E003
parent_feature: F049
depends_on: [F005]
owned_paths: [crates/domain/src/i18n/**, services/api/src/i18n/**, services/api/migrations/*_i18n_*.sql, testing/features/F049/**]
feature_flag: F049_FEATURE
branch: s097-locale-formatting
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 6
- Capability contract: `docs/capability-contracts.md` row F049

# S097 — Locale formatting

## Identity

- Parent feature: `F049` Localization
- Owner: platform
- Branch: `s097-locale-formatting`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 6; `docs/capability-contracts.md` row F049

## Vertical slice

As any authenticated user, I want the server to resolve my effective locale and timezone and format dates, datetimes, numbers, and currency accordingly, and I want the message catalog for my locale served with caching and fallback, so that exports, emails, and the API present values the way my region expects.

## Requirements

- **SR-S097-01:** `GET /api/v1/locales` returns the eight-entry supported list with `tag`, `display_name`, `catalog_version`, `first_day_of_week`, `hour_cycle`, and `decimal_separator`; `en-XA` appears only when `F049_PSEUDO_LOCALE=true` (covers FR-F049-01, FR-F049-13).
- **SR-S097-02:** `EffectiveLocaleLayer` resolves user override, then tenant default, then `en-US`/`UTC`/`monday`/`h12`, and stamps `X-OpsHub-Locale` and `X-OpsHub-Timezone` on every authenticated response in under 1 ms from cache (FR-F049-04, NFR-F049-01).
- **SR-S097-03:** `format_number`, `format_currency`, `format_date`, and `format_datetime` produce the ICU output for each supported locale, apply DST for `datetime` values, and leave `date` values unchanged across timezones (FR-F049-05, FR-F049-06).
- **SR-S097-04:** `normalize_text` converts input to NFC, `grapheme_len` counts clusters for length limits, and invalid UTF-8 maps to `400 invalid` with `field_errors.<name> = "encoding"` (FR-F049-07).
- **SR-S097-05:** `GET /api/v1/messages/{locale}` returns the catalog with `ETag` and `Cache-Control: public, max-age=86400, immutable`, answers `304` to a matching `If-None-Match`, and returns `404 not_found` for an unsupported locale (FR-F049-08).
- **SR-S097-06:** `render_message` falls back to `en-US` for a missing key and increments `i18n_missing_key_total{locale,key}` once per key per process; plural and select arguments follow ICU rules per locale (FR-F049-09, FR-F049-10).
- **SR-S097-07:** Migration creates `tenant_locales`, `user_locales`, and `message_catalogs` with check constraints and the tenant-creation trigger; the readiness probe fails when tzdata is missing (NFR-F049-04).

## Surfaces

- Infrastructure/container: `TZ=UTC` and `ICU_DATA` build argument in the API image; no new compose services
- Rust service/API: `crates/domain/src/i18n/{mod.rs, locale.rs, timezone.rs, resolve.rs, format.rs, text.rs, catalog.rs, errors.rs}`; `services/api/src/i18n/{mod.rs, routes.rs, middleware.rs, handlers_locales.rs, handlers_messages.rs, dto.rs}`
- Data/migration: `services/api/migrations/<ts>_i18n_create_tables.sql` creating the three tables, checks, trigger, and indexes from ticket section 4
- React/UI: none in this story (S098 covers pages and the provider)
- Mocks/fixtures: `testing/fixtures/i18n.rs` tenants A (`de-DE`/`Europe/Berlin`) and B (`en-US`/`UTC`), user with `pt-BR` override, DST instants, eight seeded catalogs of 2,000 keys; in-process metrics registry

## TDD harness

- Test path: `testing/features/F049/api/`, `testing/features/F049/database/`, and `testing/features/F049/performance/`
- Feature flag: `F049_FEATURE`
- Targeted command: `cargo xtask test-feature F049`
- Full command: `cargo xtask test-all`
- First failing tests: `locales_list_returns_supported_set`, `effective_locale_headers_follow_resolution_order`, `number_and_currency_format_per_locale`, `datetime_applies_dst_for_viewer_timezone`, `text_nfc_and_grapheme_limit`, `messages_etag_returns_304`, `missing_key_falls_back_and_counts`

## Exit criteria

- [ ] Requirement tests SR-S097-01 through SR-S097-07 written first and failing
- [ ] Tasks T193 and T194 complete and wired through `services/api` router and middleware stack
- [ ] Unit, API, database, permission, and performance tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/i18n/routes.rs` mounted in `services/api/src/router.rs` and `EffectiveLocaleLayer` added in `services/api/src/middleware.rs`
- [ ] Handoff evidence recorded in the F049 ticket
