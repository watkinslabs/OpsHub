---
id: S054
type: story
status: planned
parent_epic: E006
parent_feature: F027
depends_on: [S053]
owned_paths: [crates/domain/src/compliance/**, services/api/src/compliance/**, services/worker/src/compliance/**, apps/web/src/features/compliance/**, testing/features/F027/**]
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
- Decision references: `docs/architecture-decisions.md` sections 3, 4, 9; `docs/capability-contracts.md` row F027

## Vertical slice

As a compliance administrator, I want to generate an access-review report for a workspace or the whole tenant, see every principal with their roles, shares, links, tokens, and activity, and record keep or revoke decisions that take effect immediately, so that periodic access certification is a repeatable, audited task.

## Requirements

- **SR-S054-01:** `POST /api/v1/compliance/access-reviews` with `{ scope, as_of? }` generates a report listing users and guests with roles, group memberships, direct shares, share links, and API tokens, stored as JSON and CSV in object storage, and publishes `access-review.generated.v1` (covers FR-F027-11).
- **SR-S054-02:** Each principal row carries `last_login_at` and `last_activity_at`; principals inactive more than 90 days and guests with links older than 30 days are flagged, and `flagged_count` is stored on the report (FR-F027-12).
- **SR-S054-03:** `POST /api/v1/compliance/access-reviews` with `{ report_id, decisions }` records `keep`/`revoke` per principal; `revoke` removes ACL entries and share links through F003 and revokes tokens through F038, each audited as `access-review.decide` (FR-F027-12).
- **SR-S054-04:** `GET /api/v1/compliance/access-reviews` pages by cursor with `scope` filter and returns `principal_count`, `flagged_count`, and decision progress (FR-F027-11).
- **SR-S054-05:** Reports for 5,000 principals generate in under 60 s using one query per principal kind rather than per principal (NFR-F027-01).
- **SR-S054-06:** `AccessReviewList`, `AccessReviewDetail`, and `DecisionTable` render flagged rows, allow bulk `revoke` of flagged guests, and show the audit outcome per decision (FR-F027-14, NFR-F027-03).
- **SR-S054-07:** The full F027 harness covers hold-then-export-then-purge-then-review end to end, permission negatives, accessibility, and the purge and review performance budgets (FR-F027-13, NFR-F027-01, NFR-F027-02).

## Surfaces

- Infrastructure/container: none beyond S053
- Rust service/API: `crates/domain/src/compliance/{review.rs, review_query.rs, decisions.rs}`; `services/api/src/compliance/handlers_review.rs`; `services/worker/src/compliance/access_review.rs`
- Data/migration: none new; uses `access_reviews` from S053
- React/UI: `apps/web/src/features/compliance/{AccessReviewList.tsx, AccessReviewDetail.tsx, DecisionTable.tsx, ReviewScopePicker.tsx}`
- Mocks/fixtures: 40 principals including 3 stale guests and 2 users inactive 120 days; 5,000-principal generator for the performance lane; MSW handlers for component tests

## TDD harness

- Test path: `testing/features/F027/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F027_FEATURE`
- Targeted command: `cargo xtask test-feature F027`
- Full command: `cargo xtask test-all`
- First failing tests: `access_review_lists_roles_shares_links_tokens`, `access_review_flags_inactive_and_stale_guests`, `access_review_revoke_removes_acl_and_tokens`, `access_review_list_filters_by_scope`, `access_review_5000_principals_under_60s`, `decision_table_bulk_revoke_flagged`

## Exit criteria

- [ ] Requirement tests SR-S054-01 through SR-S054-07 written first and failing
- [ ] Tasks T107 and T108 complete; review UI wired to the real API through the generated client
- [ ] Unit, API, React, E2E, permission, accessibility, and performance tests pass
- [ ] Production call path named: `apps/web/src/features/compliance/AccessReviewList.tsx` mounted at `/admin/compliance/access-reviews`; `services/api/src/compliance/handlers_review.rs` via `routes.rs`
- [ ] Handoff evidence recorded in the F027 ticket
