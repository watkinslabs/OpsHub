---
id: T274
type: task
status: planned
parent_epic: E003
parent_feature: F069
parent_story: S137
depends_on: [S137]
owned_paths: [services/api/migrations/*_home_*.sql, crates/persistence/src/home/**, crates/domain/src/home/**, services/api/src/home/**, services/worker/src/home/**, testing/features/F069/api/**, testing/features/F069/database/**]
feature_flag: F069_FEATURE
branch: t274-favourites-and-recents
started_at: null
finished_at: null
---

# T274 — Favourites and recents

## Identity

- Parent story: `S137` Home surfaces
- Owner: platform
- Branch: `t274-favourites-and-recents`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3; `docs/capability-contracts.md` row F069

## Objective

Create the `home` schema and implement explicit per-user favourites, implicit per-user recents with their recording layer and flusher, and the prune job that keeps both honest.

## Specification

- Owned paths: `services/api/migrations/<ts>_home_create_tables.sql` and `.down.sql`, `crates/persistence/src/home/{mod.rs, favorite_repository.rs, recent_item_repository.rs}`, `crates/domain/src/home/{favorite.rs, recent.rs}`, `services/api/src/home/{handlers_favorites.rs, handlers_recents.rs, visit_layer.rs}`, `services/worker/src/home/{mod.rs, flusher.rs, prune.rs}`
- Contract/input: `CreateFavoriteRequest { target_kind, target_id }` with `target_kind` in `workspace`, `folder`, `sheet`, `row`, `view`, `dashboard`, `report`, `document`; list queries `{ cursor?, limit?, filter?, fields? }`; `Idempotency-Key` on `POST` and `If-Match: <version>` on `DELETE`.
- Output/behavior: routes `GET /api/v1/favorites`, `POST /api/v1/favorites`, `DELETE /api/v1/favorites/{id}`, `GET /api/v1/recents`. A pin requires read on the target and returns `not_found` otherwise, `conflict` with the existing id on a duplicate, `conflict` with `field_errors.limit` on the 201st, and publishes `favorite.added.v1`; unpin touches only the caller's own row, succeeds for an unavailable target, and publishes `favorite.removed.v1`. `filter=unavailable` returns pins whose target no longer resolves, carrying `label_cache` and no `path`. `visit_layer.rs` defines `RecentVisitLayer`, which on a `2xx` from `GET /api/v1/sheets/{id}`, `GET /api/v1/rows/{id}`, `GET /api/v1/views/{id}`, or `GET /api/v1/workspaces/{id}/tree` pushes onto a bounded 4,096-entry channel without blocking, dropping and counting when full; `flusher.rs` drains every 5 s, coalesces repeats inside 60 s, upserts through `record_visits`, and calls `trim_to_newest(user_id, 100)` in the same transaction; `prune.rs` runs hourly, deletes recents past 90 days, deletes rows for purged targets in batches of 500 ids per kind, refreshes changed labels, and stops at 10,000 rows per run. DDL for `favorites` and `recent_items` with their check constraints, the partial unique index, the recents primary key, and the five read indexes from ticket section 4.
- Data access: the handlers, the layer, the flusher, and the prune job hold no SQL; every read and write goes through `FavoriteRepository` and `RecentItemRepository` in `crates/persistence/src/home/` using the named queries listed in ticket section 4, with no generic query escape hatch, and the pin, unpin, and flush paths each commit their rows, audit row, and outbox event in one `UnitOfWork` (decision 2.1). Every named query takes `user_id` from the request or job context; none omits it.
- Dependencies: F003 `authz::require` for the read check on a pin target and for the audit row; F002 `users` for the cascade; F004 worker transport for the two jobs; the base `Repository` and `UnitOfWork` contracts of F068.
- Feature flag: `F069_FEATURE` gates the routes, the layer, and both jobs; the migration runs regardless.

## TDD

- Failing test first: `testing/features/F069/api/favorites_tests.rs::pin_requires_read_on_target`, `::duplicate_pin_returns_conflict_with_existing_id`, `::two_hundred_first_pin_rejected`, `::unpin_of_other_users_favorite_is_not_found`, `::unpin_of_unavailable_target_succeeds`, `::filter_unavailable_returns_cached_label_without_path`, `::pin_replay_is_idempotent`; `testing/features/F069/api/recents_tests.rs::visit_recorded_after_successful_read`, `::visit_not_recorded_for_non_2xx`, `::repeat_visit_within_sixty_seconds_coalesces`, `::recents_trimmed_to_one_hundred`, `::full_channel_drops_and_counts`; `testing/features/F069/api/prune_tests.rs::prune_deletes_recents_past_ninety_days`, `::prune_removes_rows_for_purged_targets`, `::prune_is_idempotent_and_bounded`; `testing/features/F069/database/migration_tests.rs::home_tables_exist_with_constraints`, `::favorite_unique_per_user_and_target`, `::recent_upsert_is_single_statement`, `::visit_count_must_be_positive`, `::rows_cascade_on_user_delete`, `::rollback_drops_home_tables`
- Targeted command: `cargo xtask test-feature F069`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/home.rs` seeding 200 favourites and 100 recents for one member and none for another; fixed clock for coalescing and retention; in-process visit channel per test worker

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; routes, layer, and jobs registered behind the flag; OpenAPI regenerated without drift
- [ ] Outbox and audit rows verified for pin and unpin
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S137
- [ ] `finished_at` recorded
