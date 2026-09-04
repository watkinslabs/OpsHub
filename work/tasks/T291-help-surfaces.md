---
id: T291
type: task
status: planned
parent_epic: E003
parent_feature: F073
parent_story: S146
depends_on: [S146]
owned_paths: [crates/domain/src/announcements/**, crates/persistence/src/announcements/**, services/api/src/announcements/**, services/worker/src/announcements/**, apps/web/src/features/announcements/**, testing/features/F073/api/**, testing/features/F073/frontend/**]
feature_flag: F073_FEATURE
branch: t291-help-surfaces
started_at: null
finished_at: null
---

# T291 — Help surfaces

## Identity

- Parent story: `S146` Contextual help
- Owner: platform
- Branch: `t291-help-surfaces`
- Decision references: `docs/architecture-decisions.md` sections 2.1, 3; `docs/capability-contracts.md` row F073; `docs/engineering-standards.md`

## Objective

Implement the help article read API, the signed content bundle import job, and the contextual help drawer, including locale fallback and the degraded path a stale link takes.

## Specification

- Owned paths: `crates/domain/src/announcements/{help.rs, bundle.rs}`, `crates/persistence/src/announcements/help_article_repository.rs`, `services/api/src/announcements/handlers_help.rs`, `services/worker/src/announcements/{mod.rs, import_help_bundle.rs}`, `apps/web/src/features/announcements/{HelpDrawer.tsx, HelpIndexList.tsx, useHelpContext.ts}`
- Contract and input: index query `{ context?, locale? }`; article path parameter `slug`; conditional request header `If-None-Match`; bundle manifest `{ bundle_id, signature, articles: [{ slug, section, default_locale, version, contexts, translations }] }`.
- Output and behaviour: routes `GET /api/v1/help/articles` returning `{ articles, locale, translation_fallback, matched }` and `GET /api/v1/help/articles/{slug}` returning `{ slug, version, locale, title, body_markdown, updated_at, translation_fallback }` for the highest `help_article_versions.version`. A `context` with no `help_article_contexts` rows returns the full index with `matched: false`; an unknown or withdrawn slug returns `404 not_found` and `HelpDrawer.tsx` renders the contextual index with a one-line note rather than an error page. A locale with no `help_article_translations` row for the resolved version falls back to the article's `default_locale`, sets `translation_fallback: true`, and increments `help_article_fallback_total{locale}`. Responses carry a strong `ETag` over slug, version and locale and answer a matching `If-None-Match` with `304`. `import_help_bundle.rs` verifies the signature before any write, then upserts `help_articles`, `help_article_versions`, `help_article_translations` and `help_article_contexts` in one `UnitOfWork` keyed by `bundle_id`; a repeated bundle is a no-op and an unverified bundle leaves the previous version serving and maps to `503 unavailable`. `useHelpContext.ts` derives the screen key from the TanStack Router match; `F1` opens the drawer and `Escape` closes it returning focus to the trigger, leaving the route's selection and scroll position untouched.
- Data access: these files hold no SQL. Every read and write goes through `HelpArticleRepository` in `crates/persistence/src/announcements/` using the named queries `list_index_for_locale`, `list_contextual_slugs`, `load_article_version` and `upsert_bundle_version`, with no generic query escape hatch (decision section 2.1).
- Authorization: both help routes are readable by any authenticated session and carry no tenant data; the import job runs as a deployment job, not on a request path, and writes an audit row for each applied bundle.
- Dependencies: F049 locale resolution through the harness stub; F062 drawer and list primitives; the `SafeDoc` renderer from T290, which article bodies share so authored help content is subject to the same node union.
- Feature flag: `F073_FEATURE` gates the routes, the drawer mount and the job registration.

## TDD

- Failing test first: `testing/features/F073/api/help_tests.rs::help_index_filters_by_context_key`, `::unknown_context_returns_full_index_unmatched`, `::article_returns_highest_version`, `::article_missing_translation_falls_back_to_default_locale`, `::withdrawn_slug_returns_not_found`, `::etag_matching_request_returns_304`, `::article_body_drops_raw_html_node`; `testing/features/F073/api/bundle_tests.rs::signed_bundle_imports_articles_and_contexts`, `::repeated_bundle_id_is_noop`, `::unsigned_bundle_leaves_previous_version_serving`; `testing/features/F073/frontend/HelpDrawer.test.tsx::not_found_renders_index_with_note`, `::fallback_locale_shows_shown_in_english_note`, `::drawer_restores_focus_to_trigger`
- Targeted command: `cargo xtask test-feature F073`
- Full command: `cargo xtask test-all`
- Fixtures and mocks: `testing/fixtures/announcements.rs` seeding eight `en-US` articles with four `de-DE` translations, six context mappings and a withdrawn slug; signed and unsigned bundle fixtures; F049 locale resolver stub; the harness is described in `testing/features/F073/README.md`

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Routes registered in `services/api/src/router.rs` and the job in `services/worker/src/registry.rs` behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S146
- [ ] `finished_at` recorded
