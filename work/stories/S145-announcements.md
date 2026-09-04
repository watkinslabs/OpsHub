---
id: S145
type: story
status: planned
parent_epic: E003
parent_feature: F073
depends_on: [F002, F037]
owned_paths: [crates/domain/src/announcements/**, crates/persistence/src/announcements/**, services/api/src/announcements/**, apps/web/src/features/announcements/**, services/api/migrations/*_announcements_*.sql, testing/features/F073/**]
feature_flag: F073_FEATURE
branch: s145-announcements
started_at: null
finished_at: null
---

# S145 — Announcements

## Identity

- Parent feature: `F073` Announcements and in-app help
- Owner: platform
- Branch: `s145-announcements`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 2.2, 3; `docs/capability-contracts.md` row F073; `docs/authorization-model.md` sections 2 and 3.1; `docs/packaging.md` sections 1 and 2

## Vertical slice

As a person using OpsHub, I want a what's-new panel that lists only the changes that apply to my tenant, my plan and my role, that I can dismiss once and never see again, and that interrupts me only when something genuinely needs doing, so that the product tells me what changed without turning into an advert or a blocker.

## Requirements

- **SR-S145-01:** `GET /api/v1/announcements` returns published, unexpired, undismissed announcements visible to the caller, newest first, with cursor paging and `include_dismissed=true` for history; `list_visible_for_actor` on `AnnouncementRepository` resolves platform and tenant scope in one query, and it is the only query in the module that widens the base tenant predicate (covers FR-F073-01, NFR-F073-01).
- **SR-S145-02:** `POST /api/v1/announcements` accepts `scope: "platform"` only from a `platform-operator` principal and `scope: "tenant"` only from a `tenant-admin` whose tenant id is taken from the session; a tenant role attempting platform scope and a `tenant` target naming another tenant are both `403 denied`, and both paths write an audit row carrying the target tuples and `content_hash` (FR-F073-02, FR-F073-03, FR-F073-15).
- **SR-S145-03:** Targeting evaluates `announcement_targets` rows of kind `plan`, `entitlement`, `role` and `tenant` as OR within a kind and AND across kinds, with an empty set reaching everyone in scope; a `plan` value comes from `docs/packaging.md` section 1 and an `entitlement` matches only in state `active` or `trial`, so an Enterprise-only module is never announced to a Free tenant (FR-F073-04).
- **SR-S145-04:** Publishing sets `published_at`, snapshots `audience_size` at that instant, emits `announcement.published.v1` through the outbox, and never recomputes the audience afterwards (FR-F073-05, NFR-F073-04).
- **SR-S145-05:** `POST /api/v1/announcements/{id}/dismiss` writes one `announcement_dismissals` row for the calling `self` principal, is idempotent, emits `announcement.dismissed.v1` carrying no user identifier, and has no inverse — no route, sweep or retention job removes a dismissal row (FR-F073-06, FR-F073-14).
- **SR-S145-06:** `PATCH /api/v1/announcements/{id}` accepts only editorial revisions — unchanged severity, target set and `learn_more_article_slug`, with each body edit within 5% of its normalized token count — and returns `409 conflict` otherwise; a material change is published as a new announcement with `supersedes_id`, the original moves to `superseded`, and the superseded row keeps its dismissals so nothing is resurrected (FR-F073-07, NFR-F073-05).
- **SR-S145-07:** `info` and `change` are always passive; only `action_required` carrying a `learn_more_article_slug` may set `interrupting`, and the server clears it when `count_interruptions_since` shows one interruption in the last 24 hours or three in the last 7 days, incrementing `announcement_interruptions_suppressed_total` with the reason (FR-F073-08, FR-F073-09).
- **SR-S145-08:** The what's-new panel renders severity as a labelled chip plus text, shows dismissed items only under `Show dismissed` and without a dismiss control, returns focus to the bell on close, and the interrupting modal is escapable, offers `Later` without dismissing, and never mounts over an open sheet, document or form editor (FR-F073-08, FR-F073-09, NFR-F073-03).
- **SR-S145-09:** Announcement bodies render through the `SafeDoc` node union, so no raw HTML, image, iframe, style or script node is representable, anchors are limited to `https:` and same-origin paths, and neither the panel nor the modal issues a request to any origin other than the API (FR-F073-13, FR-F073-14, NFR-F073-02).

## Surfaces

- Data access: `crates/persistence/src/announcements/{mod.rs, announcement_repository.rs}` holds every SQL statement for this slice; `crates/domain/src/announcements`, the `services/api/src/announcements` handlers and the publish path depend on the repository traits and contain no `sqlx::query*` call or connection, and publishing writes the announcement row, its translation rows, its target rows, the audit row and the outbox row in one `UnitOfWork` (decision section 2.1)
- Rust service and API: `crates/domain/src/announcements/{mod.rs, announcement.rs, targeting.rs, budget.rs, hashing.rs, markdown.rs, errors.rs, service.rs}`; `services/api/src/announcements/{routes.rs, handlers_announcement.rs, dto.rs}`
- Data and migration: `services/api/migrations/<ts>_announcements_create_tables.sql` creating `announcements`, `announcement_translations`, `announcement_targets`, `announcement_dismissals` and `announcement_interruptions` with the checks, partial unique indexes and indexes in ticket section 4
- React and UI: `apps/web/src/features/announcements/{WhatsNewPanel.tsx, AnnouncementItem.tsx, InterruptModal.tsx, SafeMarkdown.tsx, api.ts, hooks.ts}`
- Mocks and fixtures: `testing/fixtures/announcements.rs` with tenant A on `enterprise` holding `assets` and tenant B on `free`, a `platform-operator`, a `tenant-admin` and a member per tenant, six announcements across three severities and four target kinds, one superseded pair and one pre-dismissed announcement; F048 entitlement and F049 locale stubs; fixed clock

## TDD harness

- Test path: `testing/features/F073/{api,database,frontend}/`
- Feature flag: `F073_FEATURE`
- Targeted command: `cargo xtask test-feature F073`
- Full command: `cargo xtask test-all`
- First failing tests: `list_excludes_dismissed_and_expired`, `targets_and_across_kinds_or_within_kind`, `free_tenant_never_sees_enterprise_target`, `tenant_admin_cannot_publish_platform_scope`, `dismiss_is_idempotent_and_permanent`, `material_edit_rejected_with_conflict`, `supersede_keeps_original_dismissed`, `interruption_budget_degrades_to_passive`

## Exit criteria

- [ ] Requirement tests SR-S145-01 through SR-S145-09 written first and failing
- [ ] Tasks T289 and T290 complete and wired through the `services/api` router
- [ ] Unit, API, database, React and permission tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/announcements/routes.rs` mounted in `services/api/src/router.rs` under `/api/v1/announcements`; the what's-new panel mounted in the F062 app shell top bar
- [ ] Handoff evidence recorded in the F073 ticket
