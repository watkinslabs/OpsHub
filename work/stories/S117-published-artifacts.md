---
id: S117
type: story
status: planned
parent_epic: E008
parent_feature: F059
depends_on: [F013, F023, F036]
owned_paths: [crates/domain/src/publishing/**, services/api/src/publishing/**, services/api/migrations/*_publishing_*.sql, services/worker/src/publishing/**, testing/features/F059/**]
feature_flag: F059_FEATURE
branch: s117-published-artifacts
started_at: null
finished_at: null
---

# S117 — Published artifacts

## Identity

- Parent feature: `F059` Publishing/embedding
- Owner: platform
- Branch: `s117-published-artifacts`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 7; `docs/capability-contracts.md` row F059

## Vertical slice

As a publisher, I want to create, list, update, and revoke publications of views, reports, and dashboards with hashed scoped tokens and worker-refreshed snapshots, so that a read-only public rendering exists with correct freshness before embedding and UI are added.

## Requirements

- **SR-S117-01:** `POST /api/v1/publications` validates target kind, `expires_at` ≤ 30 days, origins, and `refresh_interval_s`, inserts `publications` and one `publication_tokens` row (SHA-256 hash, scope), returns the plaintext token once, publishes `publication.created.v1`, and enqueues the first `publishing.refresh` (covers FR-F059-01, FR-F059-02).
- **SR-S117-02:** `POST /api/v1/publications/{id}/rotate-token` issues a new token, sets `superseded_at = now + 10 min` on the old one, and publishes `publication.updated.v1` with `changed_fields: ["token"]` (FR-F059-02).
- **SR-S117-03:** `GET /public/publications/{token}` resolves the hash, rejects expired, revoked, or superseded tokens with `404`, and renders the snapshot with `generated_at`, `source_versions`, `stale`, and the `X-OpsHub-Stale` header; publisher access loss or target deletion renders the `error` state with reason (FR-F059-03, FR-F059-05).
- **SR-S117-04:** `services/worker/src/publishing/refresh_job.rs` regenerates the snapshot as the publisher through F013, F021, or F023 for-actor renderers, strips hidden columns, comments, attachments, and tenant links, stores it in object storage, and records `last_error` on failure; `scheduler.rs` enqueues due refreshes and expiries every minute (FR-F059-04, FR-F059-05, FR-F059-08).
- **SR-S117-05:** `PATCH` and `DELETE /api/v1/publications/{id}` require `If-Match`; revoke marks every token revoked, publishes `publication.revoked.v1`, and public renders return `404` within 5 s (FR-F059-08, FR-F059-09).
- **SR-S117-06:** `GET /api/v1/publications` pages by cursor with `target_kind`, `target_id`, `status` filters and `view_count_7d`, filtered to targets the actor can read; a foreign tenant receives `404` (FR-F059-11).
- **SR-S117-07:** The migration creates the three tables with the hash, active-target, and expiry constraints in ticket section 4 (NFR-F059-02).

## Surfaces

- Infrastructure/container: JetStream stream `publishing` with subject `publishing.refresh` declared in `services/worker/src/publishing/mod.rs`; MinIO prefix `publications/`
- Rust service/API: `crates/domain/src/publishing/{mod.rs, publication.rs, token.rs, snapshot.rs, errors.rs, service.rs, render.rs}`; `services/api/src/publishing/{mod.rs, routes.rs, handlers_publication.rs, handlers_public.rs, dto.rs}`; `services/worker/src/publishing/{mod.rs, refresh_job.rs, scheduler.rs}`
- Data/migration: `services/api/migrations/<ts>_publishing_create_tables.sql` and `.down.sql`
- React/UI: none in this story (S118 and T235 cover UI)
- Mocks/fixtures: `testing/fixtures/publishing.rs` publisher, non-publisher, foreign tenant, view with hidden columns, report, 12-widget dashboard; fixed token RNG seed

## TDD harness

- Test path: `testing/features/F059/api/`, `testing/features/F059/database/`
- Feature flag: `F059_FEATURE`
- Targeted command: `cargo xtask test-feature F059`
- Full command: `cargo xtask test-all`
- First failing tests: `publication_create_returns_token_once`, `publication_expiry_over_30_days_invalid`, `public_render_hides_hidden_columns`, `public_render_stale_after_refresh_failure`, `rotate_token_grace_then_404`, `revoke_returns_404_within_5s`, `non_publisher_create_denied`

## Exit criteria

- [ ] Requirement tests SR-S117-01 through SR-S117-07 written first and failing
- [ ] Tasks T233 and T234 complete and wired through `services/api` router and the worker
- [ ] Unit, API, worker, database, permission tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/publishing/routes.rs` mounted in `services/api/src/router.rs` (public routes outside the session middleware); `services/worker/src/publishing/refresh_job.rs` registered in `services/worker/src/main.rs`
- [ ] Handoff evidence recorded in the F059 ticket
