---
id: T196
type: task
status: planned
parent_epic: E003
parent_feature: F049
parent_story: S098
depends_on: [T195]
owned_paths: [apps/web/src/features/i18n/**, testing/features/F049/e2e/**, testing/features/F049/accessibility/**, testing/features/F049/performance/**, testing/features/F049/requirements/**]
feature_flag: F049_FEATURE
branch: t196-i18n-tests
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 6, 9
- Capability contract: `docs/capability-contracts.md` row F049

# T196 — I18n tests

## Identity

- Parent story: `S098` Translations
- Owner: platform
- Branch: `t196-i18n-tests`
- Decision references: `docs/architecture-decisions.md` sections 6, 9; `docs/capability-contracts.md` row F049

## Objective

Author the eight locale catalogs, the pseudo-locale E2E sweep, the timezone-pinned browser projects, the accessibility suite, and the performance benchmarks that prove the F049 requirements end to end.

## Specification

- Owned paths: `apps/web/src/features/i18n/catalogs/{en-US,en-GB,de-DE,fr-FR,es-ES,pt-BR,ja-JP}.json`, `apps/web/src/features/i18n/catalogs/schema.json`, `testing/features/F049/e2e/locale.spec.ts`, `testing/features/F049/e2e/pseudo.spec.ts`, `testing/features/F049/accessibility/locale.a11y.spec.ts`, `testing/features/F049/performance/resolve_bench.rs`, `testing/features/F049/performance/first_paint.spec.ts`, `testing/features/F049/requirements/cases.md`
- Contract/input: catalog files are flat JSON objects of ICU MessageFormat patterns validated against `schema.json` (keys `^[a-z0-9]+(\.[a-z0-9-]+)+$`, values non-empty strings); every key present in `en-US` must exist in every other catalog or be listed in `catalogs/<locale>.pending.txt`, and CI fails when the pending list grows; Playwright projects `berlin` (`TZ=Europe/Berlin`, `locale: de-DE`) and `saopaulo` (`TZ=America/Sao_Paulo`, `locale: pt-BR`) in `testing/features/F049/e2e/playwright.config.ts`.
- Output/behavior: `locale.spec.ts` covers admin tenant change with preview, user override without reload, stale conflict banner, and denied page; `pseudo.spec.ts` runs with `F049_PSEUDO_LOCALE=true`, visits every registered route, and fails on any visible text node not wrapped in `[!!! … !!!]` (allowlist: user data, IDs, numbers); the accessibility suite asserts zero serious axe violations, `<html lang>` update, live-region announcement, and combobox keyboard operation; `resolve_bench.rs` measures `resolve_effective_locale` under 1 ms p95 with a warm cache; `first_paint.spec.ts` measures first contentful paint with catalog load under 500 ms p95 on the CI profile.
- Dependencies: T195 pages and provider; F005 route registry for the pseudo sweep.
- Feature flag: `F049_FEATURE` and `F049_PSEUDO_LOCALE` for the pseudo project only.

## TDD

- Failing test first: `testing/features/F049/e2e/locale.spec.ts::admin_changes_tenant_locale_and_preview_updates`, `::user_override_switches_language_without_reload`, `::stale_tenant_settings_show_conflict_banner`, `::non_admin_sees_denied_on_admin_locale`; `testing/features/F049/e2e/pseudo.spec.ts::every_route_renders_only_wrapped_strings`; `testing/features/F049/accessibility/locale.a11y.spec.ts::locale_pages_have_no_serious_axe_violations`, `::html_lang_updates_on_locale_change`, `::locale_change_announced_by_live_region`, `::timezone_combobox_keyboard_operable`; `testing/features/F049/performance/resolve_bench.rs::resolve_effective_locale_p95`, `testing/features/F049/performance/first_paint.spec.ts::first_paint_with_catalog_p95`
- Targeted command: `cargo xtask test-feature F049`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: Playwright uses the real API against seeded tenants A and B; the `ja-JP` fixture catalog deliberately omits one key to exercise fallback; axe-core via Playwright

## Exit criteria

- [ ] Tests written before the catalogs and observed failing
- [ ] Catalog completeness check wired into `gates.yml` and passing for all eight locales
- [ ] E2E, accessibility, and performance lanes pass in both timezone projects
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S098
- [ ] `finished_at` recorded
