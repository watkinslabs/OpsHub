---
id: T289
type: task
status: planned
parent_epic: E003
parent_feature: F073
parent_story: S145
depends_on: [S145]
owned_paths: [services/api/migrations/*_announcements_*.sql, crates/domain/src/announcements/**, crates/persistence/src/announcements/**, testing/features/F073/database/**]
feature_flag: F073_FEATURE
branch: t289-announcement-schema
started_at: null
finished_at: null
---

# T289 — Announcement schema

## Identity

- Parent story: `S145` Announcements
- Owner: platform
- Branch: `t289-announcement-schema`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 2.2; `docs/capability-contracts.md` row F073

## Objective

Create the `announcements` module schema and the two repositories over it, so that every later task reads and writes announcements and help content through named queries and never through SQL of its own.

## Specification

- Owned paths: `services/api/migrations/<ts>_announcements_create_tables.sql` and `.down.sql`, `crates/domain/src/announcements/{mod.rs, announcement.rs, help.rs, errors.rs}`, `crates/persistence/src/announcements/{mod.rs, announcement_repository.rs, help_article_repository.rs}`
- DDL: the nine tables in ticket section 4 — `announcements` with the `scope`/`tenant_id` agreement check, the `severity` check, the `state` check and the constraint that `action_required` carries a `learn_more_article_slug`; `announcement_translations`, `announcement_targets`, `announcement_dismissals` and `announcement_interruptions` as the child tables that replace any array column; `help_articles`, `help_article_versions`, `help_article_translations` and `help_article_contexts`. Partial unique indexes on `(tenant_id, slug)` for tenant scope and `(slug) where tenant_id is null` for platform scope, both filtered on `deleted_at is null` and created `CONCURRENTLY`; the remaining indexes listed in ticket section 4. This migration is the expand phase of a new module: nothing is backfilled and no existing read path changes (decision section 2.2).
- Repositories: `AnnouncementRepository` owns `announcements`, `announcement_translations`, `announcement_targets`, `announcement_dismissals` and `announcement_interruptions`; `HelpArticleRepository` owns the four help tables. Named queries `list_visible_for_actor`, `list_dismissed_for_actor`, `resolve_audience_size`, `insert_with_translations_and_targets`, `replace_translations`, `find_by_slug_and_scope`, `mark_superseded`, `record_dismissal`, `count_dismissals_by_tenant`, `count_interruptions_since`, `record_interruption`, `list_index_for_locale`, `list_contextual_slugs`, `load_article_version`, `upsert_bundle_version`, with no generic query escape hatch.
- Data access: all SQL for the module lives in these two files. `crates/domain/src/announcements` holds the entities and error enum and contains no `sqlx::query*` call or connection. `list_visible_for_actor` is the single read-only named query permitted to widen the base tenant predicate to `tenant_id is null or tenant_id = $tenant`, because a platform-scope announcement is not tenant-owned; every write path keeps the base predicate.
- Domain types: `Announcement`, `Translation`, `Target`, `Dismissal`, `HelpArticle`, `ArticleVersion` as in ticket section 4, plus `AnnouncementError` with the variants mapped in ticket section 4.
- Rollback: `.down.sql` drops the nine tables children before parents and removes both partial unique indexes.
- Feature flag: `F073_FEATURE` gates the routes built on this schema; the migration runs regardless.

## TDD

- Failing test first: `testing/features/F073/database/migration_tests.rs::announcements_tables_exist_with_constraints`, `::platform_row_requires_null_tenant`, `::tenant_row_requires_tenant_id`, `::action_required_requires_article_slug`, `::slug_unique_per_scope_ignoring_deleted`; `testing/features/F073/database/constraint_tests.rs::dismissal_primary_key_blocks_duplicate`, `::interruption_ledger_one_row_per_user_and_announcement`, `::target_kind_check_rejects_unknown_kind`, `::translations_cascade_on_announcement_delete`, `::help_translation_requires_existing_version`, `::rollback_drops_announcements_tables`
- Targeted command: `cargo xtask test-feature F073`
- Full command: `cargo xtask test-all`
- Fixtures and mocks: `testing/fixtures/announcements.rs`; fixed UUIDv7 seeds and fixed clock `2026-09-03T00:00:00Z`; the harness is described in `testing/features/F073/README.md`

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; `cargo xtask check-migrations` and `check-persistence` pass
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S145
- [ ] `finished_at` recorded
