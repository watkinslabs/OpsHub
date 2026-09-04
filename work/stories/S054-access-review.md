---
id: S054
type: story
status: planned
parent_epic: E006
parent_feature: F027
depends_on: [S053]
owned_paths: [crates/domain/src/compliance/**, crates/persistence/src/compliance/**, services/api/src/compliance/**, services/worker/src/compliance/**, apps/web/src/features/compliance/**, testing/features/F027/**]
feature_flag: F027_FEATURE
branch: s054-access-review
started_at: null
finished_at: null
---

# S054 — Access review

## Identity

- Parent feature: `F027` Governance/compliance
- Owner: platform
- Branch: `s054-access-review`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 9; `docs/capability-contracts.md` row F027

## Vertical slice

As a compliance administrator, I want to generate an access-review report for a workspace or the whole tenant, see every principal with their roles, shares, links, tokens, and activity, and record keep or revoke decisions that take effect immediately, so that periodic access certification is a repeatable, audited task.

## Requirements

- **SR-S054-01:** `POST /api/v1/compliance/access-reviews` with `{ scope, as_of? }` generates a report writing one `access_review_principals` row per user and guest with `role_count`, `group_count`, `share_count`, `link_count`, and `token_count`, inserted with the parent row in one `UnitOfWork` by `AccessReviewRepository::insert_review_with_principals`; the JSON and CSV renderings are written to object storage for download and `access-review.generated.v1` is published (covers FR-F027-11).
- **SR-S054-02:** Each `access_review_principals` row carries `last_login_at`, `last_activity_at`, and `flag_reason` (`none`, `inactive_90d`, `stale_guest_link`); principals inactive more than 90 days and guests with links older than 30 days are flagged, and `access_reviews.flagged_count` is the count of rows with `flag_reason <> 'none'` (FR-F027-12).
- **SR-S054-03:** `POST /api/v1/compliance/access-reviews` with `{ report_id, decisions }` upserts one `access_review_decisions` row per principal through `AccessReviewRepository::upsert_decisions`, so re-deciding a principal updates the row instead of appending; `revoke` removes ACL entries and share links through the F003 and F036 repositories and revokes tokens through F038, writes the result to the row's `outcome`, and each decision is audited as `access-review.decide` (FR-F027-12).
- **SR-S054-04:** `GET /api/v1/compliance/access-reviews` pages by cursor with `scope` filter through `AccessReviewRepository::list_reviews_by_scope` and returns `principal_count`, `flagged_count`, and `decided_count` counted from `access_review_decisions` (FR-F027-11).
- **SR-S054-05:** Reports for 5,000 principals generate in under 60 s: `AccessReviewRepository` runs one set-based named query per principal kind rather than one per principal, and inserts the principal rows in batches inside a single `UnitOfWork` (NFR-F027-01).
- **SR-S054-06:** `AccessReviewList`, `AccessReviewDetail`, and `DecisionTable` render flagged rows first from `AccessReviewRepository::list_principals_flagged_first`, allow bulk `revoke` of flagged guests, and show each decision's `outcome` (FR-F027-14, NFR-F027-03).
- **SR-S054-07:** The full F027 harness covers hold-then-export-then-purge-then-review end to end, permission negatives, accessibility, and the purge and review performance budgets (FR-F027-13, NFR-F027-01, NFR-F027-02).

## Surfaces

- Infrastructure/container: none beyond S053
- Data access: `crates/persistence/src/compliance/review_repository.rs` holds every SQL statement for this slice; `AccessReviewRepository` owns `access_reviews`, `access_review_principals`, and `access_review_decisions`, and `review.rs`, `review_query.rs`, `decisions.rs`, `handlers_review.rs`, and the `access_review` worker depend on its trait and contain no `sqlx::query*` call; revocation reaches F003, F036, and F038 tables only through those features' repositories in the same `UnitOfWork` (decision section 2.1)
- Rust service/API: `crates/domain/src/compliance/{review.rs, review_query.rs, decisions.rs}`; `services/api/src/compliance/handlers_review.rs`; `services/worker/src/compliance/access_review.rs`
- Data/migration: none new; uses `access_reviews`, `access_review_principals`, and `access_review_decisions` created by the S053 migration
- React/UI: `apps/web/src/features/compliance/{AccessReviewList.tsx, AccessReviewDetail.tsx, DecisionTable.tsx, ReviewScopePicker.tsx}`
- Mocks/fixtures: 40 principals including 3 stale guests and 2 users inactive 120 days; 5,000-principal generator for the performance lane; MSW handlers for component tests

## TDD harness

- Test path: `testing/features/F027/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F027_FEATURE`
- Targeted command: `cargo xtask test-feature F027`
- Full command: `cargo xtask test-all`
- First failing tests: `access_review_lists_roles_shares_links_tokens`, `access_review_flags_inactive_and_stale_guests`, `access_review_revoke_removes_acl_and_tokens`, `access_review_list_filters_by_scope`, `access_review_5000_principals_under_60s`, `decision_table_bulk_revoke_flagged`, `decision_row_unique_per_principal`

## Exit criteria

- [ ] Requirement tests SR-S054-01 through SR-S054-07 written first and failing
- [ ] Tasks T107 and T108 complete; review UI wired to the real API through the generated client
- [ ] Unit, API, React, E2E, permission, accessibility, and performance tests pass
- [ ] Production call path named: `apps/web/src/features/compliance/AccessReviewList.tsx` mounted at `/admin/compliance/access-reviews`; `services/api/src/compliance/handlers_review.rs` via `routes.rs`
- [ ] Handoff evidence recorded in the F027 ticket
