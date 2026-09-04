---
id: S138
type: story
status: planned
parent_epic: E003
parent_feature: F069
depends_on: [F005, F006, F013]
owned_paths: [crates/domain/src/home/**, crates/persistence/src/home/**, services/api/src/home/**, services/worker/src/home/**, apps/web/src/features/home/**, services/api/migrations/*_home_*.sql, testing/features/F069/**]
feature_flag: F069_FEATURE
branch: s138-favourites-and-recents
started_at: null
finished_at: null
---

# S138 — Favourites and recents

## Identity

- Parent feature: `F069` Home and my work
- Owner: platform
- Branch: `s138-favourites-and-recents`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4; `docs/capability-contracts.md` row F069; `docs/authorization-model.md` section 2 (`self`)

## Vertical slice

As a member, I want the four records I live in pinned where I can reach them and the records I visited remembered without asking, both private to me and both quietly dropping anything I can no longer see, so that my landing screen stays mine and stays honest.

## Requirements

- **SR-S138-01:** `GET /api/v1/favorites` returns the caller's own pins newest first with cursor paging, `limit` 1–100 default 20, and `filter` of `available` or `unavailable`; unavailable entries carry `state: "unavailable"`, the stored `label_cache`, and no `path` (covers FR-F069-04).
- **SR-S138-02:** `POST /api/v1/favorites` pins one of the eight target kinds for a caller who can read it now, returning `not_found` when they cannot, `conflict` with the existing id on a duplicate, and `conflict` with `field_errors.limit` on the 201st; `DELETE /api/v1/favorites/{id}` removes only the caller's own pin under `If-Match`, succeeds for an unavailable target, and returns `not_found` for another user's id. Both carry `Idempotency-Key` and publish `favorite.added.v1` or `favorite.removed.v1` (FR-F069-05, FR-F069-06, FR-F069-14).
- **SR-S138-03:** `RecentVisitLayer` records a visit when `GET /api/v1/sheets/{id}`, `GET /api/v1/rows/{id}`, `GET /api/v1/views/{id}`, or `GET /api/v1/workspaces/{id}/tree` returns `2xx`, pushing onto a bounded 4,096-entry channel without blocking or changing the observed response; a repeat within 60 s is coalesced and a full channel drops the visit and counts it (FR-F069-07, NFR-F069-01).
- **SR-S138-04:** `GET /api/v1/recents` returns the caller's own targets most recently visited first with `last_visited_at` and `visit_count`, permission-filtered per request, `limit` 1–100 default 12, and each user capped at 100 rows trimmed inside the flush transaction (FR-F069-08).
- **SR-S138-05:** Losing access to a target hides it from both surfaces on the next read; a recent row is deleted by `home.prune` once its target is purged, while a favourite row is kept and hidden so restoring access restores the pin unchanged (FR-F069-09).
- **SR-S138-06:** The hourly `home.prune` job deletes recents older than 90 days, deletes rows for purged targets in batches of 500 ids per kind, refreshes changed `label_cache` values, and is idempotent, resumable, and bounded to 10,000 rows per run (FR-F069-10, NFR-F069-04).
- **SR-S138-07:** Both tables are private to one person: every named query takes `user_id` from the request context and none omits it, so a `tenant-admin` reading these routes sees only their own rows, and a cross-tenant id returns `not_found` (FR-F069-11, NFR-F069-02).
- **SR-S138-08:** The migration creates `favorites` and `recent_items` with their check constraints, the partial unique index on `(tenant_id, user_id, target_kind, target_id)`, the recents primary key that makes the upsert a single statement, and the five read indexes; `FavoriteStar` is exported from the feature so every other surface toggles a pin through one component (FR-F069-05, NFR-F069-03).

## Surfaces

- Data access: `crates/persistence/src/home/{favorite_repository.rs, recent_item_repository.rs}` own `favorites` and `recent_items` respectively and hold every statement for this slice; the pin path and the flusher each commit their audit, outbox, and trim work in one `UnitOfWork`; `crates/domain/src/home`, `services/api/src/home`, and `services/worker/src/home` contain no SQL (decision 2.1)
- Rust service/API: `crates/domain/src/home/{favorite.rs, recent.rs, service.rs}`; `services/api/src/home/{handlers_favorites.rs, handlers_recents.rs, visit_layer.rs, dto.rs}`; `services/worker/src/home/{mod.rs, flusher.rs, prune.rs}`
- Data/migration: `services/api/migrations/<ts>_home_create_tables.sql` and `.down.sql` creating the two tables, three check constraints, and five indexes from ticket section 4
- React/UI: `apps/web/src/features/home/{FavoriteStar.tsx, FavoritesList.tsx, RecentsList.tsx, api.ts, hooks.ts}`
- Mocks/fixtures: `testing/fixtures/home.rs` seeding 200 favourites and 100 recents for one member, none for another, and a viewer with no workspace access; fixed clock for the 60 s coalescing and 90-day retention cases

## TDD harness

- Test path: `testing/features/F069/{api,database,frontend,e2e}/`
- Feature flag: `F069_FEATURE`
- Targeted command: `cargo xtask test-feature F069`
- Full command: `cargo xtask test-all`
- First failing tests: `pin_requires_read_on_target`, `duplicate_pin_returns_conflict_with_existing_id`, `two_hundred_first_pin_rejected`, `unpin_of_other_users_favorite_is_not_found`, `visit_recorded_after_successful_read`, `repeat_visit_within_sixty_seconds_coalesces`, `recents_trimmed_to_one_hundred`, `tenant_admin_sees_only_own_favorites`

## Exit criteria

- [ ] Requirement tests SR-S138-01 through SR-S138-08 written first and observed failing
- [ ] Tasks T275 and T276 complete and wired through the API router and the worker registry
- [ ] API, database, React, E2E, and permission-negative tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/home/routes.rs` mounted in `services/api/src/router.rs` at `/api/v1/favorites` and `/api/v1/recents`; `RecentVisitLayer` mounted on the versioned router; `services/worker/src/home/{flusher.rs, prune.rs}` registered in `services/worker/src/registry.rs`
- [ ] Handoff evidence recorded in the F069 ticket
