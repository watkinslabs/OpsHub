---
id: T290
type: task
status: planned
parent_epic: E003
parent_feature: F073
parent_story: S145
depends_on: [S145]
owned_paths: [crates/domain/src/announcements/**, crates/persistence/src/announcements/**, services/api/src/announcements/**, apps/web/src/features/announcements/**, testing/features/F073/api/**, testing/features/F073/frontend/**]
feature_flag: F073_FEATURE
branch: t290-targeting-and-dismissal
started_at: null
finished_at: null
---

# T290 — Targeting and dismissal

## Identity

- Parent story: `S145` Announcements
- Owner: platform
- Branch: `t290-targeting-and-dismissal`
- Decision references: `docs/architecture-decisions.md` sections 2.1, 3; `docs/capability-contracts.md` row F073; `docs/authorization-model.md` sections 2 and 3.1; `docs/packaging.md` sections 1 and 2

## Objective

Implement announcement authoring, audience targeting, permanent dismissal, supersession on material change, the server-side interruption budget, and the what's-new panel that renders them.

## Specification

- Owned paths: `crates/domain/src/announcements/{targeting.rs, budget.rs, hashing.rs, markdown.rs, service.rs}`, `services/api/src/announcements/{mod.rs, routes.rs, handlers_announcement.rs, dto.rs}`, `apps/web/src/features/announcements/{WhatsNewPanel.tsx, AnnouncementItem.tsx, InterruptModal.tsx, SafeMarkdown.tsx, api.ts, hooks.ts}`
- Contract and input: `PublishAnnouncementRequest { scope, slug, severity, translations, targets, learn_more_article_slug?, expires_at?, publish }`; `EditAnnouncementRequest { revision, expires_at?, translations? }`; list query `{ cursor?, limit?, include_dismissed? }`; `Idempotency-Key` on every mutation and `If-Match` on the edit.
- Output and behaviour: routes `GET /api/v1/announcements`, `POST /api/v1/announcements`, `PATCH /api/v1/announcements/{id}`, `POST /api/v1/announcements/{id}/dismiss`. `targeting.rs` evaluates `announcement_targets` rows as OR within a kind and AND across kinds over the caller's plan, F048 entitlement states `active` and `trial`, roles and tenant id, with an empty set matching everyone in scope. `hashing.rs` computes `content_hash` as SHA-256 over severity, sorted target tuples, `learn_more_article_slug` and every translation, and classifies an edit as editorial only when severity, targets and the article slug are unchanged and each body edit is within 5% of its NFC-normalized, whitespace-collapsed token count; anything else maps to `MaterialChange`. Supersession publishes a new announcement with `supersedes_id` and marks the original `superseded` in one `UnitOfWork`, leaving its dismissal rows untouched. `budget.rs` clears `interrupting` when `count_interruptions_since` shows one interruption in the last 24 hours or three in the last 7 days, and `record_interruption` writes the ledger row when a modal is served. Publishing snapshots `audience_size` and emits `announcement.published.v1`; dismissal writes one row and emits `announcement.dismissed.v1` carrying no user identifier. `markdown.rs` returns `SafeDoc`, whose node union cannot represent a raw HTML, image, iframe, style or script node and restricts anchors to `https:` and same-origin paths; `SafeMarkdown.tsx` renders those nodes and accepts no HTML string.
- Data access: none of these files hold SQL. Every read and write goes through `AnnouncementRepository` from `crates/persistence/src/announcements/` using the named queries listed in ticket section 4, and the publish, edit and supersede paths each commit in one `UnitOfWork` (decision section 2.1).
- Authorization: `scope: platform` requires the `platform-operator` principal kind and is refused to every tenant role; `scope: tenant` requires `tenant-admin` and takes the tenant id from the session; dismissal is the `self` principal; a foreign-tenant announcement id is `404 not_found`.
- Dependencies: F002 tenants, users and the `tenants.plan` column; F037 for the bell surface the panel sits beside; F048 entitlement state and F049 locale resolution through the harness stubs; F062 primitives for the panel, chip and modal.
- Feature flag: `F073_FEATURE` gates the routes and the panel mount.

## TDD

- Failing test first: `testing/features/F073/api/targeting_tests.rs::targets_and_across_kinds_or_within_kind`, `::free_tenant_never_sees_enterprise_target`, `::entitlement_target_matches_trial_state`, `::empty_target_set_reaches_everyone`; `testing/features/F073/api/announcement_tests.rs::list_excludes_dismissed_and_expired`, `::tenant_admin_cannot_publish_platform_scope`, `::platform_operator_cannot_publish_tenant_scope`, `::foreign_tenant_target_denied`, `::publish_snapshots_audience_size_and_emits_event`, `::dismiss_is_idempotent_and_permanent`, `::material_edit_rejected_with_conflict`, `::editorial_edit_within_token_threshold_accepted`, `::supersede_keeps_original_dismissed`, `::interruption_budget_degrades_to_passive`, `::member_cannot_publish`; `testing/features/F073/frontend/WhatsNewPanel.test.tsx::dismissed_item_has_no_dismiss_control`, `::raw_html_in_body_is_dropped`
- Targeted command: `cargo xtask test-feature F073`
- Full command: `cargo xtask test-all`
- Fixtures and mocks: `testing/fixtures/announcements.rs` with tenant A on `enterprise` holding `assets` and tenant B on `free`; F048 and F049 stubs; the HTML injection corpus and the editorial token corpus described in `testing/features/F073/README.md`; fixed clock

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Routes registered in `services/api/src/router.rs` behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S145
- [ ] `finished_at` recorded
