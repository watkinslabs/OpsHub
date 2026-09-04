---
id: T194
type: task
status: planned
parent_epic: E003
parent_feature: F049
parent_story: S097
depends_on: [T193]
owned_paths: [crates/domain/src/i18n/**, crates/persistence/src/i18n/**, services/api/src/i18n/**, testing/features/F049/api/**, testing/features/F049/performance/**, testing/features/F049/requirements/**]
feature_flag: F049_FEATURE
branch: t194-message-catalog
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 6
- Capability contract: `docs/capability-contracts.md` row F049

# T194 — Message catalog

## Identity

- Parent story: `S097` Locale formatting
- Owner: platform
- Branch: `t194-message-catalog`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 6; `docs/capability-contracts.md` row F049

## Objective

Implement the ICU MessageFormat catalog store, the `GET /api/v1/messages/{locale}` route with `ETag` caching, per-key `en-US` fallback with missing-key telemetry, plural and select rendering, and the pseudo-locale generator.

## Specification

- Owned paths: `crates/domain/src/i18n/{catalog.rs, render.rs, pseudo.rs}`, `crates/persistence/src/i18n/message_catalog_repository.rs`, `services/api/src/i18n/{handlers_messages.rs, catalog_loader.rs}`
- Contract/input: catalog source files `apps/web/src/features/i18n/catalogs/<locale>.json` (flat `key: pattern` objects, owned by T196 for content) loaded at build by `catalog_loader::sync_on_startup`, which calls `MessageCatalogRepository::replace_catalog(locale, version, entries)` to write the `message_catalogs` header (`etag`, `built_at`, `entry_count`) and every `message_catalog_entries(locale, version, message_key, pattern)` row inside one `UnitOfWork`, so a concurrent reader never sees a partial version; `MessageCatalogRepository` also exposes `latest_version(locale)`, `load_catalog(locale, version)`, and `find_pattern(locale, version, key)`, and owns all SQL for both tables — `catalog.rs`, `render.rs`, and `pseudo.rs` are pure functions over loaded values; `render_message(catalog, key, args: &MessageArgs) -> String`; `MessageArgs` supports `string`, `number`, `date`, `plural`, and `select` arguments; `pseudo::wrap(pattern) -> pattern` produces `[!!! Ẽẽẽ !!!]` with 40% padding while preserving `{argument}` placeholders.
- Output/behavior: `GET /api/v1/messages/{locale}` returns `MessageCatalogResponse { locale, version, fallback: "en-US", messages }` — one document assembled from the entry rows returned by `load_catalog` in a single query — with `ETag: "<locale>-<version>-<sha256[..16]>"` read from `message_catalogs.etag` and `Cache-Control: public, max-age=86400, immutable`; a matching `If-None-Match` returns `304` with no body; an unsupported locale returns `404 not_found`; `en-XA` is generated from the `en-US` entry rows at load time when `F049_PSEUDO_LOCALE=true`, written back as wrapped `en-XA` entry rows, and otherwise returns `404`; a key with no entry row in a non-`en-US` catalog renders the `en-US` pattern found by `find_pattern` and increments `i18n_missing_key_total{locale,key}` exactly once per key per process; malformed ICU syntax in any catalog fails `sync_on_startup` and readiness with `i18n: catalog parse error <locale>:<key>`.
- Dependencies: T193 schema, locale types, and route module; F004 metrics registry and readiness probe.
- Feature flag: `F049_FEATURE`

## TDD

- Failing test first: `testing/features/F049/api/messages_tests.rs::messages_returns_catalog_with_etag`, `::messages_etag_returns_304`, `::messages_unsupported_locale_not_found`, `::missing_key_falls_back_and_counts`, `::plural_rules_per_locale`, `::pseudo_locale_wraps_and_keeps_placeholders`, `::malformed_catalog_fails_readiness`, `::replace_catalog_is_atomic_for_readers`; `testing/features/F049/performance/catalog_bench.rs::messages_2k_keys_p95`
- Targeted command: `cargo xtask test-feature F049`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: eight seeded catalog headers with 2,000 entry rows each and a `ja-JP` catalog with no entry row for `sheet.restore.confirm`; in-process metrics registry; one deliberately malformed catalog fixture

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Catalog sync wired into API startup in `services/api/src/main.rs` behind the flag
- [ ] p95 target from NFR-F049-01 met in the performance lane
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S097
- [ ] `finished_at` recorded
