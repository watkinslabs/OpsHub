---
id: S146
type: story
status: planned
parent_epic: E003
parent_feature: F073
depends_on: [F002, F037]
owned_paths: [crates/domain/src/announcements/**, crates/persistence/src/announcements/**, services/api/src/announcements/**, services/worker/src/announcements/**, apps/web/src/features/announcements/**, services/api/migrations/*_announcements_*.sql, testing/features/F073/**]
feature_flag: F073_FEATURE
branch: s146-contextual-help
started_at: null
finished_at: null
---

# S146 — Contextual help

## Identity

- Parent feature: `F073` Announcements and in-app help
- Owner: platform
- Branch: `s146-contextual-help`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3; `docs/capability-contracts.md` row F073; `docs/authorization-model.md` section 2; `docs/engineering-standards.md`

## Vertical slice

As a person part-way through a task, I want the help for the screen I am on to open beside it in my own language without losing my place, and a stale link to land me on the help index rather than a broken page, so that I can find out what a control does without abandoning the work I was doing.

## Requirements

- **SR-S146-01:** `GET /api/v1/help/articles` returns the help index for the caller's effective F049 locale, and with `context=<screen_key>` returns only the articles mapped to that key by `help_article_contexts` in `position` order with `matched: true`; an unmapped or unknown key returns the full index with `matched: false` rather than an error (covers FR-F073-10).
- **SR-S146-02:** `GET /api/v1/help/articles/{slug}` returns the highest `help_article_versions.version` of that article with its title, body and `updated_at`; an article is immutable per version and addressed only by `slug`, so a link never points at mutable text (FR-F073-11, NFR-F073-05).
- **SR-S146-03:** A locale with no `help_article_translations` row for the resolved version falls back to the article's `default_locale`, sets `translation_fallback: true`, and increments `help_article_fallback_total{locale}`, applying the same per-key fallback rule F049 uses for UI strings (FR-F073-11, NFR-F073-04, NFR-F073-05).
- **SR-S146-04:** An unknown or withdrawn slug returns `404 not_found` and the drawer renders the contextual index with a one-line note instead of an error page, so a stale contextual link degrades rather than breaks; help responses carry no tenant data and are served with a strong `ETag` per slug, version and locale (FR-F073-12, NFR-F073-01).
- **SR-S146-05:** Help articles are content, not code: the worker job `announcements.import_help_bundle` verifies the bundle signature, then upserts `help_articles`, `help_article_versions`, `help_article_translations` and `help_article_contexts` in one `UnitOfWork` keyed by `bundle_id`; a repeated bundle is a no-op and an unsigned or corrupt bundle leaves the previous version serving and maps to `503 unavailable` (FR-F073-11, NFR-F073-04, NFR-F073-05).
- **SR-S146-06:** Article bodies render through the same `SafeDoc` node union as announcements, so authored content cannot introduce a raw HTML, image, iframe, style or script node, anchors are limited to `https:` and same-origin paths, and the drawer fetches nothing from a third-party origin (FR-F073-13, FR-F073-14, NFR-F073-02).
- **SR-S146-07:** The drawer opens from the top-bar control and from `F1`, derives its screen key from the TanStack Router match through `useHelpContext`, closes on `Escape` returning focus to its trigger, announces arrival through a polite live region, and leaves the underlying route's selection and scroll position untouched (FR-F073-10, NFR-F073-03).

## Surfaces

- Data access: `crates/persistence/src/announcements/help_article_repository.rs` holds every SQL statement for this slice through `HelpArticleRepository` with the named queries `list_index_for_locale`, `list_contextual_slugs`, `load_article_version` and `upsert_bundle_version`; the domain module, the API handlers and the import job depend on that trait and contain no SQL or connection (decision section 2.1)
- Rust service and API: `crates/domain/src/announcements/{help.rs, bundle.rs, markdown.rs}`; `services/api/src/announcements/{routes.rs, handlers_help.rs, dto.rs}`; `services/worker/src/announcements/{mod.rs, import_help_bundle.rs}`
- Data and migration: the `help_articles`, `help_article_versions`, `help_article_translations` and `help_article_contexts` tables and their indexes from ticket section 4, in the same `services/api/migrations/*_announcements_*.sql` pair as S145
- React and UI: `apps/web/src/features/announcements/{HelpDrawer.tsx, HelpIndexList.tsx, SafeMarkdown.tsx, useHelpContext.ts, api.ts, hooks.ts}`
- Mocks and fixtures: `testing/fixtures/announcements.rs` seeds a help bundle of eight `en-US` articles with four `de-DE` translations and six context mappings, plus a signed and an unsigned bundle fixture and a withdrawn slug; F049 locale resolver stub

## TDD harness

- Test path: `testing/features/F073/{api,database,frontend,e2e}/`
- Feature flag: `F073_FEATURE`
- Targeted command: `cargo xtask test-feature F073`
- Full command: `cargo xtask test-all`
- First failing tests: `help_index_filters_by_context_key`, `unknown_context_returns_full_index_unmatched`, `article_missing_translation_falls_back_to_default_locale`, `withdrawn_slug_returns_not_found`, `unsigned_bundle_leaves_previous_version_serving`, `article_body_drops_raw_html_node`, `drawer_restores_focus_to_trigger`

## Exit criteria

- [ ] Requirement tests SR-S146-01 through SR-S146-07 written first and failing
- [ ] Tasks T291 and T292 complete and wired through the `services/api` router and the `services/worker` registry
- [ ] Unit, API, database, React, E2E and accessibility tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/announcements/handlers_help.rs` mounted through `services/api/src/router.rs` under `/api/v1/help/articles`; `services/worker/src/announcements/import_help_bundle.rs` registered in `services/worker/src/registry.rs`
- [ ] Handoff evidence recorded in the F073 ticket
